use anyhow::{Context, Result};
use log::{info, error};
use polars::prelude::*;
use serde::Deserialize;
use std::collections::HashMap;
use redis::Commands;

// Configuration
const REDIS_URL: &str = "rediss://:zBORiqFgabxlB7VMDjXvNWC2VAP9JPDWqAzCaLXjUNk%3D@businessfinder.redis.cache.windows.net:6380/0";
const REDIS_RESULTS_QUEUE: &str = "nlp_results_queue";
const BATCH_SIZE: usize = 10; // Number of results to accumulate before writing
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
        // Blocking pop from the results queue with a timeout.
        // blpop returns a tuple: (queue_name, value)
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
                
                // Log that we received a result
                info!("Writer received result for row_id: {}", result.row_id);

                results_batch.entry(result.file_path.clone()).or_default().push(result);
                total_processed_in_batch += 1;

                if total_processed_in_batch >= BATCH_SIZE {
                    info!("Batch size of {} reached. Writing to files...", BATCH_SIZE);
                    if let Err(e) = write_batches(&mut results_batch) {
                        error!("Failed during batch write: {}", e);
                    }
                    total_processed_in_batch = 0; // Reset counter
                }
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

    // 2. Read the original Parquet file
    let original_df = ParquetReader::new(std::fs::File::open(file_path)?)
        .finish()
        .context(format!("Failed to read original parquet file: {}", file_path))?;

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

    // 5. Write the updated DataFrame back, overwriting the original file
    let mut file = std::fs::File::create(file_path)?;
    ParquetWriter::new(&mut file)
        .with_compression(ParquetCompression::Zstd(None))
        .finish(&mut final_df.clone())
        .context(format!("Failed to write updated parquet file: {}", file_path))?;

    info!("Successfully updated file: {}", file_path);
    Ok(())
}