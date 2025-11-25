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

#[derive(Debug, Serialize, Deserialize)]
struct NlpJob {
    file_path: String,
    row_id: String, // Use the stable 'id' from the DataFrame
    text: String,
}

fn main() -> Result<()> {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();
    info!("--- Starting Rust Phase 2 Orchestrator (Single Threaded) ---");

    let processed_data_path = PathBuf::from(PROCESSED_DATA_DIR);
    if !processed_data_path.exists() {
        error!("Processed data directory not found: {:?}", processed_data_path);
        anyhow::bail!("Processed data directory not found.");
    }

    // redis::Client is thread-safe and can be cloned.
    let redis_client = redis::Client::open(REDIS_URL)
        .context("Failed to create Redis client")?;

    // Clear the queue once at the start.
    {
        let mut redis_conn = redis_client.get_connection()
            .context("Failed to connect to Redis for queue cleanup")?;
        let _: () = redis_conn.del(REDIS_TODO_QUEUE)
            .context("Failed to clear Redis todo queue")?;
        info!("Cleared existing jobs in Redis queue: {}", REDIS_TODO_QUEUE);
    }

    // Collect all subreddit directories from all suffix directories
    info!("Scanning for subreddit directories in {:?}...", processed_data_path);
    
    // First, get all suffix directories
    let suffix_dirs: Vec<PathBuf> = std::fs::read_dir(&processed_data_path)
        .context("Failed to read processed data directory")?
        .filter_map(|entry| {
            entry.ok().and_then(|e| {
                if e.file_type().map(|ft| ft.is_dir()).unwrap_or(false) {
                    Some(e.path())
                } else {
                    None
                }
            })
        })
        .collect();

    // Now collect all subreddit directories from each suffix
    let mut subreddits: Vec<PathBuf> = Vec::new();
    for suffix_dir in suffix_dirs {
        let subreddit_dirs = std::fs::read_dir(&suffix_dir)
            .context(format!("Failed to read suffix directory: {:?}", suffix_dir))?
            .filter_map(|entry| {
                entry.ok().and_then(|e| {
                    if e.file_type().map(|ft| ft.is_dir()).unwrap_or(false) {
                        Some(e.path())
                    } else {
                        None
                    }
                })
            });
        subreddits.extend(subreddit_dirs);
    }

    // Sort by name
    subreddits.sort();

    let total_subreddits = subreddits.len();
    info!("Found {} subreddit directories to process.", total_subreddits);

    if total_subreddits == 0 {
        info!("No subreddit directories found. Exiting.");
        return Ok(());
    }

    let pb = ProgressBar::new(total_subreddits as u64);
    pb.set_style(ProgressStyle::default_bar()
        .template("{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} ({eta}) {msg}")
        .unwrap()
        .progress_chars("#>-"));

    let mut redis_conn = redis_client.get_connection()
        .context("Failed to get Redis connection")?;

    for subreddit_path in subreddits {
        let subreddit_name = subreddit_path.file_name().unwrap_or_default().to_string_lossy();
        pb.set_message(format!("Processing r/{}", subreddit_name));
        
        // Find parquet files in this subreddit directory
        let parquet_files: Vec<PathBuf> = WalkDir::new(&subreddit_path)
            .into_iter()
            .filter_map(|e| e.ok())
            .filter(|e| e.file_type().is_file() && e.path().extension().map_or(false, |ext| ext == "parquet"))
            .map(|e| e.path().to_path_buf())
            .collect();

        for file_path in parquet_files {
             if let Err(e) = process_parquet_file(&file_path, &mut redis_conn) {
                pb.println(format!("Error processing file {:?}: {}", file_path, e));
            }
        }
        
        pb.inc(1);
    }

    pb.finish_with_message("All subreddits processed");
    info!("--- Rust Phase 2 Orchestrator Finished ---");
    Ok(())
}

fn process_parquet_file(file_path: &PathBuf, redis_conn: &mut redis::Connection) -> Result<()> {
    // This log can be very noisy, so it's commented out. Enable for deep debugging.
    // info!("Processing parquet file: {:?}", file_path);
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
    if total_rows == 0 {
        // info!("No NLP jobs needed for file: {:?}", file_path);
        return Ok(());
    }

    let chunk_size = 10_000;
    let file_path_str = file_path.to_str().context("Invalid file path string")?.to_string();

    for offset in (0..total_rows).step_by(chunk_size) {
        // Backpressure: Pause if queue is too large
        loop {
            let queue_len: u64 = redis_conn.llen(REDIS_TODO_QUEUE)
                .context("Failed to get queue length for backpressure")?;
            
            if queue_len <= 50_000 {
                break;
            }
            
            // Log occasionally or just sleep. 
            // Using a simple sleep here. 
            std::thread::sleep(std::time::Duration::from_secs(1));
        }

        let current_batch_size = std::cmp::min(chunk_size, total_rows - offset);
        let chunk = filtered_df.slice(offset as i64, current_batch_size);

        // Use a pipeline for efficiency
        let mut pipe = redis::pipe();
        pipe.atomic(); // Ensure all commands in the pipeline are executed together

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
    }

    // info!("Pushed {} NLP jobs from file {:?} to Redis.", filtered_df.height(), file_path);
    Ok(())
}