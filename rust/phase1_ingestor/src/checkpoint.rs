use std::collections::HashMap;
use std::fs::{self, File};
use std::io::{BufReader, BufWriter};
use std::path::{Path, PathBuf};

use anyhow::{anyhow, Context, Result};
use duckdb::{Connection, Result as DuckDBResult};
use glob::glob;
use log::{info, warn};

use crate::constants::{
    CHECKPOINT_CHUNK_SIZE, CHECKPOINT_DIR, CHECKPOINT_INTERVAL, INTERMEDIATE_DATA_DIR,
    RESTORE_SCAN_CHUNK_SIZE,
};
use crate::types::{CheckpointData, CheckpointEntry, FileInfo, JsonLineForCheckpoint, Checkpoint};
use crate::utils::{sanitize_prefix, stream_lines};

// --- Checkpoint File Path Helpers ---

pub fn checkpoint_file_path(file_info: &FileInfo) -> Result<PathBuf> {
    let file_name = file_info
        .path
        .file_name()
        .and_then(|s| s.to_str())
        .ok_or_else(|| anyhow!("Could not get file name"))?;
    Ok(Path::new(CHECKPOINT_DIR).join(format!("{}.checkpoints.json", file_name)))
}

pub fn load_checkpoint_data(file_info: &FileInfo) -> Result<Option<CheckpointData>> {
    let path = checkpoint_file_path(file_info)?;
    if !path.exists() {
        return Ok(None);
    }
    let file = File::open(path)?;
    let reader = BufReader::new(file);
    let data = serde_json::from_reader(reader)?;
    Ok(Some(data))
}

// --- Checkpoint Generation ---

pub fn generate_checkpoints(file_info: &FileInfo) -> Result<CheckpointData> {
    info!(
        "Generating checkpoints for {:?}...",
        file_info.path.file_name().unwrap()
    );
    let mut checkpoints = Vec::new();
    let mut total_lines: u64 = 0;
    let mut sample_buffer = Vec::with_capacity(CHECKPOINT_CHUNK_SIZE);

    for (i, line_result) in stream_lines(file_info)?.enumerate() {
        let current_line_num = i as u64 + 1;
        total_lines = current_line_num;

        if (current_line_num > 0) && ((current_line_num - 1) % CHECKPOINT_INTERVAL == 0) {
            sample_buffer.clear();
        }

        if sample_buffer.len() < CHECKPOINT_CHUNK_SIZE {
            let line = line_result.with_context(|| {
                format!(
                    "Error reading line {} from {:?}",
                    current_line_num, file_info.path
                )
            })?;
            sample_buffer.push(line);

            if sample_buffer.len() == CHECKPOINT_CHUNK_SIZE {
                let entries = sample_buffer
                    .iter()
                    .filter_map(|l| serde_json::from_str::<JsonLineForCheckpoint>(l).ok())
                    .map(|j| CheckpointEntry {
                        id: j.id.clone(),
                        sanitized_prefix: sanitize_prefix(&j.subreddit),
                    })
                    .collect::<Vec<_>>();

                if entries.len() == CHECKPOINT_CHUNK_SIZE {
                    checkpoints.push(Checkpoint {
                        line_number: current_line_num - (CHECKPOINT_CHUNK_SIZE as u64 - 1),
                        entries,
                    });
                }
            }
        }
    }

    let data = CheckpointData {
        total_lines,
        checkpoints,
    };

    fs::create_dir_all(CHECKPOINT_DIR).context("Failed to create checkpoint dir")?;
    let path = checkpoint_file_path(file_info)?;
    let temp_path = path.with_extension("checkpoints.json.tmp");

    let file = File::create(&temp_path)
        .context(format!("Failed to create temp file at {:?}", temp_path))?;
    let writer = BufWriter::new(file);
    serde_json::to_writer_pretty(writer, &data).context("Failed to write checkpoint data")?;
    fs::rename(&temp_path, &path)
        .context(format!("Failed to rename checkpoint file to {:?}", path))?;

    info!(
        "Finished checkpoints for {:?}. Total lines: {}",
        file_info.path.file_name().unwrap(),
        total_lines
    );
    Ok(data)
}

// --- Resume Point Detection ---

pub fn find_resume_point(file_info: &FileInfo, checkpoint_data: &CheckpointData) -> Result<u64> {
    let checkpoints = &checkpoint_data.checkpoints;
    if checkpoints.is_empty() {
        info!("No checkpoints found, file is small. Scanning from beginning.");
        return scan_block_for_resume_point(file_info, 0, checkpoint_data.total_lines);
    }

    let n = checkpoints.len();
    info!("Verifying file using {} checkpoints.", n);

    // 1. Check the first checkpoint
    info!(
        "Checking first checkpoint (line {})...",
        checkpoints[0].line_number
    );
    let first_status = check_ids_status(&checkpoints[0].entries)?;
    if first_status == 0 {
        info!("First checkpoint is not processed. Assuming file is unprocessed. Resume point is 0.");
        return Ok(0);
    }

    // 2. Check the last checkpoint
    info!(
        "Checking last checkpoint (line {})...",
        checkpoints[n - 1].line_number
    );
    let last_status = check_ids_status(&checkpoints[n - 1].entries)?;
    if last_status > 0 {
        info!("Last checkpoint has been at least partially processed. Assuming file is complete or near complete.");
        return Ok(checkpoint_data.total_lines);
    }

    // 3. If last checkpoint has no rows, perform binary search on the rest
    info!("Last checkpoint is unprocessed. Performing binary search on middle checkpoints...");
    let mut low = 0; // First block is known to be at least partially processed
    let mut high = n - 2; // Last block is known to be unprocessed
    let mut last_fully_processed_idx: i64 = -1;

    while low <= high {
        let mid = low + (high - low) / 2;
        info!(
            "  Binary search: checking checkpoint #{} (line {})...",
            mid, checkpoints[mid].line_number
        );
        let status = check_ids_status(&checkpoints[mid].entries)?;

        if status == 2 {
            info!("  Checkpoint #{} is fully processed.", mid);
            last_fully_processed_idx = mid as i64;
            low = mid + 1;
        } else {
            info!(
                "  Checkpoint #{} is not fully processed (status: {}).",
                mid, status
            );
            if mid == 0 {
                break;
            }
            high = mid - 1;
        }
    }

    // --- Determine the fine-grained search range ---
    let search_start_line = if last_fully_processed_idx == -1 {
        info!("No fully processed checkpoints found in the middle. Starting scan from line 0.");
        0
    } else {
        info!(
            "Last fully processed checkpoint is #{}. Starting scan from its block.",
            last_fully_processed_idx
        );
        checkpoints[last_fully_processed_idx as usize].line_number - 1
    };

    let search_end_line = if (last_fully_processed_idx as usize) < checkpoints.len() - 1 {
        checkpoints[(last_fully_processed_idx + 1) as usize].line_number - 1
    } else {
        checkpoint_data.total_lines
    };

    info!(
        "Checkpoints indicate resume point is between lines {} and {}. Starting detailed scan.",
        search_start_line, search_end_line
    );

    scan_block_for_resume_point(file_info, search_start_line, search_end_line)
}

pub fn scan_block_for_resume_point(
    file_info: &FileInfo,
    start_line: u64,
    end_line: u64,
) -> Result<u64> {
    if start_line >= end_line {
        return Ok(start_line);
    }

    let mut current_pos = start_line;

    loop {
        let remaining_lines = end_line - current_pos;
        if remaining_lines == 0 {
            break;
        }
        let chunk_size = std::cmp::min(remaining_lines, RESTORE_SCAN_CHUNK_SIZE as u64);
        info!(
            "  Scanning lines {} to {}...",
            current_pos,
            current_pos + chunk_size
        );

        let mut checkpoint_entries = Vec::new();

        let line_iterator = stream_lines(file_info)?
            .skip(current_pos as usize)
            .take(chunk_size as usize);

        for (_, line_result) in line_iterator.enumerate() {
            let line = line_result?;
            if let Ok(json) = serde_json::from_str::<JsonLineForCheckpoint>(&line) {
                checkpoint_entries.push(CheckpointEntry {
                    id: json.id,
                    sanitized_prefix: sanitize_prefix(&json.subreddit),
                });
            }
        }

        if checkpoint_entries.is_empty() {
            info!("  No processable lines in this chunk.");
            current_pos += chunk_size;
            continue;
        }

        let found_ids_map = get_found_ids_map(checkpoint_entries.clone())?;

        if let Some((last_index, _)) = checkpoint_entries
            .iter()
            .enumerate()
            .rev()
            .find(|(_, entry)| found_ids_map.contains_key(&entry.id))
        {
            let last_line_num = current_pos + last_index as u64;
            let resume_point = last_line_num + 1;
            info!(
                "  Found last processed line in chunk at: {}. Advancing scan to {}",
                last_line_num, resume_point
            );
            current_pos = resume_point;
        } else {
            info!(
                "  No processed items found in this chunk. Resume point is at {}",
                current_pos
            );
            return Ok(current_pos);
        }
    }

    Ok(current_pos)
}

/// Checks a list of IDs against the database and returns a status.
/// 0 = None found, 1 = Some found (partial), 2 = All found
pub fn check_ids_status(entries: &[CheckpointEntry]) -> Result<u8> {
    if entries.is_empty() {
        return Ok(0);
    }
    let found_ids = get_found_ids_map(entries.to_vec())?;
    if found_ids.is_empty() {
        Ok(0) // None
    } else if found_ids.len() == entries.len() {
        Ok(2) // All
    } else {
        Ok(1) // Partial
    }
}

/// Queries DuckDB for a list of IDs and returns a HashMap of the ones that were found.
pub fn get_found_ids_map(entries: Vec<CheckpointEntry>) -> Result<HashMap<String, bool>> {
    if entries.is_empty() {
        return Ok(HashMap::new());
    }

    let mut grouped_by_prefix: HashMap<String, Vec<String>> = HashMap::new();
    for entry in entries {
        grouped_by_prefix
            .entry(entry.sanitized_prefix)
            .or_default()
            .push(entry.id);
    }

    let conn = Connection::open_in_memory()?;
    conn.execute("INSTALL httpfs; LOAD httpfs;", [])?;
    conn.execute("SET enable_object_cache=true;", [])?;

    let mut final_found_map = HashMap::new();

    for (prefix, ids) in grouped_by_prefix {
        let parquet_glob = Path::new(INTERMEDIATE_DATA_DIR)
            .join(&prefix)
            .join("*.parquet");
        let parquet_path_str = parquet_glob.to_str().unwrap();

        if let Ok(paths) = glob(parquet_path_str) {
            if paths.count() == 0 {
                continue;
            }
        }

        let id_list = ids
            .iter()
            .map(|id| format!("'{}'", id.replace('`', "''")))
            .collect::<Vec<_>>()
            .join(",");

        let query = format!(
            "SELECT id FROM read_parquet('{}', union_by_name = true) WHERE id IN ({})",
            parquet_path_str, id_list
        );

        let mut stmt = match conn.prepare(&query) {
            Ok(s) => s,
            Err(e) => {
                warn!("Could not prepare query for prefix '{}': {}. This can happen if no files have been written for this prefix yet.", prefix, e);
                continue;
            }
        };

        let found_ids_iter = match stmt.query_map([], |row| row.get(0)) {
            Ok(iter) => iter,
            Err(e) => {
                warn!("Could not execute query for prefix '{}': {}. This can happen if no files have been written for this prefix yet.", prefix, e);
                continue;
            }
        };

        let found_ids: Vec<String> = found_ids_iter.collect::<DuckDBResult<Vec<String>>>()?;

        for id in found_ids {
            final_found_map.insert(id, true);
        }
    }

    Ok(final_found_map)
}
