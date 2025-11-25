use std::fs::File;
use std::io::{self, BufRead, BufReader};
use std::path::PathBuf;

use anyhow::Result;
use walkdir::WalkDir;
use zstd::stream::read::Decoder;

use crate::types::{FileInfo, FileStatus, ProcessingState};

/// Sanitize a subreddit name to a 2-character prefix
pub fn sanitize_prefix(s: &str) -> String {
    let prefix = s.chars().take(2).collect::<String>();
    prefix
        .chars()
        .filter(|c| c.is_alphanumeric() || *c == '_')
        .collect::<String>()
        .to_lowercase()
}

/// Discover raw files to process
pub fn discover_files(base_dirs: &[&str], state: &ProcessingState) -> Result<Vec<FileInfo>> {
    let mut all_files = Vec::new();
    for base_dir in base_dirs {
        let root = PathBuf::from(base_dir);
        if !root.exists() {
            continue;
        }

        for entry in WalkDir::new(root)
            .into_iter()
            .filter_map(|e| e.ok())
            .filter(|e| e.file_type().is_file())
        {
            let path = entry.path();
            if let Some(s) = state.get(path) {
                if s.status == FileStatus::Completed {
                    continue;
                }
            }

            let file_name = match path.file_name().and_then(|s| s.to_str()) {
                Some(s) => s,
                None => continue,
            };

            let file_type = if file_name.starts_with("RS") {
                "submission".to_string()
            } else if file_name.starts_with("RC") {
                "comment".to_string()
            } else {
                continue;
            };
            
            if file_name.ends_with(".zst") || file_name.ends_with(".jsonl") {
                all_files.push(FileInfo {
                    path: path.to_path_buf(),
                    file_type,
                });
            }
        }
    }
    all_files.sort_by(|a, b| a.path.cmp(&b.path));
    Ok(all_files)
}

/// Stream lines from a file (handles both .zst and plain text)
pub fn stream_lines(
    file_info: &FileInfo,
) -> Result<Box<dyn Iterator<Item = io::Result<String>>>> {
    let file = File::open(&file_info.path)?;
    let reader = BufReader::new(file);
    if file_info.path.extension().and_then(|s| s.to_str()) == Some("zst") {
        let decoder = Decoder::new(reader)?;
        let zstd_reader = BufReader::new(decoder);
        Ok(Box::new(zstd_reader.lines()))
    } else {
        Ok(Box::new(reader.lines()))
    }
}
