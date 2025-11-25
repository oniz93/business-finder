use std::collections::HashMap;
use std::fs::{self, File};
use std::io::{BufReader, BufWriter};
use std::path::{Path, PathBuf};

use anyhow::{Context, Result};
use dashmap::DashMap;

use crate::constants::{CHECKPOINT_DIR, PROCESSED_DATA_DIR, RESUME_STATE_FILE_NAME, STATE_FILE_NAME};
use crate::types::{FileProcessState, ProcessingState, RestoreState};

// --- State Management ---

pub fn state_file_path() -> PathBuf {
    Path::new(PROCESSED_DATA_DIR).join(STATE_FILE_NAME)
}

pub fn load_state() -> Result<ProcessingState> {
    let path = state_file_path();
    if !path.exists() {
        return Ok(DashMap::new());
    }
    let file = File::open(path).context("Failed to open state file")?;
    let reader = BufReader::new(file);
    let state: HashMap<PathBuf, FileProcessState> =
        serde_json::from_reader(reader).context("Failed to deserialize state")?;
    Ok(state.into_iter().collect())
}

pub fn save_state(state: &ProcessingState) -> Result<()> {
    let path = state_file_path();
    let file = File::create(path).context("Failed to create state file for writing")?;
    let writer = BufWriter::new(file);
    let state_hashmap: HashMap<_, _> = state
        .iter()
        .map(|entry| (entry.key().clone(), entry.value().clone()))
        .collect();
    serde_json::to_writer_pretty(writer, &state_hashmap)
        .context("Failed to serialize and write state")?;
    Ok(())
}

// --- Restore State Management ---

pub fn restore_state_path() -> PathBuf {
    Path::new(CHECKPOINT_DIR).join(RESUME_STATE_FILE_NAME)
}

pub fn load_restore_state() -> Result<RestoreState> {
    let path = restore_state_path();
    if !path.exists() {
        return Ok(RestoreState::default());
    }
    let file = File::open(path)?;
    let reader = BufReader::new(file);
    let state: HashMap<PathBuf, bool> = serde_json::from_reader(reader)?;
    Ok(RestoreState {
        checkpoints_generated: state.into_iter().collect(),
    })
}

pub fn save_restore_state(state: &RestoreState) -> Result<()> {
    fs::create_dir_all(CHECKPOINT_DIR)?;
    let path = restore_state_path();
    let file = File::create(path)?;
    let writer = BufWriter::new(file);
    let state_hashmap: HashMap<_, _> = state
        .checkpoints_generated
        .iter()
        .map(|e| (e.key().clone(), *e.value()))
        .collect();
    serde_json::to_writer_pretty(writer, &state_hashmap)?;
    Ok(())
}
