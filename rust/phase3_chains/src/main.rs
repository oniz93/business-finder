mod coordinator;
mod discovery;
mod processing;
mod protocol;
mod standalone;
mod worker;

use anyhow::Result;
use clap::{Parser, ValueEnum};
use std::path::PathBuf;

// Default configuration constants for backward compatibility
const DEFAULT_DATA_DIR: &str = "/Volumes/2TBSSD/reddit/processed";
const DEFAULT_OUTPUT_DIR: &str = "/Volumes/2TBSSD/reddit/chains";
const DEFAULT_COORDINATOR_PORT: u16 = 5000;

#[derive(Debug, Clone, ValueEnum)]
enum Mode {
    Standalone,
    Coordinator,
    Worker,
}

#[derive(Parser, Debug)]
#[command(name = "phase3_chains")]
#[command(about = "Build complete conversation chains from ideas", long_about = None)]
struct Args {
    /// Operating mode: standalone (default), coordinator, or worker
    #[arg(long, value_enum, default_value = "standalone")]
    mode: Mode,

    /// Data directory (processed parquet files)
    #[arg(long, default_value = DEFAULT_DATA_DIR)]
    data_dir: PathBuf,

    /// Output directory (chains output)
    #[arg(long, default_value = DEFAULT_OUTPUT_DIR)]
    output_dir: PathBuf,

    /// Process only a specific subreddit (standalone mode only)
    #[arg(long)]
    subreddit: Option<String>,

    /// Coordinator address (worker mode, optional if using mDNS)
    #[arg(long)]
    coordinator_addr: Option<String>,

    /// Local cache directory for worker temp files
    #[arg(long)]
    local_cache_dir: Option<PathBuf>,

    /// Worker ID (worker mode, auto-generated if not provided)
    #[arg(long)]
    worker_id: Option<String>,

    /// Port for coordinator to listen on
    #[arg(long, default_value_t = DEFAULT_COORDINATOR_PORT)]
    port: u16,
}

#[tokio::main]
async fn main() -> Result<()> {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();
    
    let args = Args::parse();

    match args.mode {
        Mode::Standalone => {
            standalone::run_standalone(&args.data_dir, &args.output_dir, args.subreddit)
        }
        Mode::Coordinator => {
            coordinator::run_coordinator(&args.data_dir, args.port).await
        }
        Mode::Worker => {
            let worker_id = args.worker_id.unwrap_or_else(|| {
                use uuid::Uuid;
                format!("worker-{}", Uuid::new_v4())
            });

            let config = worker::WorkerConfig {
                worker_id,
                coordinator_addr: args.coordinator_addr,
                data_dir: args.data_dir,
                output_dir: args.output_dir,
                local_cache_dir: args.local_cache_dir,
            };

            worker::run_worker(config).await
        }
    }
}
