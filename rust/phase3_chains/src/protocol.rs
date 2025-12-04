use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Messages exchanged between coordinator and workers
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Message {
    /// Worker requests a task from the coordinator
    RequestTask { worker_id: String },
    
    /// Coordinator assigns a task to a worker
    AssignTask {
        task_id: Uuid,
        relative_path: String,
    },
    
    /// Worker reports task completion
    TaskComplete {
        task_id: Uuid,
        status: TaskStatus,
    },
    
    /// Keep-alive message from worker
    Heartbeat { worker_id: String },
    
    /// Coordinator indicates no tasks are available
    NoTasksAvailable,
}

/// Status of a completed task
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TaskStatus {
    Success,
    Failed { error: String },
}

impl Message {
    /// Serialize message to bytes using bincode
    pub fn to_bytes(&self) -> anyhow::Result<Vec<u8>> {
        Ok(bincode::serialize(self)?)
    }
    
    /// Deserialize message from bytes using bincode
    pub fn from_bytes(bytes: &[u8]) -> anyhow::Result<Self> {
        Ok(bincode::deserialize(bytes)?)
    }
}
