use anyhow::{Context, Result};
use log::{info, warn, error};
use polars::prelude::*;
use walkdir::WalkDir;
use std::path::PathBuf;
use std::collections::{HashMap, HashSet};
use indicatif::{ProgressBar, ProgressStyle};
use serde::{Serialize, Deserialize};

// Configuration constants
const PROCESSED_DATA_DIR: &str = "/Volumes/2TBSSD/reddit/processed";
const CHAINS_OUTPUT_DIR: &str = "/Volumes/2TBSSD/reddit/chains";
const CHECKPOINT_DIR: &str = "/Users/teomiscia/web/business-finder/rust/checkpoint";
const CHECKPOINT_FILE: &str = "phase3_progress.json";

// List of subreddit prefixes to process (same as in phase2_orchestrator)
const SUBREDDIT_PREFIXES: &[&str] = &[
    "01", "02", "03", "04", "05", "06", "07", "08", "09", "0a",
    "0b", "0c", "0d", "0e", "0f", "10", "11", "12", "13", "14",
    "15", "16", "17", "18", "19", "1a", "1b", "1c", "1d", "1e",
    "1f", "20", "21", "22", "23", "24", "25", "26", "27", "28",
    "29", "2a", "2b", "2c", "2d", "2e", "2f", "30", "31", "32",
    "33", "34", "35", "36", "37", "38", "39", "3a", "3b", "3c",
    "3d", "3e", "3f", "40", "41", "42", "43", "44", "45", "46",
    "47", "48", "49", "4a", "4b", "4c", "4d", "4e", "4f", "50",
    "51", "52", "53", "54", "55", "56", "57", "58", "59", "5a",
    "5b", "5c", "5d", "5e", "5f", "60", "61", "62", "63", "64",
    "65", "66", "67", "68", "69", "6a", "6b", "6c", "6d", "6e",
    "6f", "70", "71", "72", "73", "74", "75", "76", "77", "78",
    "79", "7a", "7b", "7c", "7d", "7e", "7f", "80", "81", "82",
    "83", "84", "85", "86", "87", "88", "89", "8a", "8b", "8c",
    "8d", "8e", "8f", "90", "91", "92", "93", "94", "95", "96",
    "97", "98", "99", "9a", "9b", "9c", "9d", "9e", "9f", "a0",
    "a1", "a2", "a3", "a4", "a5", "a6", "a7", "a8", "a9", "aa",
    "ab", "ac", "ad", "ae", "af", "b0", "b1", "b2", "b3", "b4",
    "b5", "b6", "b7", "b8", "b9", "ba", "bb", "bc", "bd", "be",
    "bf", "c0", "c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8",
    "c9", "ca", "cb", "cc", "cd", "ce", "cf", "d0", "d1", "d2",
    "d3", "d4", "d5", "d6", "d7", "d8", "d9", "da", "db", "dc",
    "dd", "de", "df", "e0", "e1", "e2", "e3", "e4", "e5", "e6",
    "e7", "e8", "e9", "ea", "eb", "ec", "ed", "ee", "ef", "f0",
    "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "fa",
    "fb", "fc", "fd", "fe", "ff",
];

#[derive(Debug, Clone)]
struct MessageNode {
    id: String,
    parent_id: Option<String>,
    link_id: Option<String>,
    body: String,
    // Store full row for later output
    row_index: usize,
}

    subreddit_index: usize,
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
    
    info!("╔══════════════════════════════════════════════════════════╗");
    info!("║   Phase 3: Building Message Chains from Ideas           ║");
    info!("╚══════════════════════════════════════════════════════════╝");
    
    let processed_data_path = PathBuf::from(PROCESSED_DATA_DIR);
    if !processed_data_path.exists() {
        error!("Processed data directory not found: {:?}", processed_data_path);
        anyhow::bail!("Processed data directory not found.");
    }

    // Create output directory
    std::fs::create_dir_all(CHAINS_OUTPUT_DIR)
        .context("Failed to create chains output directory")?;

    // Scan for all subreddit directories
    info!("📂 Scanning for subreddit directories...");
    let subreddits = scan_subreddits(&processed_data_path)?;
    info!("✓ Found {} subreddit directories", subreddits.len());

    // Load progress
    let mut progress = load_progress()?;
    info!("📍 Resuming from subreddit index: {}", progress.subreddit_index);

    let total_subreddits = subreddits.len();
    if progress.subreddit_index >= total_subreddits {
        info!("All subreddits already processed. Exiting.");
        return Ok(());
    }

    // Create progress bar
    let main_pb = ProgressBar::new(total_subreddits as u64);
    main_pb.set_style(ProgressStyle::default_bar()
        .template("{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} ({eta}) {msg}")
        .unwrap()
        .progress_chars("█▓▒░ "));
    main_pb.set_position(progress.subreddit_index as u64);

    // Process each subreddit sequentially (with checkpoint support)
    for i in progress.subreddit_index..total_subreddits {
        // Update progress index
        progress.subreddit_index = i;
        save_progress(&progress)?;

        let subreddit_path = &subreddits[i];
        
        match process_subreddit(subreddit_path, &main_pb) {
            Ok(()) => {},
            Err(e) => {
                error!("Error processing subreddit {:?}: {}", subreddit_path, e);
                // Continue to next subreddit instead of crashing
            }
        }

        main_pb.inc(1);
    }

    // Mark as fully done
    progress.subreddit_index = total_subreddits;
    save_progress(&progress)?;

    main_pb.finish_with_message("✓ Completed all subreddits");

    info!("╔══════════════════════════════════════════════════════════╗");
    info!("║   Phase 3: Complete!                                     ║");
    info!("╚══════════════════════════════════════════════════════════╝");

    Ok(())
}

/// Scan for all subreddit directories in the processed data directory
fn scan_subreddits(base_path: &PathBuf) -> Result<Vec<PathBuf>> {
    let mut subreddits = Vec::new();

    for prefix in SUBREDDIT_PREFIXES {
        let prefix_path = base_path.join(prefix);
        if !prefix_path.exists() {
            continue;
        }

        let subreddit_dirs = std::fs::read_dir(&prefix_path)?
            .filter_map(|e| e.ok().map(|e| e.path()))
            .filter(|p| p.is_dir());

        subreddits.extend(subreddit_dirs);
    }

    subreddits.sort();
    Ok(subreddits)
}

/// Process a single subreddit directory
fn process_subreddit(subreddit_path: &PathBuf, main_pb: &ProgressBar) -> Result<()> {
    let subreddit_name = subreddit_path
        .file_name()
        .unwrap_or_default()
        .to_string_lossy()
        .to_string();

    main_pb.set_message(format!("Processing r/{}", subreddit_name));

    // Find all parquet files for this subreddit
    let parquet_files: Vec<PathBuf> = WalkDir::new(subreddit_path)
        .into_iter()
        .filter_map(|e| e.ok())
        .filter(|e| {
            e.file_type().is_file() 
            && e.path().extension().map_or(false, |ext| ext == "parquet")
        })
        .map(|e| e.path().to_path_buf())
        .collect();

    if parquet_files.is_empty() {
        main_pb.inc(1);
        return Ok(());
    }

    // Read all ideas from all files in this subreddit
    let mut all_dataframes = Vec::new();
    let mut message_map: HashMap<String, MessageNode> = HashMap::new();

    for file_path in &parquet_files {
        match read_ideas_from_file(file_path) {
            Ok((df, nodes)) => {
                if df.height() > 0 {
                    all_dataframes.push(df);
                }
                for node in nodes {
                    message_map.insert(node.id.clone(), node);
                }
            }
            Err(e) => {
                warn!("Failed to read file {:?}: {}", file_path, e);
                continue;
            }
        }
    }

    if all_dataframes.is_empty() {
        main_pb.inc(1);
        return Ok(());
    }

    // Concatenate all dataframes vertically (same schema, different rows)
    let all_messages = if all_dataframes.len() == 1 {
        all_dataframes.into_iter().next().unwrap()
    } else {
        let mut combined = all_dataframes[0].clone();
        for df in &all_dataframes[1..] {
            combined = combined.vstack(df)
                .context("Failed to vertically stack dataframes")?;
        }
        combined
    };


    // Build chains: keep only messages that have a complete chain to a root
    let chain_messages = build_chains(&all_messages, &message_map)?;

    if chain_messages.height() == 0 {
        main_pb.inc(1);
        return Ok(());
    }

    // Write the chains to output
    write_chains(subreddit_path, &chain_messages)?;

    main_pb.inc(1);
    Ok(())
}

/// Read ideas from a parquet file and return both the full dataframe and message nodes
fn read_ideas_from_file(file_path: &PathBuf) -> Result<(DataFrame, Vec<MessageNode>)> {
    let file = std::fs::File::open(file_path)
        .context(format!("Failed to open file: {:?}", file_path))?;

    let df = ParquetReader::new(file)
        .finish()
        .context(format!("Failed to read parquet file: {:?}", file_path))?;

    // Filter for rows where is_idea = true
    let ideas_df = df
        .lazy()
        .filter(col("is_idea").eq(lit(true)))
        .collect()
        .context("Failed to filter for ideas")?;

    if ideas_df.height() == 0 {
        return Ok((ideas_df, Vec::new()));
    }

    // Extract message nodes for relationship building
    let id_series = ideas_df.column("id")?.str()?;
    let parent_id_series = ideas_df.column("parent_id")?.str()?;
    let link_id_series = ideas_df.column("link_id")?.str()?;
    let body_series = ideas_df.column("body")?.str()?;

    let mut nodes = Vec::new();
    for i in 0..ideas_df.height() {
        let id = id_series.get(i).context("Missing id")?.to_string();
        let parent_id = parent_id_series.get(i).map(|s| s.to_string());
        let link_id = link_id_series.get(i).map(|s| s.to_string());
        let body = body_series.get(i).context("Missing body")?.to_string();

        nodes.push(MessageNode {
            id,
            parent_id,
            link_id,
            body,
            row_index: i,
        });
    }

    Ok((ideas_df, nodes))
}

/// Build chains by keeping only messages that have a complete path to a root (parent_id = null)
fn build_chains(
    df: &DataFrame,
    message_map: &HashMap<String, MessageNode>,
) -> Result<DataFrame> {
    let mut valid_ids = HashSet::new();

    // For each message, check if it has a complete chain to root
    for (id, node) in message_map.iter() {
        if has_path_to_root(node, message_map, &mut HashSet::new()) {
            valid_ids.insert(id.clone());
        }
    }

    if valid_ids.is_empty() {
        return Ok(DataFrame::default().lazy().collect()?);
    }

    // Filter the dataframe to keep only valid IDs
    let id_series = df.column("id")?.str()?;
    let mask: BooleanChunked = id_series
        .into_iter()
        .map(|opt_id| {
            opt_id.map(|id| valid_ids.contains(id)).unwrap_or(false)
        })
        .collect();

    let filtered_df = df.filter(&mask)?;
    Ok(filtered_df)
}

/// Recursively check if a message has a path to a root (parent_id = null)
fn has_path_to_root(
    node: &MessageNode,
    message_map: &HashMap<String, MessageNode>,
    visited: &mut HashSet<String>,
) -> bool {
    // Avoid infinite loops
    if visited.contains(&node.id) {
        return false;
    }
    visited.insert(node.id.clone());

    // Check if this is a root node
    if node.parent_id.is_none() || node.parent_id.as_ref().map_or(false, |p| p.is_empty()) {
        return true;
    }

    // Extract the actual parent ID from the link format (e.g., "t1_abc123" -> "abc123")
    let parent_id = match &node.parent_id {
        Some(pid) => {
            // Reddit parent IDs are in the format "t1_xxxxx" or "t3_xxxxx"
            if pid.contains('_') {
                pid.split('_').nth(1).unwrap_or(pid).to_string()
            } else {
                pid.clone()
            }
        }
        None => return false,
    };

    // Check if parent exists in our dataset
    if let Some(parent_node) = message_map.get(&parent_id) {
        return has_path_to_root(parent_node, message_map, visited);
    }

    // Parent doesn't exist in our dataset, chain is broken
    false
}

/// Write chains to output parquet files, maintaining the same directory structure
fn write_chains(subreddit_path: &PathBuf, chain_df: &DataFrame) -> Result<()> {
    // Extract the relative path from PROCESSED_DATA_DIR
    let relative_path = subreddit_path
        .strip_prefix(PROCESSED_DATA_DIR)
        .context("Failed to get relative path")?;

    // Create the output directory with the same structure
    let output_path = PathBuf::from(CHAINS_OUTPUT_DIR).join(relative_path);
    std::fs::create_dir_all(&output_path)
        .context(format!("Failed to create output directory: {:?}", output_path))?;

    // Group by month (if created_utc exists) or write as single file
    let output_file = output_path.join("chains.parquet");
    
    let mut file = std::fs::File::create(&output_file)
        .context(format!("Failed to create output file: {:?}", output_file))?;

    ParquetWriter::new(&mut file)
        .with_compression(ParquetCompression::Zstd(None))
        .finish(&mut chain_df.clone())
        .context(format!("Failed to write parquet file: {:?}", output_file))?;

    info!(
        "✓ Wrote {} chain messages to {:?}",
        chain_df.height(),
        output_file
    );

    Ok(())
}
