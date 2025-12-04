use anyhow::{Context, Result};
use duckdb::{Connection, params};
use log::{info, warn};
use std::collections::HashSet;
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

const CHUNK_SIZE: usize = 10_000;

/// Process a single subreddit directory
pub fn process_subreddit(
    subreddit_path: &Path,
    output_base_dir: &Path,
    data_base_dir: &Path,
) -> Result<()> {
    let subreddit_name = subreddit_path
        .file_name()
        .unwrap_or_default()
        .to_string_lossy()
        .to_string();

    info!("Processing r/{}", subreddit_name);

    // Find all parquet files for this subreddit
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
        info!("  No parquet files found, skipping");
        return Ok(());
    }

    info!("  Found {} parquet files", parquet_files.len());

    // Create an in-memory DuckDB database
    let conn = Connection::open_in_memory()
        .context("Failed to create DuckDB connection")?;

    // Create a table to hold all messages
    conn.execute(
        "CREATE TABLE messages (
            id VARCHAR,
            parent_id VARCHAR,
            link_id VARCHAR,
            body VARCHAR,
            is_idea BOOLEAN,
            subreddit VARCHAR,
            author VARCHAR,
            permalink VARCHAR,
            created_utc BIGINT,
            ups BIGINT,
            downs BIGINT,
            sanitized_prefix VARCHAR,
            cpu_filter_is_idea BOOLEAN,
            nlp_top_score DOUBLE
        )",
        [],
    ).context("Failed to create messages table")?;

    // Load ALL messages from all parquet files into DuckDB
    info!("  Loading all messages into DuckDB...");
    for file_path in &parquet_files {
        let file_path_str = file_path.to_string_lossy();
        // Explicitly select columns to avoid schema inference issues
        let sql = format!(
            "INSERT INTO messages 
             SELECT 
                id, parent_id, link_id, body, is_idea, 
                subreddit, author, permalink, created_utc, 
                ups, downs, sanitized_prefix, cpu_filter_is_idea, nlp_top_score
             FROM read_parquet('{}')",
            file_path_str
        );
        
        match conn.execute(&sql, []) {
            Ok(_) => {},
            Err(e) => {
                warn!("  Failed to load file {:?}: {}", file_path, e);
                continue;
            }
        }
    }

    // Get total count of ideas
    let idea_count: i64 = conn
        .query_row("SELECT COUNT(*) FROM messages WHERE is_idea = true", [], |row| row.get(0))
        .context("Failed to count ideas")?;

    if idea_count == 0 {
        info!("  No ideas found, skipping");
        return Ok(());
    }

    info!("  Found {} ideas to process", idea_count);

    // Process ideas in chunks and write each chunk immediately
    let num_chunks = ((idea_count as usize) + CHUNK_SIZE - 1) / CHUNK_SIZE;

    info!("  Processing {} ideas in {} chunks of {} (writing each chunk immediately)", idea_count, num_chunks, CHUNK_SIZE);

    let mut total_valid_ideas = 0;

    for chunk_idx in 0..num_chunks {
        let offset = chunk_idx * CHUNK_SIZE;
        
        // Get a chunk of idea IDs
        let mut stmt = conn.prepare(
            "SELECT id, parent_id FROM messages WHERE is_idea = true LIMIT ? OFFSET ?"
        ).context("Failed to prepare chunk query")?;

        let idea_rows = stmt
            .query_map(params![CHUNK_SIZE as i64, offset as i64], |row| {
                Ok((row.get::<_, String>(0)?, row.get::<_, Option<String>>(1)?))
            })
            .context("Failed to query chunk")?;

        let mut chunk_valid_ids: HashSet<String> = HashSet::new();

        for row in idea_rows {
            let (id, parent_id) = row.context("Failed to get row data")?;
            
            // Trace this idea's chain to see if it's complete
            if has_complete_chain(&id, &parent_id, &conn)? {
                chunk_valid_ids.insert(id);
            }
        }

        info!("    Chunk {}/{}: {} valid ideas", chunk_idx + 1, num_chunks, chunk_valid_ids.len());
        
        // Write this chunk immediately if it has any valid ideas
        if !chunk_valid_ids.is_empty() {
            write_chunk_to_parquet(
                subreddit_path,
                &conn,
                &chunk_valid_ids,
                chunk_idx,
                output_base_dir,
                data_base_dir,
            )?;
            total_valid_ideas += chunk_valid_ids.len();
        }
        
        // chunk_valid_ids is dropped here, freeing memory
    }

    if total_valid_ideas == 0 {
        info!("  No valid chains found, skipping");
        return Ok(());
    }

    info!("  Total valid ideas with complete chains: {}", total_valid_ideas);

    Ok(())
}

/// Check if a message has a complete chain to a root (parent_id = null)
/// This function looks at ALL messages (not just ideas) when tracing parents
fn has_complete_chain(
    id: &str,
    parent_id: &Option<String>,
    conn: &Connection,
) -> Result<bool> {
    let mut visited: HashSet<String> = HashSet::new();
    let mut current_id = id.to_string();
    let mut current_parent_id = parent_id.clone();

    loop {
        // Check for circular reference
        if visited.contains(&current_id) {
            return Ok(false);
        }
        visited.insert(current_id.clone());

        // Check if we've reached the root
        if current_parent_id.is_none() || current_parent_id.as_ref().map_or(false, |p| p.is_empty()) {
            return Ok(true);
        }

        // Extract the actual parent ID from the link format (e.g., "t1_abc123" -> "abc123")
        let parent_id_clean = current_parent_id.as_ref().unwrap();
        let parent_id_clean = if parent_id_clean.contains('_') {
            parent_id_clean.split('_').nth(1).unwrap_or(parent_id_clean)
        } else {
            parent_id_clean
        };

        // Look up the parent in the database (checking ALL messages, not just ideas)
        let result = conn.query_row(
            "SELECT id, parent_id FROM messages WHERE id = ?",
            params![parent_id_clean],
            |row| {
                Ok((row.get::<_, String>(0)?, row.get::<_, Option<String>>(1)?))
            },
        );

        match result {
            Ok((parent_msg_id, parent_parent_id)) => {
                // Continue tracing up the chain
                current_id = parent_msg_id;
                current_parent_id = parent_parent_id;
            }
            Err(duckdb::Error::QueryReturnedNoRows) => {
                // Parent not found, chain is broken
                return Ok(false);
            }
            Err(e) => {
                return Err(anyhow::anyhow!("Database error: {}", e));
            }
        }
    }
}

/// Write a single chunk of valid chains to an output parquet file
/// Each chunk gets its own file: chains_chunk_0.parquet, chains_chunk_1.parquet, etc.
fn write_chunk_to_parquet(
    subreddit_path: &Path,
    conn: &Connection,
    valid_ids: &HashSet<String>,
    chunk_idx: usize,
    output_base_dir: &Path,
    data_base_dir: &Path,
) -> Result<()> {
    // Extract the relative path from data_base_dir
    let relative_path = subreddit_path
        .strip_prefix(data_base_dir)
        .context("Failed to get relative path")?;

    // Create the output directory with the same structure
    let output_path = output_base_dir.join(relative_path);
    std::fs::create_dir_all(&output_path)
        .context(format!("Failed to create output directory: {:?}", output_path))?;

    let output_file = output_path.join(format!("chains_chunk_{}.parquet", chunk_idx));
    let output_file_str = output_file.to_string_lossy();

    // Build a SQL query with all valid IDs for this chunk
    // For large sets, we'll use a temporary table
    conn.execute("DROP TABLE IF EXISTS chunk_valid_ids", [])
        .context("Failed to drop temp table")?;
    
    conn.execute("CREATE TEMP TABLE chunk_valid_ids (id VARCHAR)", [])
        .context("Failed to create temp table")?;

    // Insert valid IDs in batches
    let batch_size = 1000;
    let valid_ids_vec: Vec<&String> = valid_ids.iter().collect();
    
    for chunk in valid_ids_vec.chunks(batch_size) {
        let values: Vec<String> = chunk.iter().map(|id| format!("('{}')", id)).collect();
        let values_str = values.join(",");
        let sql = format!("INSERT INTO chunk_valid_ids VALUES {}", values_str);
        conn.execute(&sql, [])
            .context("Failed to insert valid IDs")?;
    }

    // Export valid ideas to parquet
    let sql = format!(
        "COPY (SELECT m.* FROM messages m INNER JOIN chunk_valid_ids v ON m.id = v.id WHERE m.is_idea = true) 
         TO '{}' (FORMAT PARQUET, COMPRESSION ZSTD)",
        output_file_str
    );

    conn.execute(&sql, [])
        .context(format!("Failed to write parquet file: {:?}", output_file))?;

    // Get count for logging
    let count: i64 = conn.query_row(
        "SELECT COUNT(*) FROM messages m INNER JOIN chunk_valid_ids v ON m.id = v.id WHERE m.is_idea = true",
        [],
        |row| row.get(0)
    ).context("Failed to get count")?;

    info!(
        "    ✓ Wrote {} ideas from chunk {} to {:?}",
        count,
        chunk_idx,
        output_file.file_name().unwrap()
    );

    Ok(())
}

/// Count the number of chunk files in a subreddit directory
#[allow(dead_code)]
pub fn count_chunks(subreddit_path: &Path) -> Result<usize> {
    let chunk_count = WalkDir::new(subreddit_path)
        .into_iter()
        .filter_map(|e| e.ok())
        .filter(|e| {
            e.file_type().is_file()
            && e.file_name()
                .to_string_lossy()
                .starts_with("chains_chunk_")
            && e.path().extension().map_or(false, |ext| ext == "parquet")
        })
        .count();
    
    Ok(chunk_count)
}
