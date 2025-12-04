use anyhow::{Context, Result};
use indicatif::{ProgressBar, ProgressStyle};
use log::{error, info};
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};

use crate::processing::process_subreddit;

// Default checkpoint directory - will be created relative to current directory if not absolute
const CHECKPOINT_DIR: &str = "checkpoint";
const CHECKPOINT_FILE: &str = "phase3_progress.json";
const SUBREDDITS_LIST_FILE: &str = "subreddits_list.json";

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
struct Progress {
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

fn save_subreddits_list(subreddits: &[PathBuf]) -> Result<()> {
    std::fs::create_dir_all(CHECKPOINT_DIR).context("Failed to create checkpoint directory")?;
    let path = PathBuf::from(CHECKPOINT_DIR).join(SUBREDDITS_LIST_FILE);
    let f = std::fs::File::create(&path).context("Failed to create subreddits list file")?;
    serde_json::to_writer_pretty(f, subreddits).context("Failed to write subreddits list")?;
    Ok(())
}

fn load_subreddits_list() -> Result<Option<Vec<PathBuf>>> {
    let path = PathBuf::from(CHECKPOINT_DIR).join(SUBREDDITS_LIST_FILE);
    if path.exists() {
        info!("✓ Found cached subreddits list at {:?}", path);
        let f = std::fs::File::open(&path).context("Failed to open subreddits list file")?;
        let subreddits: Vec<PathBuf> = serde_json::from_reader(f)
            .context("Failed to parse subreddits list")?;
        Ok(Some(subreddits))
    } else {
        Ok(None)
    }
}

/// Find a specific subreddit path by name
fn find_subreddit_path(base_path: &Path, subreddit_name: &str) -> Result<PathBuf> {
    // First, get all suffix directories (01, 02, etc.)
    let suffix_dirs: Vec<PathBuf> = std::fs::read_dir(base_path)?
        .filter_map(|e| e.ok().map(|e| e.path()))
        .filter(|p| p.is_dir())
        .collect();
    
    for suffix_dir in suffix_dirs {
        let potential_path = suffix_dir.join(subreddit_name);
        if potential_path.exists() && potential_path.is_dir() {
            return Ok(potential_path);
        }
    }
    
    anyhow::bail!("Subreddit '{}' not found in any suffix directory", subreddit_name);
}

/// Scan for all subreddit directories in the processed data directory
fn scan_subreddits(base_path: &Path) -> Result<Vec<PathBuf>> {
    // First, get all suffix directories (01, 02, etc.)
    let suffix_dirs: Vec<PathBuf> = std::fs::read_dir(base_path)?
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
    info!("Sorted.");
    
    Ok(list)
}

/// Run in standalone mode - processes all subreddits on a single machine
pub fn run_standalone(
    data_dir: &Path,
    output_dir: &Path,
    subreddit_filter: Option<String>,
) -> Result<()> {
    info!("╔══════════════════════════════════════════════════════════╗");
    info!("║   Phase 3: Building Message Chains (Standalone Mode)    ║");
    info!("╚══════════════════════════════════════════════════════════╝");
    
    if !data_dir.exists() {
        error!("Processed data directory not found: {:?}", data_dir);
        anyhow::bail!("Processed data directory not found.");
    }

    // Create output directory
    std::fs::create_dir_all(output_dir)
        .context("Failed to create chains output directory")?;

    // Handle single subreddit mode
    if let Some(subreddit_name) = subreddit_filter {
        info!("🎯 Single subreddit mode: {}", subreddit_name);
        
        // Find the subreddit path
        let subreddit_path = find_subreddit_path(data_dir, &subreddit_name)?;
        
        info!("Found subreddit at: {:?}", subreddit_path);
        
        // Process this single subreddit
        process_subreddit(&subreddit_path, output_dir, data_dir)?;
        
        info!("╔══════════════════════════════════════════════════════════╗");
        info!("║   Phase 3: Complete (Single Subreddit)!                 ║");
        info!("╚══════════════════════════════════════════════════════════╝");
        
        return Ok(());
    }

    // Scan for all subreddit directories or load from cache
    let subreddits = if let Some(cached_list) = load_subreddits_list()? {
        info!("✓ Using cached list of {} subreddits", cached_list.len());
        cached_list
    } else {
        info!("📂 Scanning for subreddit directories...");
        let list = scan_subreddits(data_dir)?;
        info!("✓ Found {} subreddit directories", list.len());
        
        // Save the list for future runs
        save_subreddits_list(&list)?;
        info!("✓ Saved subreddits list to checkpoint");
        
        list
    };

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
        
        let subreddit_name = subreddit_path
            .file_name()
            .unwrap_or_default()
            .to_string_lossy()
            .to_string();
        
        main_pb.set_message(format!("Processing r/{}", subreddit_name));
        
        match process_subreddit(subreddit_path, output_dir, data_dir) {
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
