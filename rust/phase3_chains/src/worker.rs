use anyhow::{Context, Result};
use log::{info, warn, error};
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpStream;
use tokio::sync::Mutex;
use uuid::Uuid;
use walkdir::WalkDir;

use crate::discovery::discover_coordinator;
use crate::processing::process_subreddit;
use crate::protocol::{Message, TaskStatus};

/// Worker configuration
pub struct WorkerConfig {
    pub worker_id: String,
    pub coordinator_addr: Option<String>,
    pub data_dir: PathBuf,
    pub output_dir: PathBuf,
    pub local_cache_dir: Option<PathBuf>,
}

async fn send_message(stream: &mut TcpStream, message: &Message) -> Result<()> {
    let msg_bytes = message.to_bytes()?;
    let len_bytes = (msg_bytes.len() as u32).to_be_bytes();
    stream.write_all(&len_bytes).await?;
    stream.write_all(&msg_bytes).await?;
    Ok(())
}

async fn receive_message(stream: &mut TcpStream) -> Result<Message> {
    let mut len_bytes = [0u8; 4];
    stream.read_exact(&mut len_bytes).await?;
    let msg_len = u32::from_be_bytes(len_bytes) as usize;

    if msg_len > 10_000_000 {
        anyhow::bail!("Message too large: {} bytes", msg_len);
    }

    let mut msg_bytes = vec![0u8; msg_len];
    stream.read_exact(&mut msg_bytes).await?;

    Message::from_bytes(&msg_bytes)
}

/// Copy directory contents recursively
fn copy_dir_all(src: &Path, dst: &Path) -> Result<()> {
    std::fs::create_dir_all(dst)?;
    
    for entry in WalkDir::new(src).min_depth(1) {
        let entry = entry?;
        let path = entry.path();
        let relative = path.strip_prefix(src)?;
        let dest_path = dst.join(relative);
        
        if entry.file_type().is_dir() {
            std::fs::create_dir_all(&dest_path)?;
        } else {
            if let Some(parent) = dest_path.parent() {
                std::fs::create_dir_all(parent)?;
            }
            std::fs::copy(path, &dest_path)?;
        }
    }
    
    Ok(())
}

/// Count parquet files in a directory
fn count_parquet_files(dir: &Path) -> Result<usize> {
    let count = WalkDir::new(dir)
        .into_iter()
        .filter_map(|e| e.ok())
        .filter(|e| {
            e.file_type().is_file()
                && e.path().extension().map_or(false, |ext| ext == "parquet")
        })
        .count();
    Ok(count)
}

/// Process a task with smart caching
fn process_task_with_caching(
    relative_path: &str,
    data_dir: &Path,
    output_dir: &Path,
    local_cache_dir: Option<&Path>,
) -> Result<()> {
    let subreddit_path = data_dir.join(relative_path);
    
    if !subreddit_path.exists() {
        anyhow::bail!("Subreddit path does not exist: {:?}", subreddit_path);
    }

    // Count parquet files (chunks) in the subreddit
    let num_chunks = count_parquet_files(&subreddit_path)?;
    
    info!("  Subreddit has {} parquet files", num_chunks);

    // Decide whether to use local caching
    let should_cache = num_chunks > 1 && local_cache_dir.is_some();

    if should_cache {
        let cache_dir = local_cache_dir.unwrap();
        info!("  Using local cache (multi-chunk processing)");

        // Create unique temp directory for this task
        let temp_id = Uuid::new_v4();
        let local_input_dir = cache_dir.join(format!("input_{}", temp_id));
        let local_output_dir = cache_dir.join(format!("output_{}", temp_id));

        // Copy input data to local cache
        info!("  Copying input data to local cache...");
        copy_dir_all(&subreddit_path, &local_input_dir)
            .context("Failed to copy input data to cache")?;

        // Process using local cache
        info!("  Processing from local cache...");
        std::fs::create_dir_all(&local_output_dir)
            .context("Failed to create local output directory")?;
        
        process_subreddit(&local_input_dir, &local_output_dir, cache_dir)
            .context("Failed to process subreddit from cache")?;

        // Copy results back to Samba
        info!("  Copying results back to Samba...");
        let output_path = output_dir.join(relative_path);
        std::fs::create_dir_all(&output_path)
            .context("Failed to create output directory on Samba")?;

        // Only copy the output files (chains_chunk_*.parquet)
        for entry in WalkDir::new(&local_output_dir)
            .into_iter()
            .filter_map(|e| e.ok())
            .filter(|e| e.file_type().is_file())
        {
            let path = entry.path();
            if let Some(filename) = path.file_name() {
                let dest = output_path.join(filename);
                std::fs::copy(path, &dest)
                    .context("Failed to copy result file to Samba")?;
            }
        }

        // Clean up local cache
        info!("  Cleaning up local cache...");
        if local_input_dir.exists() {
            std::fs::remove_dir_all(&local_input_dir)
                .unwrap_or_else(|e| warn!("Failed to remove local input dir: {}", e));
        }
        if local_output_dir.exists() {
            std::fs::remove_dir_all(&local_output_dir)
                .unwrap_or_else(|e| warn!("Failed to remove local output dir: {}", e));
        }

        info!("  ✓ Task completed with local caching");
    } else {
        info!("  Processing directly on Samba (single chunk or no cache dir)");
        
        // Process directly on Samba mount
        process_subreddit(&subreddit_path, output_dir, data_dir)
            .context("Failed to process subreddit on Samba")?;

        info!("  ✓ Task completed on Samba");
    }

    Ok(())
}

/// Run as worker - connect to coordinator and process tasks
pub async fn run_worker(config: WorkerConfig) -> Result<()> {
    info!("╔══════════════════════════════════════════════════════════╗");
    info!("║   Phase 3: Worker Mode                                   ║");
    info!("╚══════════════════════════════════════════════════════════╝");
    info!("Worker ID: {}", config.worker_id);

    // Determine coordinator address
    let coordinator_addr = if let Some(addr) = config.coordinator_addr {
        info!("Using manual coordinator address: {}", addr);
        addr
    } else {
        info!("Attempting mDNS discovery...");
        discover_coordinator(std::time::Duration::from_secs(30))?
    };

    info!("Connecting to coordinator at {}...", coordinator_addr);
    let stream = TcpStream::connect(&coordinator_addr)
        .await
        .context("Failed to connect to coordinator")?;
    info!("✓ Connected to coordinator");

    // Verify directories
    if !config.data_dir.exists() {
        error!("Data directory not found: {:?}", config.data_dir);
        anyhow::bail!("Data directory not found");
    }
    std::fs::create_dir_all(&config.output_dir)
        .context("Failed to create output directory")?;

    if let Some(cache_dir) = &config.local_cache_dir {
        std::fs::create_dir_all(cache_dir)
            .context("Failed to create local cache directory")?;
        info!("Using local cache directory: {:?}", cache_dir);
    } else {
        info!("No local cache directory specified - will process directly on Samba");
    }

    // Wrap stream in Arc<Mutex> for sharing between tasks
    let stream = Arc::new(Mutex::new(stream));
    
    // Start heartbeat task
    let heartbeat_stream = Arc::clone(&stream);
    let worker_id_hb = config.worker_id.clone();
    tokio::spawn(async move {
        let mut interval = tokio::time::interval(tokio::time::Duration::from_secs(30));
        loop {
            interval.tick().await;
            let heartbeat = Message::Heartbeat {
                worker_id: worker_id_hb.clone(),
            };
            let mut stream_guard = heartbeat_stream.lock().await;
            if let Err(e) = send_message(&mut *stream_guard, &heartbeat).await {
                error!("Failed to send heartbeat: {}", e);
                break;
            }
        }
    });

    // Main work loop
    loop {
        // Request a task
        let request = Message::RequestTask {
            worker_id: config.worker_id.clone(),
        };
        {
            let mut stream_guard = stream.lock().await;
            send_message(&mut *stream_guard, &request).await?;
        }

        // Wait for response
        let response = {
            let mut stream_guard = stream.lock().await;
            receive_message(&mut *stream_guard).await?
        };

        match response {
            Message::AssignTask {
                task_id,
                relative_path,
            } => {
                info!("📦 Received task {}: {}", task_id, relative_path);

                // Process the task
                let status = match process_task_with_caching(
                    &relative_path,
                    &config.data_dir,
                    &config.output_dir,
                    config.local_cache_dir.as_deref(),
                ) {
                    Ok(()) => {
                        info!("✓ Task {} completed successfully", task_id);
                        TaskStatus::Success
                    }
                    Err(e) => {
                        error!("✗ Task {} failed: {}", task_id, e);
                        TaskStatus::Failed {
                            error: e.to_string(),
                        }
                    }
                };

                // Report completion
                let completion = Message::TaskComplete { task_id, status };
                let mut stream_guard = stream.lock().await;
                send_message(&mut *stream_guard, &completion).await?;
            }
            Message::NoTasksAvailable => {
                info!("No tasks available. All work is done!");
                break;
            }
            _ => {
                warn!("Unexpected message from coordinator: {:?}", response);
            }
        }
    }

    info!("╔══════════════════════════════════════════════════════════╗");
    info!("║   Worker: All tasks completed!                           ║");
    info!("╚══════════════════════════════════════════════════════════╝");

    Ok(())
}
