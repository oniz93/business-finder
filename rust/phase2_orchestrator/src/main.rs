use anyhow::{Context, Result};
use log::{info, error, warn};
use polars::prelude::*;
use walkdir::WalkDir;
use std::path::PathBuf;
use serde::{Serialize, Deserialize};
use redis::Commands;
use indicatif::{ProgressBar, ProgressStyle};

// Assuming Redis is running on default port
const REDIS_URL: &str = "redis://:kRoGWJXNK75zMIcJz4RDDhNhz1hfKq6OLAzCaCFPVIw%3D@businessfinder.canadacentral.redis.azure.net:10000/";
//const REDIS_URL: &str = "redis://127.0.0.1:6379/";
const REDIS_TODO_QUEUE: &str = "nlp_todo_queue";

// This should ideally come from a config file or env var
const PROCESSED_DATA_DIR: &str = "/Volumes/2TBSSD/reddit/processed";
const CHECKPOINT_DIR: &str = "/Users/teomiscia/web/business-finder/rust/checkpoint";
const SUBREDDITS_FILE: &str = "subreddits_list.json";
const CHECKPOINT_FILE: &str = "phase2_progress.json";

#[derive(Debug, Serialize, Deserialize)]
struct NlpJob {
    file_path: String,
    row_id: String, // Use the stable 'id' from the DataFrame
    text: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct FileProgress {
    filename: String,
    lines_processed: usize,
}

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
struct Progress {
    subreddit_index: usize,
    current_file: Option<FileProgress>,
}

fn save_subreddits(subreddits: &[PathBuf]) -> Result<()> {
    std::fs::create_dir_all(CHECKPOINT_DIR).context("Failed to create checkpoint directory")?;
    let path = PathBuf::from(CHECKPOINT_DIR).join(SUBREDDITS_FILE);
    let f = std::fs::File::create(&path).context("Failed to create subreddits file")?;
    serde_json::to_writer_pretty(f, subreddits).context("Failed to write subreddits list")?;
    Ok(())
}

fn load_subreddits() -> Result<Option<Vec<PathBuf>>> {
    let path = PathBuf::from(CHECKPOINT_DIR).join(SUBREDDITS_FILE);
    if path.exists() {
        let f = std::fs::File::open(&path).context("Failed to open subreddits file")?;
        let subreddits: Vec<PathBuf> = serde_json::from_reader(f).context("Failed to parse subreddits list")?;
        Ok(Some(subreddits))
    } else {
        Ok(None)
    }
}

fn save_progress(progress: &Progress) -> Result<()> {
    std::fs::create_dir_all(CHECKPOINT_DIR).context("Failed to create checkpoint directory")?;
    let path = PathBuf::from(CHECKPOINT_DIR).join(CHECKPOINT_FILE);
    let f = std::fs::File::create(&path).context("Failed to create progress file")?;
    serde_json::to_writer_pretty(f, progress).context("Failed to write progress")?;
    Ok(())
}

fn load_progress() -> Result<Progress> {
    let path = PathBuf::from(CHECKPOINT_DIR).join(CHECKPOINT_FILE);
    if path.exists() {
        let f = std::fs::File::open(&path).context("Failed to open progress file")?;
        let progress: Progress = serde_json::from_reader(f).context("Failed to parse progress")?;
        Ok(progress)
    } else {
        Ok(Progress::default())
    }
}

fn main() -> Result<()> {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();
    info!("--- Starting Rust Phase 2 Orchestrator (Optimized Checkpoints) ---");

    let processed_data_path = PathBuf::from(PROCESSED_DATA_DIR);
    if !processed_data_path.exists() {
        error!("Processed data directory not found: {:?}", processed_data_path);
        anyhow::bail!("Processed data directory not found.");
    }

    let redis_client = redis::Client::open(REDIS_URL)
        .context("Failed to create Redis client")?;
    
    let mut redis_conn = redis_client.get_connection()
        .context("Failed to get Redis connection")?;

    // 1. Load or Scan Subreddits
    let subreddits = match load_subreddits()? {
        Some(list) => {
            info!("Loaded {} subreddits from cache.", list.len());
            list
        },
        None => {
            info!("Scanning for subreddit directories in {:?}...", processed_data_path);
            let suffix_dirs: Vec<PathBuf> = std::fs::read_dir(&processed_data_path)?
                .filter_map(|e| e.ok().map(|e| e.path()))
                .filter(|p| p.is_dir())
                .collect();
            
            info!("Found {} suffix directories. Scanning each for subreddits...", suffix_dirs.len());

            let mut list: Vec<PathBuf> = Vec::new();
            for (idx, suffix_dir) in suffix_dirs.iter().enumerate() {
                let suffix_name = suffix_dir.file_name().unwrap_or_default().to_string_lossy();
                info!("Scanning suffix {}/{}: {}", idx + 1, suffix_dirs.len(), suffix_name);
                
                let subreddit_dirs = std::fs::read_dir(&suffix_dir)?
                    .filter_map(|e| e.ok().map(|e| e.path()))
                    .filter(|p| p.is_dir());
                
                let before_count = list.len();
                list.extend(subreddit_dirs);
                let added = list.len() - before_count;
                info!("  Found {} subreddits in suffix {}", added, suffix_name);
            }
            
            info!("Total {} subreddit directories found. Sorting...", list.len());
            list.sort(); // Crucial for deterministic ordering
            info!("Sorted. Saving to cache...");
            save_subreddits(&list)?;
            info!("Cache saved.");
            
            // If we are scanning fresh, we should probably clear the queue too, 
            // assuming this is a fresh start or a reset.
            // However, if we just deleted the cache file but not the progress, we might not want to.
            // But usually, if subreddits list is missing, it's a fresh start.
             let _: () = redis_conn.del(REDIS_TODO_QUEUE)
                .context("Failed to clear Redis todo queue")?;
            info!("Cleared existing jobs in Redis queue: {}", REDIS_TODO_QUEUE);
            
            list
        }
    };

    // 2. Load Progress
    let mut progress = load_progress()?;
    info!("Resuming from subreddit index: {}", progress.subreddit_index);

    let total_subreddits = subreddits.len();
    if progress.subreddit_index >= total_subreddits {
        info!("All subreddits processed. Exiting.");
        return Ok(());
    }

    let pb = ProgressBar::new(total_subreddits as u64);
    pb.set_style(ProgressStyle::default_bar()
        .template("{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} ({eta}) {msg}")
        .unwrap()
        .progress_chars("#>-"));
    pb.set_position(progress.subreddit_index as u64);

    // 3. Main Loop
    for i in progress.subreddit_index..total_subreddits {
        // Update progress index (if we just started loop, it matches; if we moved to next, it updates)
        if progress.subreddit_index != i {
            progress.subreddit_index = i;
            progress.current_file = None; // Reset file progress for new subreddit
            save_progress(&progress)?;
        }

        let sub_path = &subreddits[i];
        let sub_name = sub_path.file_name().unwrap_or_default().to_string_lossy().to_string();
        pb.set_message(format!("Processing r/{}", sub_name));

        // Scan files for this subreddit
        let parquet_files: Vec<PathBuf> = WalkDir::new(sub_path)
            .into_iter()
            .filter_map(|e| e.ok())
            .filter(|e| e.file_type().is_file() && e.path().extension().map_or(false, |ext| ext == "parquet"))
            .map(|e| e.path().to_path_buf())
            .collect();
        
        let mut sorted_files = parquet_files;
        sorted_files.sort(); // Alphabetical order

        // Determine start file
        let (start_file_idx, start_line) = if let Some(ref file_prog) = progress.current_file {
            if let Some(idx) = sorted_files.iter().position(|p| p.file_name().unwrap_or_default().to_string_lossy() == file_prog.filename) {
                (idx, file_prog.lines_processed)
            } else {
                warn!("File {} not found in r/{}. Starting from beginning of subreddit.", file_prog.filename, sub_name);
                (0, 0)
            }
        } else {
            (0, 0)
        };

        for file_idx in start_file_idx..sorted_files.len() {
            let file_path = &sorted_files[file_idx];
            let file_name = file_path.file_name().unwrap_or_default().to_string_lossy().to_string();
            
            let current_start_line = if file_idx == start_file_idx { start_line } else { 0 };

            // Update progress before starting file
            progress.current_file = Some(FileProgress {
                filename: file_name.clone(),
                lines_processed: current_start_line,
            });
            save_progress(&progress)?;

            pb.set_message(format!("Processing r/{} - {}", sub_name, file_name));

            let result = process_parquet_file(
                file_path,
                &mut redis_conn,
                current_start_line,
                |new_lines| {
                    progress.current_file = Some(FileProgress {
                        filename: file_name.clone(),
                        lines_processed: new_lines,
                    });
                    save_progress(&progress)
                }
            );

            if let Err(e) = result {
                // Check if this is a corrupted file error
                let error_msg = format!("{}", e);
                if error_msg.contains("out of specification") || 
                   error_msg.contains("PAR1") || 
                   error_msg.contains("corrupted") {
                    warn!("Skipping corrupted parquet file {:?}: {}", file_path, e);
                    pb.println(format!("⚠️  Skipping corrupted file: {:?}", file_path));
                    // Continue to next file instead of crashing
                    continue;
                } else {
                    // For other errors, still crash as they might be critical
                    pb.println(format!("Error processing file {:?}: {}", file_path, e));
                    return Err(e);
                }
            }
        }

        pb.inc(1);
    }

    // Mark as fully done
    progress.subreddit_index = total_subreddits;
    progress.current_file = None;
    save_progress(&progress)?;

    pb.finish_with_message("All subreddits processed");
    info!("--- Rust Phase 2 Orchestrator Finished ---");
    Ok(())
}

fn process_parquet_file<F>(
    file_path: &PathBuf, 
    redis_conn: &mut redis::Connection, 
    start_offset: usize,
    mut on_progress: F
) -> Result<()> 
where F: FnMut(usize) -> Result<()>
{
    // Read and filter the DataFrame, then immediately close the file
    let filtered_df = {
        let file = std::fs::File::open(file_path)
            .context(format!("Failed to open file: {:?}", file_path))?;
            
        let df = ParquetReader::new(file)
            .finish()
            .context(format!("Failed to read parquet file: {:?}", file_path))?;

        // Filter for rows that need NLP processing
        df.lazy()
            .filter(
                col("cpu_filter_is_idea").eq(lit(true))
                .and(col("is_idea").eq(lit(false))) // Not yet classified as an idea by NLP
                .and(col("nlp_top_score").is_null()) // No NLP score yet
            )
            .select(&[col("body"), col("id")]) // Select body and a unique ID
            .collect()
            .context("Failed to filter DataFrame")?
    }; // File handle is dropped here, releasing any locks

    let total_rows = filtered_df.height();
    if total_rows == 0 || start_offset >= total_rows {
        return Ok(());
    }

    let chunk_size = 10_000;
    let file_path_str = file_path.to_str().context("Invalid file path string")?.to_string();

    for offset in (start_offset..total_rows).step_by(chunk_size) {
        // Backpressure: Pause if queue is too large
        loop {
            let queue_len: u64 = redis_conn.llen(REDIS_TODO_QUEUE)
                .context("Failed to get queue length for backpressure")?;
            
            if queue_len <= 50_000 {
                break;
            }
            std::thread::sleep(std::time::Duration::from_secs(1));
        }

        let current_batch_size = std::cmp::min(chunk_size, total_rows - offset);
        let chunk = filtered_df.slice(offset as i64, current_batch_size);

        let mut pipe = redis::pipe();
        pipe.atomic(); 

        let body_series = chunk.column("body")?.str()?;
        let id_series = chunk.column("id")?.str()?; 

        for i in 0..current_batch_size {
            let job = NlpJob {
                file_path: file_path_str.clone(),
                row_id: id_series.get(i).context("Missing stable ID")?.to_string(),
                text: body_series.get(i).context("Missing body text")?.to_string(),
            };
            
            let job_json = serde_json::to_string(&job)
                .context("Failed to serialize NLP job to JSON")?;
            
            pipe.lpush(REDIS_TODO_QUEUE, job_json);
        }

        pipe.query::<()>(redis_conn)
            .context(format!("Failed to push batch of {} jobs to Redis for file {:?}", current_batch_size, file_path))?;
        
        // Update progress
        on_progress(offset + current_batch_size)?;
    }

    Ok(())
}