use anyhow::{Context, Result};
use log::{info, warn, error};
use walkdir::WalkDir;
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use serde::{Serialize, Deserialize};
use redis::Commands;
use indicatif::{ProgressBar, ProgressStyle};

// Configuration constants
const CHAINS_INPUT_DIR: &str = "/Volumes/2TBSSD/reddit/chains";
const EMBEDDINGS_OUTPUT_DIR: &str = "/Volumes/2TBSSD/reddit/embeddings";
const CHECKPOINT_DIR: &str = "/Users/teomiscia/web/business-finder/rust/checkpoint";
const SUBREDDITS_LIST_FILE: &str = "subreddits_list_phase4.json";
const PROGRESS_FILE: &str = "phase4_manager_progress.json";

// Redis configuration
const REDIS_URL: &str = "redis://:kRoGWJXNK75zMIcJz4RDDhNhz1hfKq6OLAzCaCFPVIw%3D@businessfinder.canadacentral.redis.azure.net:10000/";
const REDIS_PHASE4_QUEUE: &str = "phase4_todo_queue";

/// Job struct sent to workers via Redis
#[derive(Debug, Serialize, Deserialize, Clone)]
struct EmbeddingJob {
    /// Full path to input parquet file (from chains/)
    input_path: String,
    /// Full path to output parquet file (to embeddings/)
    output_path: String,
}

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
struct Progress {
    subreddit_index: usize,
}

fn save_progress(progress: &Progress) -> Result<()> {
    std::fs::create_dir_all(CHECKPOINT_DIR).context("Failed to create checkpoint directory")?;
    let path = PathBuf::from(CHECKPOINT_DIR).join(PROGRESS_FILE);
    let f = std::fs::File::create(&path).context("Failed to create progress file")?;
    serde_json::to_writer_pretty(f, progress).context("Failed to write progress")?;
    Ok(())
}

fn load_progress() -> Result<Progress> {
    let path = PathBuf::from(CHECKPOINT_DIR).join(PROGRESS_FILE);
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

/// Scan for all subreddit directories in the chains directory
fn scan_subreddits(base_path: &PathBuf) -> Result<Vec<PathBuf>> {
    // Get all suffix directories (00, 01, etc.)
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
    list.sort();
    info!("Sorted.");
    
    Ok(list)
}

/// Convert a chains input path to the corresponding embeddings output path
fn get_output_path(input_path: &PathBuf) -> Result<PathBuf> {
    // Extract relative path from CHAINS_INPUT_DIR
    let relative_path = input_path
        .strip_prefix(CHAINS_INPUT_DIR)
        .context("Failed to get relative path from chains directory")?;
    
    // Build output path in embeddings directory
    let output_path = PathBuf::from(EMBEDDINGS_OUTPUT_DIR).join(relative_path);
    
    Ok(output_path)
}

/// Process a single subreddit: find all parquet files and queue missing embeddings
fn process_subreddit(
    subreddit_path: &PathBuf,
    redis_conn: &mut redis::Connection,
    running: &Arc<AtomicBool>,
) -> Result<usize> {
    let subreddit_name = subreddit_path
        .file_name()
        .unwrap_or_default()
        .to_string_lossy()
        .to_string();

    // Find all parquet files in this subreddit directory
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
        return Ok(0);
    }

    let mut jobs_queued = 0;

    for input_path in parquet_files {
        // Check for shutdown signal
        if !running.load(Ordering::SeqCst) {
            info!("Shutdown requested, stopping subreddit processing");
            break;
        }

        // Calculate output path
        let output_path = match get_output_path(&input_path) {
            Ok(p) => p,
            Err(e) => {
                warn!("Failed to compute output path for {:?}: {}", input_path, e);
                continue;
            }
        };

        // Idempotency check: skip if output already exists
        if output_path.exists() {
            continue;
        }

        // Create job and push to Redis queue
        let job = EmbeddingJob {
            input_path: input_path.to_string_lossy().to_string(),
            output_path: output_path.to_string_lossy().to_string(),
        };

        let job_json = serde_json::to_string(&job)
            .context("Failed to serialize embedding job")?;

        let _: () = redis_conn.lpush(REDIS_PHASE4_QUEUE, job_json)
            .context("Failed to push job to Redis queue")?;

        jobs_queued += 1;
    }

    if jobs_queued > 0 {
        info!("  r/{}: Queued {} embedding jobs", subreddit_name, jobs_queued);
    }

    Ok(jobs_queued)
}

fn main() -> Result<()> {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();
    
    info!("╔══════════════════════════════════════════════════════════╗");
    info!("║   Phase 4 Manager: Queueing Embedding Jobs               ║");
    info!("╚══════════════════════════════════════════════════════════╝");

    // Set up graceful shutdown
    let running = Arc::new(AtomicBool::new(true));
    let running_ctrlc = running.clone();
    ctrlc::set_handler(move || {
        info!("⚠️  Shutdown signal received, finishing current work...");
        running_ctrlc.store(false, Ordering::SeqCst);
    }).context("Failed to set Ctrl+C handler")?;
    
    let chains_path = PathBuf::from(CHAINS_INPUT_DIR);
    if !chains_path.exists() {
        error!("Chains input directory not found: {:?}", chains_path);
        anyhow::bail!("Chains input directory not found.");
    }

    // Create output directory
    std::fs::create_dir_all(EMBEDDINGS_OUTPUT_DIR)
        .context("Failed to create embeddings output directory")?;

    // Connect to Redis
    let redis_client = redis::Client::open(REDIS_URL)
        .context("Failed to create Redis client")?;
    
    let mut redis_conn = redis_client.get_connection()
        .context("Failed to get Redis connection")?;

    info!("✓ Connected to Redis");

    // Get current queue length
    let queue_len: u64 = redis_conn.llen(REDIS_PHASE4_QUEUE)
        .context("Failed to get queue length")?;
    info!("Current queue length: {}", queue_len);

    // Load or scan subreddits
    let subreddits = if let Some(cached_list) = load_subreddits_list()? {
        info!("✓ Using cached list of {} subreddits", cached_list.len());
        cached_list
    } else {
        info!("📂 Scanning for subreddit directories...");
        let list = scan_subreddits(&chains_path)?;
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

    let mut total_jobs_queued = 0;

    // Process each subreddit
    for i in progress.subreddit_index..total_subreddits {
        // Check for shutdown
        if !running.load(Ordering::SeqCst) {
            info!("Shutdown requested, saving progress and exiting...");
            break;
        }

        // Update progress
        progress.subreddit_index = i;
        save_progress(&progress)?;

        let subreddit_path = &subreddits[i];
        
        let subreddit_name = subreddit_path
            .file_name()
            .unwrap_or_default()
            .to_string_lossy()
            .to_string();
        
        main_pb.set_message(format!("Scanning r/{}", subreddit_name));
        
        match process_subreddit(subreddit_path, &mut redis_conn, &running) {
            Ok(jobs) => {
                total_jobs_queued += jobs;
            },
            Err(e) => {
                error!("Error processing subreddit {:?}: {}", subreddit_path, e);
                // Continue to next subreddit instead of crashing
            }
        }

        main_pb.inc(1);
    }

    // Mark as fully done (only if not interrupted)
    if running.load(Ordering::SeqCst) {
        progress.subreddit_index = total_subreddits;
        save_progress(&progress)?;
    }

    main_pb.finish_with_message("✓ Completed scanning");

    // Get final queue length
    let final_queue_len: u64 = redis_conn.llen(REDIS_PHASE4_QUEUE)
        .context("Failed to get final queue length")?;

    info!("╔══════════════════════════════════════════════════════════╗");
    info!("║   Phase 4 Manager: Complete!                             ║");
    info!("╠══════════════════════════════════════════════════════════╣");
    info!("║   Jobs queued this run:  {:>8}                       ║", total_jobs_queued);
    info!("║   Total queue length:    {:>8}                       ║", final_queue_len);
    info!("╚══════════════════════════════════════════════════════════╝");

    Ok(())
}
