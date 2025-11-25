// Directory Paths
pub const RAW_DATA_DIRS: &[&str] = &[
    "/Volumes/2TBSSD/reddit/raw",
    "/Volumes/256GB/raw",
    "/Volumes/SSD256/raw",
];
pub const PROCESSED_DATA_DIR: &str = "/Volumes/2TBSSD/reddit/processed";
pub const INTERMEDIATE_DATA_DIR: &str = "/Volumes/2TBSSD/reddit/intermediate";
pub const CHECKPOINT_DIR: &str = "/Volumes/2TBSSD/reddit/intermediate/checkpoints";

// State Files
pub const STATE_FILE_NAME: &str = "processing_state.json";
pub const RESUME_STATE_FILE_NAME: &str = "restore_state.json";

// Phase 1 Settings
pub const RAW_CHUNK_SIZE: usize = 400_000; // Lines to read from raw text
pub const NUM_PHASE1_WORKERS: usize = 4;
pub const CHECKPOINT_INTERVAL: u64 = 100_000; // How often to sample
pub const CHECKPOINT_CHUNK_SIZE: usize = 10; // How many lines to sample
pub const RESTORE_SCAN_CHUNK_SIZE: usize = 2000; // For fine-grained scanning after finding a block

// Phase 2 Settings
pub const NUM_PHASE2_WORKERS: usize = 8;
pub const PHASE2_CHUNK_SIZE: usize = 1_000_000;

// Phase 3 Settings
pub const FINAL_FILE_ROW_LIMIT: usize = 1_000_000; // Rows per final parquet file
