use std::fs;

use anyhow::{Context, Result};
use clap::Parser;
use log::info;

use phase1_ingestor::{run_phase_1, run_phase_2, Cli, INTERMEDIATE_DATA_DIR, PROCESSED_DATA_DIR};


// --- Main Orchestration ---
fn main() -> Result<()> {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();
    let cli = Cli::parse();

    // --- PHASE 1: Ingestion ---
    if !cli.skip_phase1 {
        info!("=== STARTING PHASE 1: Ingestion to Intermediate ===");
        fs::create_dir_all(INTERMEDIATE_DATA_DIR).context("Failed to create intermediate dir")?;
        run_phase_1(cli.restore, cli.only_check_files, cli.exclude_check_files)?;
        info!("=== PHASE 1 COMPLETE ===");
    } else {
        info!("=== SKIPPING PHASE 1 (--skip-phase1 flag set) ===");
    }

    // --- PHASE 2: Partitioning ---
    info!("=== STARTING PHASE 2: Partitioning by Subreddit ===");
    fs::create_dir_all(PROCESSED_DATA_DIR).context("Failed to create processed dir")?;
    run_phase_2()?;
    info!("=== PHASE 2 COMPLETE ===");

    Ok(())
}