use std::fs::{self, File};
use std::io;
use std::path::Path;
use std::sync::Arc;
use std::thread;

use anyhow::Result;
use crossbeam_channel::bounded;
use indicatif::{MultiProgress, ParallelProgressIterator, ProgressBar, ProgressStyle};
use log::{error, info, warn};
use polars::prelude::*;
use rayon::prelude::*;
use uuid::Uuid;

use crate::checkpoint::{find_resume_point, generate_checkpoints, load_checkpoint_data};
use crate::constants::{INTERMEDIATE_DATA_DIR, NUM_PHASE1_WORKERS, RAW_CHUNK_SIZE};
use crate::state::{load_restore_state, load_state, save_restore_state, save_state};
use crate::types::{FileInfo, FileProcessState, FileStatus, ProcessingState};
use crate::utils::{discover_files, sanitize_prefix, stream_lines};

pub fn run_phase_1(
    restore: bool,
    only_check_files: Option<Vec<String>>,
    exclude_check_files: Option<Vec<String>>,
) -> Result<()> {
    let state: Arc<ProcessingState> = Arc::new(load_state().unwrap_or_else(|_| {
        warn!("Could not load state file, starting from scratch.");
        dashmap::DashMap::new()
    }));

    let mut files_to_process = discover_files(crate::constants::RAW_DATA_DIRS, &state)?;
    if files_to_process.is_empty() {
        warn!("No new raw files to process for Phase 1.");
        return Ok(());
    }

    // Apply filters if provided
    if let Some(only_list) = only_check_files {
        files_to_process.retain(|file_info| {
            file_info
                .path
                .file_name()
                .and_then(|s| s.to_str())
                .map_or(false, |name| only_list.contains(&name.to_string()))
        });
        info!(
            "Filtered to {} files based on --only-check-files.",
            files_to_process.len()
        );
    }

    if let Some(exclude_list) = exclude_check_files {
        files_to_process.retain(|file_info| {
            file_info
                .path
                .file_name()
                .and_then(|s| s.to_str())
                .map_or(true, |name| !exclude_list.contains(&name.to_string()))
        });
        info!(
            "Filtered to {} files based on --exclude-check-files.",
            files_to_process.len()
        );
    }

    if files_to_process.is_empty() {
        warn!("No files remaining after applying filters.");
        return Ok(());
    }

    if restore {
        info!("--restore flag is set. Verifying all non-completed files.");
        let restore_state = Arc::new(load_restore_state().unwrap_or_default());

        // Step 1: Generate checkpoints in parallel for files that don't have them
        info!("Restore Step 1: Generating checkpoints...");
        let checkpoint_pb = ProgressBar::new(files_to_process.len() as u64);
        checkpoint_pb.set_style(
            ProgressStyle::default_bar()
                .template(
                    "{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} ({eta})",
                )
                .unwrap(),
        );

        files_to_process
            .par_iter()
            .progress_with(checkpoint_pb)
            .for_each(|file_info| {
                if restore_state
                    .checkpoints_generated
                    .contains_key(&file_info.path)
                {
                    return;
                }
                if let Ok(Some(_)) = load_checkpoint_data(file_info) {
                    restore_state
                        .checkpoints_generated
                        .insert(file_info.path.clone(), true);
                    return;
                }

                match generate_checkpoints(file_info) {
                    Ok(_) => {
                        restore_state
                            .checkpoints_generated
                            .insert(file_info.path.clone(), true);
                    }
                    Err(e) => {
                        error!(
                            "Failed to generate checkpoints for {:?}: {}",
                            file_info.path, e
                        );
                    }
                }
            });
        save_restore_state(&restore_state)?;
        info!("Restore Step 1 Complete.");

        // Step 2: Verify each file sequentially to conserve memory, as requested.
        info!("Restore Step 2: Verifying file progress one-by-one...");
        for (i, file_info) in files_to_process.iter().enumerate() {
            info!(
                "Verifying file {} of {}: {:?}",
                i + 1,
                files_to_process.len(),
                file_info.path.file_name().unwrap()
            );

            let mut file_state_entry = state.entry(file_info.path.clone()).or_insert_with(|| {
                FileProcessState {
                    status: FileStatus::InProgress,
                    lines_processed: 0,
                }
            });

            if file_state_entry.status == FileStatus::Completed {
                info!("File already marked as completed. Skipping verification.");
                continue;
            }

            match load_checkpoint_data(file_info) {
                Ok(Some(checkpoint_data)) => {
                    info!("Loaded checkpoint data. Finding resume point...");
                    match find_resume_point(file_info, &checkpoint_data) {
                        Ok(new_lines_processed) => {
                            if new_lines_processed != file_state_entry.lines_processed {
                                info!(
                                    "Updating progress for {:?}: from {} to {}",
                                    file_info.path.file_name().unwrap(),
                                    file_state_entry.lines_processed,
                                    new_lines_processed
                                );
                                file_state_entry.lines_processed = new_lines_processed;
                            } else {
                                info!(
                                    "Progress for {:?} is already up to date.",
                                    file_info.path.file_name().unwrap()
                                );
                            }
                        }
                        Err(e) => {
                            error!(
                                "Could not verify resume point for {:?}: {}. Resetting to 0.",
                                file_info.path, e
                            );
                            file_state_entry.lines_processed = 0;
                        }
                    }
                }
                _ => {
                    warn!(
                        "Could not load checkpoint data for {:?}. Skipping verification for this file.",
                        file_info.path
                    );
                }
            }
        }
        info!("Restore Step 2 Complete.");
    }

    info!(
        "Phase 1: Found {} raw files. Spawning {} workers.",
        files_to_process.len(),
        NUM_PHASE1_WORKERS
    );
    let multi_progress = Arc::new(MultiProgress::new());
    let (file_tx, file_rx) = bounded(files_to_process.len());

    for file in files_to_process {
        file_tx.send(file).unwrap();
    }
    drop(file_tx);

    let mut handles = vec![];

    for i in 0..NUM_PHASE1_WORKERS {
        let rx = file_rx.clone();
        let state_clone = Arc::clone(&state);
        let mp_clone = Arc::clone(&multi_progress);

        let handle = thread::Builder::new()
            .name(format!("p1-worker-{}", i))
            .spawn(move || {
                while let Ok(file_info) = rx.recv() {
                    let pb = mp_clone.add(ProgressBar::new_spinner());
                    pb.set_style(
                        ProgressStyle::default_spinner()
                            .template("{spinner:.blue} {msg}")
                            .unwrap(),
                    );

                    let initial_state = state_clone.get(&file_info.path).map(|s| s.clone());
                    let lines_processed = initial_state.map_or(0, |s| s.lines_processed);

                    if let Err(e) =
                        process_raw_file(&file_info, Arc::clone(&state_clone), &pb, lines_processed)
                    {
                        error!("Phase 1 Error {:?}: {}", file_info.path, e);
                        pb.finish_with_message(format!(
                            "Error: {:?}",
                            file_info.path.file_name()
                        ));
                    }
                }
            })
            .unwrap();
        handles.push(handle);
    }

    for h in handles {
        h.join().unwrap();
    }
    save_state(&state)?;
    Ok(())
}

fn process_raw_file(
    file_info: &FileInfo,
    state: Arc<ProcessingState>,
    pb: &ProgressBar,
    mut lines_processed: u64,
) -> Result<()> {
    let fname = file_info.path.file_name().unwrap().to_string_lossy();
    let initial_state = state.get(&file_info.path).map(|s| s.clone());

    if let Some(s) = &initial_state {
        if s.status == FileStatus::Completed {
            pb.finish_with_message(format!("Skipped (completed): {}", fname));
            return Ok(());
        }
        pb.set_message(format!("Resuming {} from {}", fname, lines_processed));
    } else {
        pb.set_message(format!("Starting {}", fname));
    }

    let mut line_iterator = stream_lines(file_info)?.skip(lines_processed as usize);

    loop {
        let mut chunk_lines = Vec::with_capacity(RAW_CHUNK_SIZE);
        let mut lines_in_chunk = 0;

        pb.set_message(format!("Reading chunk from line {}...", lines_processed));

        for _ in 0..RAW_CHUNK_SIZE {
            match line_iterator.next() {
                Some(Ok(line)) => {
                    chunk_lines.push(line);
                    lines_in_chunk += 1;
                }
                Some(Err(e)) => {
                    warn!("I/O error: {}", e);
                    break;
                }
                None => break,
            }
        }

        if chunk_lines.is_empty() {
            break;
        }

        pb.set_message(format!("Processing {} lines...", chunk_lines.len()));

        match process_chunk_logic(chunk_lines, &file_info.file_type) {
            Ok(df_chunk) => {
                if df_chunk.height() > 0 {
                    let groups = df_chunk.group_by(["sanitized_prefix"]).unwrap();

                    let _ = groups.apply(|mut group_df| {
                        let prefix = group_df
                            .column("sanitized_prefix")
                            .and_then(|c| c.str())
                            .ok()
                            .and_then(|s| s.get(0))
                            .unwrap_or("misc")
                            .to_string();

                        let output_dir = Path::new(INTERMEDIATE_DATA_DIR).join(&prefix);
                        fs::create_dir_all(&output_dir).unwrap();

                        let output_file =
                            output_dir.join(format!("inter-{}.parquet", Uuid::new_v4()));
                        let mut file =
                            File::create(&output_file).expect("Failed to create intermediate file");

                        ParquetWriter::new(&mut file)
                            .with_compression(ParquetCompression::Zstd(None))
                            .finish(&mut group_df)
                            .unwrap();

                        Ok(DataFrame::empty())
                    });
                }
            }
            Err(e) => error!("Processing Logic Error: {}", e),
        }

        lines_processed += lines_in_chunk as u64;
        state.insert(
            file_info.path.clone(),
            FileProcessState {
                status: FileStatus::InProgress,
                lines_processed,
            },
        );

        if lines_processed % (RAW_CHUNK_SIZE as u64 * 5) == 0 {
            let _ = save_state(&state);
        }

        if lines_in_chunk < RAW_CHUNK_SIZE {
            break;
        }
    }

    pb.finish_with_message(format!("Finished: {}", fname));
    state.insert(
        file_info.path.clone(),
        FileProcessState {
            status: FileStatus::Completed,
            lines_processed,
        },
    );
    save_state(&state)?;
    Ok(())
}

fn process_chunk_logic(lines: Vec<String>, item_type: &str) -> Result<DataFrame> {
    let text = lines.join("\n");
    let cursor = io::Cursor::new(text.as_bytes());

    let schema = Schema::from_iter(vec![
        Field::new("id", DataType::String),
        Field::new("name", DataType::String),
        Field::new("link_id", DataType::String),
        Field::new("parent_id", DataType::String),
        Field::new("subreddit", DataType::String),
        Field::new("author", DataType::String),
        Field::new("title", DataType::String),
        Field::new("selftext", DataType::String),
        Field::new("body", DataType::String),
        Field::new("permalink", DataType::String),
        Field::new("created_utc", DataType::Float64),
        Field::new("ups", DataType::Float64),
        Field::new("downs", DataType::Float64),
        Field::new("distinguished", DataType::String),
    ]);

    let df_chunk = JsonReader::new(cursor)
        .with_schema(Arc::new(schema))
        .with_json_format(JsonFormat::JsonLines)
        .with_ignore_errors(true) // Robustness
        .finish()?;

    if df_chunk.height() == 0 {
        return Ok(df_chunk);
    }

    // Normalize
    let df_normalized = if item_type == "submission" {
        df_chunk
            .lazy()
            .select([
                col("id").fill_null(lit("")).alias("id"),
                col("name").fill_null(lit("")).alias("link_id"),
                lit(NULL).cast(DataType::String).alias("parent_id"),
                col("subreddit").fill_null(lit("")).alias("subreddit"),
                col("author").fill_null(lit("")).alias("author"),
                (col("title").fill_null(lit("")) + lit("\n") + col("selftext").fill_null(lit("")))
                    .alias("body"),
                col("permalink").fill_null(lit("")).alias("permalink"),
                col("created_utc").fill_null(0.0).alias("created_utc"),
                col("ups").fill_null(0.0).alias("ups"),
                col("downs").fill_null(0.0).alias("downs"),
                col("distinguished")
                    .fill_null(lit(""))
                    .alias("distinguished"),
            ])
            .collect()? // Collect into memory to reshape
    } else {
        df_chunk
            .lazy()
            .select([
                col("id").fill_null(lit("")).alias("id"),
                col("link_id").fill_null(lit("")).alias("link_id"),
                col("parent_id").fill_null(lit("")).alias("parent_id"),
                col("subreddit").fill_null(lit("")).alias("subreddit"),
                col("author").fill_null(lit("")).alias("author"),
                col("body").fill_null(lit("")).alias("body"),
                col("permalink").fill_null(lit("")).alias("permalink"),
                col("created_utc").fill_null(0.0).alias("created_utc"),
                col("ups").fill_null(0.0).alias("ups"),
                col("downs").fill_null(0.0).alias("downs"),
                col("distinguished")
                    .fill_null(lit(""))
                    .alias("distinguished"),
            ])
            .collect()? // Collect into memory to reshape
    };

    // Filter Logic
    let engagement_score = (col("ups") * lit(0.8)) + (col("body").str().len_chars() * lit(0.2));

    let is_idea_udf = |s: Series| {
        let ca = s.str().unwrap();
        let pattern = "(?i)idea|solution|concept|opportunity|build|create|develop|imagine|what if|improve|new way|innovate";
        Ok(Some(ca.contains(pattern, true).unwrap().into_series()))
    };
    let exclude_udf = |s: Series| {
        let ca = s.str().unwrap();
        let pattern = r"why doesn't someone|wouldn't it be cool if|in a perfect world|they should just|if I won the lottery|magical solution|cure for cancer|world peace|free .* for everyone";
        Ok(Some(ca.contains(pattern, true).unwrap().into_series()))
    };
    let sanitize_udf = |s: Series| {
        let ca = s.str().unwrap();
        let sanitized: StringChunked = ca.apply_generic(|val| val.map(|s_val| sanitize_prefix(s_val)));
        Ok(Some(sanitized.into_series()))
    };

    let df_filtered = df_normalized
        .lazy()
        .with_column(
            col("subreddit")
                .apply(sanitize_udf, GetOutput::from_type(DataType::String))
                .alias("sanitized_prefix"),
        )
        .filter(col("author").str().contains(lit("bot"), true).not())
        .filter(
            col("distinguished")
                .eq(lit("moderator"))
                .or(col("distinguished").eq(lit("admin")))
                .not(),
        )
        .filter(
            col("body")
                .apply(exclude_udf, GetOutput::from_type(DataType::Boolean))
                .not(),
        )
        .with_column(engagement_score.alias("engagement_quality"))
        .filter(col("engagement_quality").gt(lit(5.0)))
        .with_column(
            col("body")
                .apply(is_idea_udf, GetOutput::from_type(DataType::Boolean))
                .alias("cpu_filter_is_idea"),
        )
        .with_column(lit(false).alias("is_idea"))
        .with_column(lit(NULL).cast(DataType::Float32).alias("nlp_top_score"))
        .select([
            col("id"),
            col("link_id"),
            col("parent_id"),
            col("subreddit"),
            col("author"),
            col("body"),
            col("permalink"),
            col("created_utc"),
            col("ups"),
            col("downs"),
            col("sanitized_prefix"),
            col("cpu_filter_is_idea"),
            col("is_idea"),
            col("nlp_top_score"),
        ])
        .collect()?;

    Ok(df_filtered)
}
