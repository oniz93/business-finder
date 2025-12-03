use anyhow::{Context, Result};
use log::{info, error};
use polars::prelude::*;
use serde::Deserialize;
use std::collections::HashMap;
use redis::Commands;

// Configuration
const REDIS_URL: &str = "redis://:kRoGWJXNK75zMIcJz4RDDhNhz1hfKq6OLAzCaCFPVIw%3D@businessfinder.canadacentral.redis.azure.net:10000/0";
//const REDIS_URL: &str = "redis://localhost:6379/0";

const REDIS_RESULTS_QUEUE: &str = "nlp_results_queue";
const BATCH_SIZE: usize = 10000; // Number of results to accumulate before writing
const BATCH_TIMEOUT_SECS: usize = 3600; // Max time to wait for a full batch (1 hour)

#[derive(Debug, Deserialize, Clone)]
struct NlpResult {
    file_path: String,
    row_id: String,
    nlp_label: String,
    nlp_score: f32,
}

fn main() -> Result<()> {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();
    info!("--- Starting Rust Phase 2 Writer ---");

    let redis_client = redis::Client::open(REDIS_URL)?;
    let mut redis_conn = redis_client.get_connection()?;

    let mut results_batch: HashMap<String, Vec<NlpResult>> = HashMap::new();
    let mut total_processed_in_batch = 0;

    loop {        
        // Non-blocking batch pop
        let batch_size_nz = std::num::NonZeroUsize::new(BATCH_SIZE);
        let messages: Vec<String> = redis_conn.lpop(REDIS_RESULTS_QUEUE, batch_size_nz)?;
        
        let messages_fetched = messages.len();

        for json in messages {
            let result: NlpResult = match serde_json::from_str(&json) {
                Ok(res) => res,
                Err(e) => {
                    error!("Failed to deserialize NLP result from Redis: {}. Payload: {}", e, json);
                    continue; 
                }
            };
            
            results_batch.entry(result.file_path.clone()).or_default().push(result);
            total_processed_in_batch += 1;
        }
        
        if messages_fetched > 0 {
            info!("Fetched {} messages from Redis queue", messages_fetched);
        }

        // If we got no messages, use blocking pop to wait for new ones
        if messages_fetched == 0 {
            let redis_result: Option<(String, String)> = redis_conn.blpop(REDIS_RESULTS_QUEUE, BATCH_TIMEOUT_SECS as f64)?;
            
            match redis_result {
                Some((_queue_name, result_json)) => {
                    let result: NlpResult = match serde_json::from_str(&result_json) {
                        Ok(res) => res,
                        Err(e) => {
                            error!("Failed to deserialize NLP result from Redis: {}. Payload: {}", e, result_json);
                            continue; // Skip this malformed entry
                        }
                    };
                    
                    results_batch.entry(result.file_path.clone()).or_default().push(result);
                    total_processed_in_batch += 1;
                }
                None => {
                    // Timeout occurred
                    if !results_batch.is_empty() {
                        info!("Redis queue timed out, writing remaining {} results...", total_processed_in_batch);
                        if let Err(e) = write_batches(&mut results_batch) {
                            error!("Failed during final batch write: {}", e);
                        }
                        total_processed_in_batch = 0;
                    } else {
                        info!("Redis results queue has been empty for {} seconds. Shutting down.", BATCH_TIMEOUT_SECS);
                        break; // Exit the loop
                    }
                }
            }
        }

        // Check if we should write the batch
        if total_processed_in_batch >= BATCH_SIZE {
            info!("Batch size of {} reached. Writing to files...", BATCH_SIZE);
            if let Err(e) = write_batches(&mut results_batch) {
                error!("Failed during batch write: {}", e);
            }
            total_processed_in_batch = 0; // Reset counter
        }
    }

    info!("--- Rust Phase 2 Writer Finished ---");
    Ok(())
}

fn write_batches(batches: &mut HashMap<String, Vec<NlpResult>>) -> Result<()> {
    for (file_path, results) in batches.iter() {
        if let Err(e) = write_single_file_update(file_path, results) {
            error!("Failed to write update for file {}: {}. Results for this file will be dropped.", file_path, e);
        }
    }
    batches.clear();
    Ok(())
}

fn write_single_file_update(file_path: &str, results: &[NlpResult]) -> Result<()> {
    info!("Updating {} results in file: {}", results.len(), file_path);

    // 1. Create a DataFrame from the NLP results
    let ids: Vec<String> = results.iter().map(|r| r.row_id.clone()).collect();
    let labels: Vec<String> = results.iter().map(|r| r.nlp_label.clone()).collect();
    let scores: Vec<f32> = results.iter().map(|r| r.nlp_score).collect();

    let results_df = df!(
        "id" => &ids,
        "new_nlp_label" => &labels,
        "new_nlp_score" => &scores
    )?;

    // 2. Read the original Parquet file (open and close immediately)
    let original_df = {
        let file = std::fs::File::open(file_path)
            .context(format!("Failed to open original parquet file: {}", file_path))?;
        ParquetReader::new(file)
            .finish()
            .context(format!("Failed to read original parquet file: {}", file_path))?
    }; // File handle is dropped here, releasing any locks

    // 3. Join the results
    let joined_df = original_df.lazy()
        .left_join(results_df.lazy(), col("id"), col("id"))
        .collect()?;

    // 4. Update the columns using coalesce to fill in new values
    let final_df = joined_df.lazy()
        .with_column(
            when(col("new_nlp_label").is_not_null())
                .then(col("new_nlp_label").eq(lit("idea")))
                .otherwise(col("is_idea"))
                .alias("is_idea")
        )
        .with_column(
            coalesce(&[col("new_nlp_score"), col("nlp_top_score")])
                .alias("nlp_top_score")
        )
        .select(&[
            col("id"), col("link_id"), col("parent_id"), col("subreddit"),
            col("author"), col("body"), col("permalink"), col("created_utc"),
            col("ups"), col("downs"), col("sanitized_prefix"),
            col("cpu_filter_is_idea"), col("is_idea"), col("nlp_top_score")
        ])
        .collect()?;

    // 5. Write to a temporary file first (atomic operation)
    let temp_path = format!("{}.tmp.{}", file_path, std::process::id());
    {
        let mut temp_file = std::fs::File::create(&temp_path)
            .context(format!("Failed to create temporary file: {}", temp_path))?;
        ParquetWriter::new(&mut temp_file)
            .with_compression(ParquetCompression::Zstd(None))
            .finish(&mut final_df.clone())
            .context(format!("Failed to write to temporary parquet file: {}", temp_path))?;
    } // temp_file is closed here

    // 6. Atomically replace the original file with the temp file
    std::fs::rename(&temp_path, file_path)
        .context(format!("Failed to replace original file {} with updated version", file_path))?;

    info!("Successfully updated file: {}", file_path);
    Ok(())
}