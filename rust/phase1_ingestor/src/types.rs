use std::path::PathBuf;
use serde::{Deserialize, Serialize};
use dashmap::DashMap;
use clap::Parser;

// CLI Arguments
#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
pub struct Cli {
    /// Restore from the last known state, verifying progress
    #[arg(short, long)]
    pub restore: bool,

    /// Only check these specific files during restore (space-separated list of file names)
    #[arg(long, value_delimiter = ' ')]
    pub only_check_files: Option<Vec<String>>,

    /// Exclude these files from checking during restore (space-separated list of file names)
    #[arg(long, value_delimiter = ' ')]
    pub exclude_check_files: Option<Vec<String>>,
    
    /// Skip Phase 1 (ingestion) and start directly with Phase 2 (partitioning)
    #[arg(long)]
    pub skip_phase1: bool,
}

// File Information
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FileInfo {
    pub path: PathBuf,
    pub file_type: String,
}

// File Processing Status
#[derive(Serialize, Deserialize, Debug, Clone, Copy, PartialEq)]
pub enum FileStatus {
    InProgress,
    Completed,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct FileProcessState {
    pub status: FileStatus,
    pub lines_processed: u64,
}

// Checkpoint Structures
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct JsonLineForCheckpoint {
    pub id: String,
    pub subreddit: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct CheckpointEntry {
    pub id: String,
    pub sanitized_prefix: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Checkpoint {
    pub line_number: u64,
    pub entries: Vec<CheckpointEntry>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct CheckpointData {
    pub total_lines: u64,
    pub checkpoints: Vec<Checkpoint>,
}

// Restore State
#[derive(Serialize, Deserialize, Debug, Clone, Default)]
pub struct RestoreState {
    pub checkpoints_generated: DashMap<PathBuf, bool>,
}

// Type Aliases
pub type ProcessingState = DashMap<PathBuf, FileProcessState>;
