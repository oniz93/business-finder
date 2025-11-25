
// ==================================================================================
// PHASE 1.5: Compaction
// ==================================================================================

fn run_compaction() -> Result<()> {
    // 1. Discover all prefix directories
    let mut prefix_dirs = Vec::new();
    for entry in fs::read_dir(INTERMEDIATE_DATA_DIR)? {
        let entry = entry?;
        if entry.file_type()?.is_dir() {
            // Ignore checkpoints directory
            if entry.file_name() == "checkpoints" {
                continue;
            }
            prefix_dirs.push(entry.path());
        }
    }
    
    prefix_dirs.sort();
    
    info!("Phase 1.5: Found {} prefix directories to compact.", prefix_dirs.len());
    
    let pb = MultiProgress::new();
    let style = ProgressStyle::default_bar()
        .template("{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} ({eta}) {msg}")
        .unwrap()
        .progress_chars("#>-");
        
    let overall_pb = pb.add(ProgressBar::new(prefix_dirs.len() as u64));
    overall_pb.set_style(style.clone());
    overall_pb.set_message("Compacting prefixes");

    // Parallel processing of prefixes
    prefix_dirs.par_iter().for_each(|prefix_path| {
        let prefix_name = prefix_path.file_name().unwrap().to_string_lossy();
        
        // Find all part-*.parquet files
        let pattern = prefix_path.join("part-*.parquet");
        let pattern_str = pattern.to_str().unwrap();
        
        let mut original_files = Vec::new();
        if let Ok(paths) = glob(pattern_str) {
            for path in paths {
                if let Ok(p) = path {
                    original_files.push(p);
                }
            }
        }
        
        if original_files.is_empty() {
            overall_pb.inc(1);
            return;
        }
        
        // Read all files into one DataFrame
        // We use LazyFrame for better performance and memory management
        let args = ScanArgsParquet::default();
        let lf_result = LazyFrame::scan_parquet_files(original_files.clone().into(), args);
        
        match lf_result {
            Ok(lf) => {
                match lf.collect() {
                    Ok(combined_df) => {
                        if combined_df.height() == 0 {
                             // Clean up empty files
                            for f in &original_files {
                                let _ = fs::remove_file(f);
                            }
                        } else {
                            // Remove original small files
                            for f in &original_files {
                                let _ = fs::remove_file(f);
                            }
                            
                            // Write back in larger chunks
                            let compaction_row_limit = 1_000_000; // Same as python code
                            
                            if combined_df.height() <= compaction_row_limit {
                                let output_file = prefix_path.join(format!("compacted-{}.parquet", Uuid::new_v4()));
                                let mut file = File::create(&output_file).expect("Failed to create compacted file");
                                let mut df_to_write = combined_df.clone();
                                
                                let _ = ParquetWriter::new(&mut file)
                                    .with_compression(ParquetCompression::Zstd(None))
                                    .finish(&mut df_to_write);
                            } else {
                                // Split into multiple files
                                let mut offset = 0;
                                let mut part_idx = 0;
                                
                                while offset < combined_df.height() {
                                    let length = std::cmp::min(compaction_row_limit, combined_df.height() - offset);
                                    let mut chunk = combined_df.slice(offset as i64, length);
                                    
                                    let output_file = prefix_path.join(format!("compacted-{}_part_{}.parquet", Uuid::new_v4(), part_idx));
                                    let mut file = File::create(&output_file).expect("Failed to create compacted chunk file");
                                    
                                    let _ = ParquetWriter::new(&mut file)
                                        .with_compression(ParquetCompression::Zstd(None))
                                        .finish(&mut chunk);
                                        
                                    offset += length;
                                    part_idx += 1;
                                }
                            }
                        }
                    },
                    Err(e) => error!("Error collecting dataframe for {}: {}", prefix_name, e),
                }
            },
            Err(e) => error!("Error scanning parquet files for {}: {}", prefix_name, e),
        }
        
        overall_pb.inc(1);
    });
    
    overall_pb.finish_with_message("Compaction complete");
    
    Ok(())
}
