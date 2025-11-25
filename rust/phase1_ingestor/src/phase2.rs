use std::fs::{self, File};
use std::path::Path;

use anyhow::Result;
use glob::glob;
use indicatif::{ProgressBar, ProgressStyle};
use log::{error, info, warn};
use polars::prelude::*;
use polars::io::parquet::ParquetReader;
use uuid::Uuid;

use crate::constants::{INTERMEDIATE_DATA_DIR, PROCESSED_DATA_DIR};

pub fn run_phase_2() -> Result<()> {
    info!("=== STARTING PHASE 2: Partitioning by Subreddit (Threaded - 8 Workers) ===");

    // 1. Discover all parquet files in INTERMEDIATE_DATA_DIR
    let glob_pattern = format!("{}/**/*.parquet", INTERMEDIATE_DATA_DIR);
    let mut parquet_files = Vec::new();

    for entry in glob(&glob_pattern)? {
        match entry {
            Ok(path) => parquet_files.push(path),
            Err(e) => warn!("Error reading glob entry: {}", e),
        }
    }

    if parquet_files.is_empty() {
        warn!("Phase 2: No intermediate parquet files found.");
        return Ok(());
    }

    info!(
        "Phase 2: Found {} parquet files to process.",
        parquet_files.len()
    );

    let pb = ProgressBar::new(parquet_files.len() as u64);
    pb.set_style(
        ProgressStyle::default_bar()
            .template("[{elapsed_precise}] {bar:40.cyan/blue} {pos}/{len} files ({eta}) {msg}")
            .unwrap(),
    );
    
    // Wrap PB in Arc to share across threads (indicatif PBs are thread-safe internally)
    // but we need Arc to clone the handle.
    // Actually indicatif::ProgressBar is Clone and points to the same state? 
    // Yes, ProgressBar is a cheap clone that shares state.
    
    // 2. Process files using explicit worker threads (8)
    // This ensures exactly 8 files are being processed at once.
    let num_workers = 8;
    let (tx, rx) = crossbeam_channel::bounded(parquet_files.len());

    for path in parquet_files {
        tx.send(path).unwrap();
    }
    drop(tx); // Close sender so workers know when to stop

    let mut handles = Vec::with_capacity(num_workers);

    for i in 0..num_workers {
        let rx_worker = rx.clone();
        let pb_worker = pb.clone();
        
        let handle = std::thread::Builder::new()
            .name(format!("p2-worker-{}", i))
            .spawn(move || {
                while let Ok(file_path) = rx_worker.recv() {
                    let file_name = file_path.file_name().unwrap().to_string_lossy().to_string();
                    pb_worker.set_message(format!("Processing {}", file_name));

                    if let Err(e) = process_intermediate_file(&file_path) {
                        error!("Error processing file {:?}: {}", file_path, e);
                    }
                    pb_worker.inc(1);
                }
            })?;
        handles.push(handle);
    }

    // Wait for all workers to finish
    for h in handles {
        h.join().unwrap();
    }

    pb.finish_with_message("Phase 2 partitioning complete.");
    Ok(())
}

fn process_intermediate_file(file_path: &Path) -> Result<()> {
    // Infer prefix from parent directory
    let prefix = file_path
        .parent()
        .and_then(|p| p.file_name())
        .and_then(|s| s.to_str())
        .unwrap_or("misc")
        .to_string();

    // Read the file using ParquetReader to ensure FD is closed immediately
    let df = {
        let file = File::open(file_path)?;
        let df = ParquetReader::new(file).finish()?;
        // file goes out of scope and is dropped here
        df
    };

    if df.height() == 0 {
        return Ok(());
    }

    // Manual partition by subreddit to ensure sequential processing and compatibility
    let s = df.column("subreddit")?.cast(&DataType::String)?;
    let ca = s.str()?;
    let unique_subreddits: Vec<String> = ca
        .unique()?
        .into_iter()
        .flatten()
        .map(|s| s.to_string())
        .collect();

    for subreddit in unique_subreddits {
        let mask = ca.equal(subreddit.as_str());
        let mut sub_df = df.filter(&mask)?;

        let safe_subreddit = subreddit
            .chars()
            .filter(|c| c.is_alphanumeric() || *c == '_')
            .collect::<String>();

        // Output path: PROCESSED_DATA_DIR/<prefix>/<safe_subreddit>/
        let output_dir = Path::new(PROCESSED_DATA_DIR)
            .join(&prefix)
            .join(&safe_subreddit);
        fs::create_dir_all(&output_dir)?;

        // Wrap file write in scope to ensure immediate cleanup
        {
            let output_file = output_dir.join(format!("part-{}.parquet", Uuid::new_v4()));
            let mut file = File::create(&output_file)?;

            ParquetWriter::new(&mut file)
                .with_compression(ParquetCompression::Zstd(None))
                .finish(&mut sub_df)?;

            // Explicitly drop to close file handle immediately
            drop(file);
        }
    }

    Ok(())
}
