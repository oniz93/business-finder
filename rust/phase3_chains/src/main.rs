use anyhow::{Context, Result};
use clap::Parser;
use duckdb::{Connection, params};
use log::{info, warn, error};
use walkdir::WalkDir;
use std::path::PathBuf;
use std::collections::HashSet;
use indicatif::{ProgressBar, ProgressStyle};
use serde::{Serialize, Deserialize};
use sysinfo::{System, RefreshKind, MemoryRefreshKind};

// Configuration constants
const PROCESSED_DATA_DIR: &str = "/Volumes/2TBSSD/reddit/processed";
const CHAINS_OUTPUT_DIR: &str = "/Volumes/2TBSSD/reddit/chains";
const CHECKPOINT_DIR: &str = "/Users/teomiscia/web/business-finder/rust/checkpoint";
const CHECKPOINT_FILE: &str = "phase3_progress.json";
const SUBREDDITS_LIST_FILE: &str = "subreddits_list.json";
const CHUNK_SIZE: usize = 10_000;

#[derive(Parser, Debug)]
#[command(name = "phase3_chains")]
#[command(about = "Build complete conversation chains from ideas", long_about = None)]
struct Args {
    /// Process only a specific subreddit (e.g., "AskReddit")
    /// When specified, will process only this subreddit and skip checkpoint/scanning
    #[arg(long)]
    subreddit: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
struct Progress {
    subreddit_index: usize,
}



fn save_progress(progress: &Progress) -> Result<()> {
    std::fs::create_dir_all(CHECKPOINT_DIR).context("Failed to create checkpoint directory")?;
    let path = PathBuf::from(CHECKPOINT_DIR).join(CHECKPOINT_FILE);
    let f = std::fs::File::create(&path).context("Failed to create progress file")?;
    serde_json::to_writer_pretty(f, progress).context("Failed to write progress")?;
    Ok(())
}

fn load_progress() -> Result<Progress> {
    let path = PathBuf::from(CHECKPOINT_DIR).join(CHECKPOINT_FILE);
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

fn main() -> Result<()> {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();
    
    let args = Args::parse();
    
    info!("╔══════════════════════════════════════════════════════════╗");
    info!("║   Phase 3: Building Message Chains from Ideas           ║");
    info!("╚══════════════════════════════════════════════════════════╝");
    
    let processed_data_path = PathBuf::from(PROCESSED_DATA_DIR);
    if !processed_data_path.exists() {
        error!("Processed data directory not found: {:?}", processed_data_path);
        anyhow::bail!("Processed data directory not found.");
    }

    // Create output directory
    std::fs::create_dir_all(CHAINS_OUTPUT_DIR)
        .context("Failed to create chains output directory")?;

    // Handle single subreddit mode
    if let Some(subreddit_name) = args.subreddit {
        info!("🎯 Single subreddit mode: {}", subreddit_name);
        
        // Find the subreddit path
        let subreddit_path = find_subreddit_path(&processed_data_path, &subreddit_name)?;
        
        info!("Found subreddit at: {:?}", subreddit_path);
        
        // Process this single subreddit
        process_subreddit(&subreddit_path)?;
        
        info!("╔══════════════════════════════════════════════════════════╗");
        info!("║   Phase 3: Complete (Single Subreddit)!                 ║");
        info!("╚══════════════════════════════════════════════════════════╝");
        
        return Ok(());
    }

    // Scan for all subreddit directories or load from cache
    let subreddits = if let Some(cached_list) = load_subreddits_list()? {
        info!("✓ Using cached list of {} subreddits", cached_list.len());
        cached_list
    } else {
        info!("📂 Scanning for subreddit directories...");
        let list = scan_subreddits(&processed_data_path)?;
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

    // Process each subreddit sequentially (with checkpoint support)
    for i in progress.subreddit_index..total_subreddits {
        // Update progress index
        progress.subreddit_index = i;
        save_progress(&progress)?;

        let subreddit_path = &subreddits[i];
        
        let subreddit_name = subreddit_path
            .file_name()
            .unwrap_or_default()
            .to_string_lossy()
            .to_string();
        
        main_pb.set_message(format!("Processing r/{}", subreddit_name));
        
        match process_subreddit(subreddit_path) {
            Ok(()) => {},
            Err(e) => {
                error!("Error processing subreddit {:?}: {}", subreddit_path, e);
                // Continue to next subreddit instead of crashing
            }
        }

        main_pb.inc(1);
    }

    // Mark as fully done
    progress.subreddit_index = total_subreddits;
    save_progress(&progress)?;

    main_pb.finish_with_message("✓ Completed all subreddits");

    info!("╔══════════════════════════════════════════════════════════╗");
    info!("║   Phase 3: Complete!                                     ║");
    info!("╚══════════════════════════════════════════════════════════╝");

    Ok(())
}

/// Find a specific subreddit path by name
fn find_subreddit_path(base_path: &PathBuf, subreddit_name: &str) -> Result<PathBuf> {
    // First, get all suffix directories (01, 02, etc.)
    let suffix_dirs: Vec<PathBuf> = std::fs::read_dir(base_path)?
        .filter_map(|e| e.ok().map(|e| e.path()))
        .filter(|p| p.is_dir())
        .collect();
    
    for suffix_dir in suffix_dirs {
        let potential_path = suffix_dir.join(subreddit_name);
        if potential_path.exists() && potential_path.is_dir() {
            return Ok(potential_path);
        }
    }
    
    anyhow::bail!("Subreddit '{}' not found in any suffix directory", subreddit_name);
}

/// Scan for all subreddit directories in the processed data directory
/// Uses the same dynamic scanning logic as phase2_orchestrator
fn scan_subreddits(base_path: &PathBuf) -> Result<Vec<PathBuf>> {
    // First, get all suffix directories (01, 02, etc.)
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
    list.sort(); // Crucial for deterministic ordering
    info!("Sorted.");
    
    Ok(list)
}

/// Process a single subreddit directory
fn process_subreddit(subreddit_path: &PathBuf) -> Result<()> {
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

    // Set memory limit to 90% of system RAM
    let mut sys = System::new_with_specifics(
        RefreshKind::new().with_memory(MemoryRefreshKind::everything())
    );
    sys.refresh_memory();
    let total_mem = sys.total_memory();
    let memory_limit = (total_mem as f64 * 0.9) as u64;
    let memory_limit_gb = memory_limit as f64 / 1024.0 / 1024.0 / 1024.0;
    
    // info!("  System memory: {} bytes. Setting DuckDB memory limit to {:.2} GB", total_mem, memory_limit_gb);
    
    conn.execute(&format!("PRAGMA memory_limit='{}B'", memory_limit), [])
        .context("Failed to set memory limit")?;

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

    // Create an index on 'id' to speed up chain traversal
    info!("  Creating index on message IDs...");
    conn.execute("CREATE INDEX idx_messages_id ON messages(id)", [])
        .context("Failed to create index on id")?;

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
            write_chunk_to_parquet(subreddit_path, &conn, &chunk_valid_ids, chunk_idx)?;
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
    subreddit_path: &PathBuf,
    conn: &Connection,
    valid_ids: &HashSet<String>,
    chunk_idx: usize,
) -> Result<()> {
    // Extract the relative path from PROCESSED_DATA_DIR
    let relative_path = subreddit_path
        .strip_prefix(PROCESSED_DATA_DIR)
        .context("Failed to get relative path")?;

    // Create the output directory with the same structure
    let output_path = PathBuf::from(CHAINS_OUTPUT_DIR).join(relative_path);
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
