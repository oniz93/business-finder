use anyhow::{Context, Result};
use log::{error, info, warn};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, VecDeque};
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};
use uuid::Uuid;

use crate::constants::MAX_MESSAGE_SIZE;
use crate::discovery::announce_coordinator;
use crate::protocol::{Message, TaskStatus};

// Checkpoint directory and files
const CHECKPOINT_DIR: &str = "checkpoint";
const COORDINATOR_CHECKPOINT_FILE: &str = "coordinator_state.json";
const STANDALONE_CHECKPOINT_FILE: &str = "phase3_progress.json";
const SUBREDDITS_LIST_FILE: &str = "subreddits_list.json";

#[derive(Debug, Clone, Serialize, Deserialize)]
enum TaskState {
    Pending,
    Assigned { worker_id: String },
    Completed,
    Failed {
        error: String
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Task {
    id: Uuid,
    relative_path: String,
    state: TaskState,
}

/// Serializable checkpoint format for coordinator state
#[derive(Debug, Serialize, Deserialize)]
struct CoordinatorCheckpoint {
    tasks: Vec<Task>,
    version: u32,
}

/// Old standalone checkpoint format for migration
#[derive(Debug, Deserialize)]
struct StandaloneProgress {
    subreddit_index: usize,
}

struct CoordinatorState {
    task_queue: VecDeque<Task>,
    tasks: HashMap<Uuid, Task>,
    worker_heartbeats: HashMap<String, std::time::Instant>,
}

impl CoordinatorState {
    fn new(subreddits: Vec<PathBuf>, data_base_dir: &Path) -> Result<Self> {
        let mut task_queue = VecDeque::new();
        let mut tasks = HashMap::new();

        for subreddit_path in subreddits {
            let relative_path = subreddit_path
                .strip_prefix(data_base_dir)
                .context("Failed to get relative path")?
                .to_string_lossy()
                .to_string();

            let task = Task {
                id: Uuid::new_v4(),
                relative_path: relative_path.clone(),
                state: TaskState::Pending,
            };

            task_queue.push_back(task.clone());
            tasks.insert(task.id, task);
        }

        info!("Created {} tasks from subreddits", tasks.len());

        Ok(Self {
            task_queue,
            tasks,
            worker_heartbeats: HashMap::new(),
        })
    }

    /// Save coordinator state to checkpoint file
    fn save_checkpoint(&self) -> Result<()> {
        std::fs::create_dir_all(CHECKPOINT_DIR).context("Failed to create checkpoint directory")?;
        let path = PathBuf::from(CHECKPOINT_DIR).join(COORDINATOR_CHECKPOINT_FILE);
        
        let checkpoint = CoordinatorCheckpoint {
            tasks: self.tasks.values().cloned().collect(),
            version: 1,
        };
        
        let f = std::fs::File::create(&path).context("Failed to create checkpoint file")?;
        serde_json::to_writer_pretty(f, &checkpoint).context("Failed to write checkpoint")?;
        
        Ok(())
    }

    /// Load coordinator state from checkpoint file
    fn load_checkpoint() -> Result<Option<Vec<Task>>> {
        let path = PathBuf::from(CHECKPOINT_DIR).join(COORDINATOR_CHECKPOINT_FILE);
        
        if path.exists() {
            info!("📍 Found coordinator checkpoint at {:?}", path);
            let f = std::fs::File::open(&path).context("Failed to open checkpoint file")?;
            let checkpoint: CoordinatorCheckpoint = serde_json::from_reader(f)
                .context("Failed to parse checkpoint")?;
            
            info!("✓ Loaded {} tasks from checkpoint (version {})", checkpoint.tasks.len(), checkpoint.version);
            return Ok(Some(checkpoint.tasks));
        }
        
        Ok(None)
    }

    /// Restore state from a list of tasks (from checkpoint or migration)
    fn from_tasks(tasks: Vec<Task>) -> Result<Self> {
        let mut task_queue = VecDeque::new();
        let mut tasks_map = HashMap::new();
        
        let mut pending_count = 0;
        let mut completed_count = 0;
        let mut assigned_count = 0;
        let mut failed_count = 0;
        
        for task in tasks {
            match &task.state {
                TaskState::Pending | TaskState::Failed { .. } => {
                    // Re-queue pending and failed tasks
                    task_queue.push_back(task.clone());
                    if matches!(task.state, TaskState::Pending) {
                        pending_count += 1;
                    } else {
                        failed_count += 1;
                    }
                }
                TaskState::Assigned { .. } => {
                    // Re-queue assigned tasks (worker may have died)
                    let mut reassigned_task = task.clone();
                    reassigned_task.state = TaskState::Pending;
                    task_queue.push_back(reassigned_task.clone());
                    tasks_map.insert(reassigned_task.id, reassigned_task);
                    assigned_count += 1;
                    continue; // Don't insert the original assigned task
                }
                TaskState::Completed => {
                    completed_count += 1;
                    // Don't re-queue completed tasks
                }
            }
            
            tasks_map.insert(task.id, task);
        }
        
        info!("📊 Restored state: {} pending, {} completed, {} failed, {} reassigned from assigned", 
              pending_count, completed_count, failed_count, assigned_count);
        
        Ok(Self {
            task_queue,
            tasks: tasks_map,
            worker_heartbeats: HashMap::new(),
        })
    }

    /// Migrate from old standalone checkpoint format
    fn migrate_from_standalone(subreddits: Vec<PathBuf>, data_base_dir: &Path) -> Result<Option<Vec<Task>>> {
        let standalone_path = PathBuf::from(CHECKPOINT_DIR).join(STANDALONE_CHECKPOINT_FILE);
        
        if !standalone_path.exists() {
            return Ok(None);
        }
        
        info!("📦 Found old standalone checkpoint, migrating...");
        
        let f = std::fs::File::open(&standalone_path).context("Failed to open standalone checkpoint")?;
        let progress: StandaloneProgress = serde_json::from_reader(f)
            .context("Failed to parse standalone checkpoint")?;
        
        info!("   Standalone was at subreddit index {}/{}", progress.subreddit_index, subreddits.len());
        
        let mut tasks = Vec::new();
        
        // Create tasks from subreddits, marking completed ones
        for (idx, subreddit_path) in subreddits.iter().enumerate() {
            let relative_path = subreddit_path
                .strip_prefix(data_base_dir)
                .context("Failed to get relative path")?
                .to_string_lossy()
                .to_string();
            
            let state = if idx < progress.subreddit_index {
                TaskState::Completed
            } else {
                TaskState::Pending
            };
            
            let task = Task {
                id: Uuid::new_v4(),
                relative_path,
                state,
            };
            
            tasks.push(task);
        }
        
        info!("✓ Migrated {} completed and {} pending tasks from standalone checkpoint",
              progress.subreddit_index,
              subreddits.len() - progress.subreddit_index);
        
        // Rename old checkpoint to backup
        let backup_path = PathBuf::from(CHECKPOINT_DIR).join("phase3_progress.json.migrated");
        std::fs::rename(&standalone_path, &backup_path)
            .context("Failed to backup old checkpoint")?;
        info!("   Backed up old checkpoint to {:?}", backup_path);
        
        Ok(Some(tasks))
    }

    fn assign_task(&mut self, worker_id: &str) -> Option<(Uuid, String)> {
        if let Some(mut task) = self.task_queue.pop_front() {
            task.state = TaskState::Assigned {
                worker_id: worker_id.to_string(),
            };
            let task_id = task.id;
            let relative_path = task.relative_path.clone();
            self.tasks.insert(task_id, task);
            self.worker_heartbeats
                .insert(worker_id.to_string(), std::time::Instant::now());
            Some((task_id, relative_path))
        } else {
            None
        }
    }

    fn complete_task(&mut self, task_id: Uuid, status: TaskStatus) {
        if let Some(task) = self.tasks.get_mut(&task_id) {
            match status {
                TaskStatus::Success => {
                    task.state = TaskState::Completed;
                    info!("✓ Task {} completed successfully", task_id);
                }
                TaskStatus::Failed { error } => {
                    warn!("✗ Task {} failed: {}", task_id, error);
                    task.state = TaskState::Failed { error: error.clone() };
                    // Re-queue failed tasks
                    self.task_queue.push_back(task.clone());
                }
            }
        }
    }

    fn update_heartbeat(&mut self, worker_id: &str) {
        self.worker_heartbeats
            .insert(worker_id.to_string(), std::time::Instant::now());
    }

    fn check_stale_workers(&mut self) {
        let stale_timeout = std::time::Duration::from_secs(60);
        let now = std::time::Instant::now();

        let stale_workers: Vec<String> = self
            .worker_heartbeats
            .iter()
            .filter(|(_, &last_seen)| now.duration_since(last_seen) > stale_timeout)
            .map(|(worker_id, _)| worker_id.clone())
            .collect();

        for worker_id in stale_workers {
            warn!("Worker {} is stale, reassigning tasks", worker_id);
            self.worker_heartbeats.remove(&worker_id);

            // Find tasks assigned to this worker and re-queue them
            let tasks_to_requeue: Vec<Task> = self
                .tasks
                .values()
                .filter(|task| matches!(&task.state, TaskState::Assigned { worker_id: wid } if wid == &worker_id))
                .cloned()
                .collect();

            for mut task in tasks_to_requeue {
                task.state = TaskState::Pending;
                self.task_queue.push_back(task.clone());
                self.tasks.insert(task.id, task);
            }
        }
    }

    fn get_status(&self) -> String {
        let pending = self.task_queue.len();
        let completed = self.tasks.values().filter(|t| matches!(t.state, TaskState::Completed)).count();
        let assigned = self.tasks.values().filter(|t| matches!(t.state, TaskState::Assigned { .. })).count();
        let failed = self.tasks.values().filter(|t| matches!(t.state, TaskState::Failed { .. })).count();
        
        format!(
            "Tasks: {} pending, {} assigned, {} completed, {} failed. Workers: {}",
            pending, assigned, completed, failed, self.worker_heartbeats.len()
        )
    }
}

async fn handle_worker(
    mut stream: TcpStream,
    state: Arc<Mutex<CoordinatorState>>,
) -> Result<()> {
    let peer_addr = stream.peer_addr()?;
    info!("New worker connected from {}", peer_addr);

    loop {
        // Read message length (4 bytes)
        let mut len_bytes = [0u8; 4];
        match stream.read_exact(&mut len_bytes).await {
            Ok(_) => {}
            Err(e) if e.kind() == std::io::ErrorKind::UnexpectedEof => {
                info!("Worker {} disconnected", peer_addr);
                break;
            }
            Err(e) => {
                error!("Error reading from worker {}: {}", peer_addr, e);
                break;
            }
        }

        let msg_len = u32::from_be_bytes(len_bytes) as usize;
        if msg_len > MAX_MESSAGE_SIZE {
            error!("Message too large from {}: {} bytes", peer_addr, msg_len);
            break;
        }

        // Read message
        let mut msg_bytes = vec![0u8; msg_len];
        stream.read_exact(&mut msg_bytes).await?;

        let message = Message::from_bytes(&msg_bytes)?;

        // Process message
        let response = {
            let mut state = state.lock().unwrap();

            match message {
                Message::RequestTask { worker_id } => {
                    info!("Worker {} requesting task", worker_id);
                    state.update_heartbeat(&worker_id);

                    if let Some((task_id, relative_path)) = state.assign_task(&worker_id) {
                        info!(
                            "Assigned task {} (path: {}) to worker {}",
                            task_id, relative_path, worker_id
                        );
                        Message::AssignTask {
                            task_id,
                            relative_path,
                        }
                    } else {
                        info!("No tasks available for worker {}", worker_id);
                        Message::NoTasksAvailable
                    }
                }
                Message::TaskComplete { task_id, status } => {
                    state.complete_task(task_id, status);
                    info!("Status: {}", state.get_status());
                    // Don't send a response for task completion, worker will request next task
                    continue;
                }
                Message::Heartbeat { worker_id } => {
                    state.update_heartbeat(&worker_id);
                    continue; // No response needed
                }
                _ => {
                    warn!("Unexpected message from worker: {:?}", message);
                    continue;
                }
            }
        };

        // Send response
        let response_bytes = response.to_bytes()?;
        let len_bytes = (response_bytes.len() as u32).to_be_bytes();
        stream.write_all(&len_bytes).await?;
        stream.write_all(&response_bytes).await?;
    }

    Ok(())
}

/// Scan for all subreddit directories in the processed data directory
fn scan_subreddits(base_path: &Path) -> Result<Vec<PathBuf>> {
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

/// Load or create subreddits list with caching
fn load_or_scan_subreddits(data_dir: &Path) -> Result<Vec<PathBuf>> {
    let subreddits_list_path = PathBuf::from(CHECKPOINT_DIR).join(SUBREDDITS_LIST_FILE);
    
    if subreddits_list_path.exists() {
        info!("✓ Found cached subreddits list");
        let f = std::fs::File::open(&subreddits_list_path)?;
        let subreddits: Vec<PathBuf> = serde_json::from_reader(f)?;
        info!("   Loaded {} subreddits from cache", subreddits.len());
        return Ok(subreddits);
    }
    
    info!("📂 Scanning for subreddit directories...");
    let subreddits = scan_subreddits(data_dir)?;
    info!("✓ Found {} subreddit directories", subreddits.len());
    
    // Save to cache
    std::fs::create_dir_all(CHECKPOINT_DIR)?;
    let f = std::fs::File::create(&subreddits_list_path)?;
    serde_json::to_writer_pretty(f, &subreddits)?;
    info!("   Cached subreddits list");
    
    Ok(subreddits)
}

/// Run as coordinator - distribute tasks to workers
pub async fn run_coordinator(data_dir: &Path, port: u16) -> Result<()> {
    info!("╔══════════════════════════════════════════════════════════╗");
    info!("║   Phase 3: Coordinator Mode                              ║");
    info!("╚══════════════════════════════════════════════════════════╝");

    if !data_dir.exists() {
        error!("Data directory not found: {:?}", data_dir);
        anyhow::bail!("Data directory not found.");
    }

    // Load or scan subreddits
    let subreddits = load_or_scan_subreddits(data_dir)?;

    // Try to load checkpoint, then migrate from standalone, or create new state
    let state = if let Some(tasks) = CoordinatorState::load_checkpoint()? {
        info!("🔄 Restoring from coordinator checkpoint...");
        Arc::new(Mutex::new(CoordinatorState::from_tasks(tasks)?))
    } else if let Some(tasks) = CoordinatorState::migrate_from_standalone(subreddits.clone(), data_dir)? {
        info!("🔄 Restoring from migrated standalone checkpoint...");
        let state = Arc::new(Mutex::new(CoordinatorState::from_tasks(tasks)?));
        // Save the migrated state immediately
        state.lock().unwrap().save_checkpoint()?;
        info!("✓ Saved migrated state to coordinator checkpoint");
        state
    } else {
        info!("🆕 Creating new coordinator state...");
        Arc::new(Mutex::new(CoordinatorState::new(subreddits, data_dir)?))
    };

    // Save initial checkpoint
    {
        let state_guard = state.lock().unwrap();
        state_guard.save_checkpoint()?;
        info!("✓ Saved initial checkpoint");
    }

    // Start mDNS announcement
    let _mdns = announce_coordinator(port)?;

    // Start TCP listener
    let addr = format!("0.0.0.0:{}", port);
    let listener = TcpListener::bind(&addr).await?;
    info!("🚀 Coordinator listening on {}", addr);

    // Spawn periodic status check, stale worker detection, and checkpoint saving
    let status_state = Arc::clone(&state);
    tokio::spawn(async move {
        let mut interval = tokio::time::interval(tokio::time::Duration::from_secs(30));
        loop {
            interval.tick().await;
            let mut state = status_state.lock().unwrap();
            state.check_stale_workers();
            info!("📊 {}", state.get_status());
            
            // Save checkpoint periodically
            if let Err(e) = state.save_checkpoint() {
                error!("Failed to save checkpoint: {}", e);
            }
        }
    });

    // Accept worker connections
    loop {
        let (stream, _) = listener.accept().await?;
        let state = Arc::clone(&state);

        tokio::spawn(async move {
            if let Err(e) = handle_worker(stream, state).await {
                error!("Error handling worker: {}", e);
            }
        });
    }
}
