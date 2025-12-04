use anyhow::{Context, Result};
use log::{error, info, warn};
use std::collections::{HashMap, VecDeque};
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};
use uuid::Uuid;

use crate::constants::MAX_MESSAGE_SIZE;
use crate::discovery::announce_coordinator;
use crate::protocol::{Message, TaskStatus};

#[derive(Debug, Clone)]
enum TaskState {
    Pending,
    Assigned { worker_id: String },
    Completed,
    Failed {
        #[allow(dead_code)]
        error: String
    },
}

#[derive(Debug, Clone)]
struct Task {
    id: Uuid,
    relative_path: String,
    state: TaskState,
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

/// Run as coordinator - distribute tasks to workers
pub async fn run_coordinator(data_dir: &Path, port: u16) -> Result<()> {
    info!("╔══════════════════════════════════════════════════════════╗");
    info!("║   Phase 3: Coordinator Mode                              ║");
    info!("╚══════════════════════════════════════════════════════════╝");

    if !data_dir.exists() {
        error!("Data directory not found: {:?}", data_dir);
        anyhow::bail!("Data directory not found.");
    }

    // Scan for subreddits
    info!("📂 Scanning for subreddit directories...");
    let subreddits = scan_subreddits(data_dir)?;
    info!("✓ Found {} subreddit directories", subreddits.len());

    // Create coordinator state
    let state = Arc::new(Mutex::new(CoordinatorState::new(subreddits, data_dir)?));

    // Start mDNS announcement
    let _mdns = announce_coordinator(port)?;

    // Start TCP listener
    let addr = format!("0.0.0.0:{}", port);
    let listener = TcpListener::bind(&addr).await?;
    info!("🚀 Coordinator listening on {}", addr);

    // Spawn periodic status and stale worker check
    let status_state = Arc::clone(&state);
    tokio::spawn(async move {
        let mut interval = tokio::time::interval(tokio::time::Duration::from_secs(30));
        loop {
            interval.tick().await;
            let mut state = status_state.lock().unwrap();
            state.check_stale_workers();
            info!("📊 {}", state.get_status());
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
