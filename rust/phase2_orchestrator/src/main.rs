use anyhow::{Context, Result};
use log::{info, error};
use polars::prelude::*;
use walkdir::WalkDir;
use std::path::PathBuf;
use serde::{Serialize, Deserialize};
use redis::Commands;
use indicatif::{ProgressBar, ProgressStyle};

// Assuming Redis is running on default port
const REDIS_URL: &str = "rediss://:zBORiqFgabxlB7VMDjXvNWC2VAP9JPDWqAzCaLXjUNk%3D@businessfinder.redis.cache.windows.net:6380/";
const REDIS_TODO_QUEUE: &str = "nlp_todo_queue";

// This should ideally come from a config file or env var
const PROCESSED_DATA_DIR: &str = "/Volumes/2TBSSD/reddit/processed";
const CHECKPOINT_DIR: &str = "/Volumes/2TBSSD/reddit/checkpoint";
const CHECKPOINT_FILE: &str = "phase2_orchestrator.json";

#[derive(Debug, Serialize, Deserialize)]
struct NlpJob {
    file_path: String,
    row_id: String, // Use the stable 'id' from the DataFrame
    text: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct FileCheckpoint {
    path: PathBuf,
    lines_processed: usize,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct SubredditCheckpoint {
    path: PathBuf,
    files_queue: Vec<PathBuf>,
    current_file: Option<FileCheckpoint>,
    files_done: Vec<PathBuf>,
}

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
struct Checkpoint {
    subreddits_queue: Vec<PathBuf>,
    current_subreddit: Option<SubredditCheckpoint>,
    subreddits_done: Vec<PathBuf>,
}

fn save_checkpoint(checkpoint: &Checkpoint) -> Result<()> {
    std::fs::create_dir_all(CHECKPOINT_DIR).context("Failed to create checkpoint directory")?;
    let path = PathBuf::from(CHECKPOINT_DIR).join(CHECKPOINT_FILE);
    let f = std::fs::File::create(&path).context("Failed to create checkpoint file")?;
    serde_json::to_writer_pretty(f, checkpoint).context("Failed to write checkpoint")?;
    Ok(())
}

fn load_checkpoint() -> Result<Option<Checkpoint>> {
    let path = PathBuf::from(CHECKPOINT_DIR).join(CHECKPOINT_FILE);
    if path.exists() {
        let f = std::fs::File::open(&path).context("Failed to open checkpoint file")?;
        let checkpoint: Checkpoint = serde_json::from_reader(f).context("Failed to parse checkpoint")?;
        Ok(Some(checkpoint))
    } else {
        Ok(None)
    }
}

fn main() -> Result<()> {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();
    info!("--- Starting Rust Phase 2 Orchestrator (With Checkpoints) ---");

    let processed_data_path = PathBuf::from(PROCESSED_DATA_DIR);
    if !processed_data_path.exists() {
        error!("Processed data directory not found: {:?}", processed_data_path);
        anyhow::bail!("Processed data directory not found.");
    }

    let redis_client = redis::Client::open(REDIS_URL)
        .context("Failed to create Redis client")?;
    
    let mut redis_conn = redis_client.get_connection()
        .context("Failed to get Redis connection")?;

    // Load or Initialize Checkpoint
    let mut checkpoint = match load_checkpoint()? {
        Some(cp) => {
            info!("Found existing checkpoint. Resuming...");
            cp
        },
        None => {
            info!("No checkpoint found. Starting fresh.");
            
            // Clear the queue only if starting fresh
            let _: () = redis_conn.del(REDIS_TODO_QUEUE)
                .context("Failed to clear Redis todo queue")?;
            info!("Cleared existing jobs in Redis queue: {}", REDIS_TODO_QUEUE);

            // Scan for subreddits
            info!("Scanning for subreddit directories in {:?}...", processed_data_path);
            let suffix_dirs: Vec<PathBuf> = std::fs::read_dir(&processed_data_path)?
                .filter_map(|e| e.ok().map(|e| e.path()))
                .filter(|p| p.is_dir())
                .collect();

            let mut subreddits: Vec<PathBuf> = Vec::new();
            for suffix_dir in suffix_dirs {
                let subreddit_dirs = std::fs::read_dir(&suffix_dir)?
                    .filter_map(|e| e.ok().map(|e| e.path()))
                    .filter(|p| p.is_dir());
                subreddits.extend(subreddit_dirs);
            }
            subreddits.sort();
            info!("Found {} subreddit directories.", subreddits.len());

            let cp = Checkpoint {
                subreddits_queue: subreddits,
                current_subreddit: None,
                subreddits_done: Vec::new(),
            };
            save_checkpoint(&cp)?;
            cp
        }
    };

    // Progress bar setup (rough estimation based on subreddits)
    let total_subs = checkpoint.subreddits_queue.len() + checkpoint.subreddits_done.len() + if checkpoint.current_subreddit.is_some() { 1 } else { 0 };
    let pb = ProgressBar::new(total_subs as u64);
    pb.set_style(ProgressStyle::default_bar()
        .template("{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} ({eta}) {msg}")
        .unwrap()
        .progress_chars("#>-"));
    pb.set_position(checkpoint.subreddits_done.len() as u64);

    loop {
        // 1. Check if we need to pick a new subreddit
        if checkpoint.current_subreddit.is_none() {
            if checkpoint.subreddits_queue.is_empty() {
                break; // All done
            }
            let next_sub = checkpoint.subreddits_queue.remove(0);
            
            // Scan files for this subreddit
            let parquet_files: Vec<PathBuf> = WalkDir::new(&next_sub)
                .into_iter()
                .filter_map(|e| e.ok())
                .filter(|e| e.file_type().is_file() && e.path().extension().map_or(false, |ext| ext == "parquet"))
                .map(|e| e.path().to_path_buf())
                .collect();
            
            let mut sorted_files = parquet_files;
            sorted_files.sort();

            checkpoint.current_subreddit = Some(SubredditCheckpoint {
                path: next_sub,
                files_queue: sorted_files,
                current_file: None,
                files_done: Vec::new(),
            });
            save_checkpoint(&checkpoint)?;
        }

        // 2. Check if we need to pick a new file in the current subreddit
        let sub_finished = {
            let sub = checkpoint.current_subreddit.as_ref().unwrap();
            sub.current_file.is_none() && sub.files_queue.is_empty()
        };

        if sub_finished {
            let sub = checkpoint.current_subreddit.take().unwrap();
            checkpoint.subreddits_done.push(sub.path);
            pb.inc(1);
            save_checkpoint(&checkpoint)?;
            continue;
        }

        // 3. Pick next file if needed
        let need_next_file = checkpoint.current_subreddit.as_ref().unwrap().current_file.is_none();
        if need_next_file {
            let sub = checkpoint.current_subreddit.as_mut().unwrap();
            let next_file = sub.files_queue.remove(0);
            sub.current_file = Some(FileCheckpoint { path: next_file, lines_processed: 0 });
            save_checkpoint(&checkpoint)?;
        }

        // 4. Process the current file
        let (file_path, start_offset) = {
            let sub = checkpoint.current_subreddit.as_ref().unwrap();
            let file = sub.current_file.as_ref().unwrap();
            (file.path.clone(), file.lines_processed)
        };
        
        let sub_name = checkpoint.current_subreddit.as_ref().unwrap().path.file_name().unwrap_or_default().to_string_lossy().to_string();
        pb.set_message(format!("Processing r/{} - {:?}", sub_name, file_path.file_name().unwrap_or_default()));

        let result = process_parquet_file(
            &file_path,
            &mut redis_conn,
            start_offset,
            |new_lines| {
                let sub = checkpoint.current_subreddit.as_mut().unwrap();
                let file = sub.current_file.as_mut().unwrap();
                file.lines_processed = new_lines;
                save_checkpoint(&checkpoint)
            }
        );

        if let Err(e) = result {
            pb.println(format!("Error processing file {:?}: {}", file_path, e));
            // We return error here to stop the pipeline so user can investigate.
            // Checkpoint is saved at last successful chunk.
            return Err(e);
        }

        // 5. Mark file as done
        {
            let sub = checkpoint.current_subreddit.as_mut().unwrap();
            let file = sub.current_file.take().unwrap();
            sub.files_done.push(file.path);
            save_checkpoint(&checkpoint)?;
        }
    }

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
    let file = std::fs::File::open(file_path)
        .context(format!("Failed to open file: {:?}", file_path))?;
        
    let df = ParquetReader::new(file)
        .finish()
        .context(format!("Failed to read parquet file: {:?}", file_path))?;

    // Filter for rows that need NLP processing
    let filtered_df = df.lazy()
        .filter(
            col("cpu_filter_is_idea").eq(lit(true))
            .and(col("is_idea").eq(lit(false))) // Not yet classified as an idea by NLP
            .and(col("nlp_top_score").is_null()) // No NLP score yet
        )
        .select(&[col("body"), col("id")]) // Select body and a unique ID
        .collect()
        .context("Failed to filter DataFrame")?;

    let total_rows = filtered_df.height();
    if total_rows == 0 || start_offset >= total_rows {
        return Ok(());
    }

    let chunk_size = 10_000;
    let file_path_str = file_path.to_str().context("Invalid file path string")?.to_string();

    // Start loop from start_offset
    // We align start_offset to chunk boundaries if needed, or just process.
    // The logic below handles arbitrary start_offset.
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