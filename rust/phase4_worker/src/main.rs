use anyhow::{Context, Result};
use log::{info, warn, error};
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::Arc;
use serde::{Serialize, Deserialize};
use redis::Commands;
use polars::prelude::*;
use ndarray::Array2;
use tokenizers::Tokenizer;
use ort::session::{Session, builder::{GraphOptimizationLevel, SessionBuilder}};
use ort::value::Value;
use indicatif::{ProgressBar, ProgressStyle};

// Configuration constants
const MODEL_DIR: &str = "/Users/teomiscia/web/business-finder/models/onnx/minilm";
const EMBEDDING_DIM: usize = 384;  // all-MiniLM-L6-v2 produces 384-dim embeddings
const BATCH_SIZE: usize = 32;

// Redis configuration
const REDIS_URL: &str = "redis://:kRoGWJXNK75zMIcJz4RDDhNhz1hfKq6OLAzCaCFPVIw%3D@businessfinder.canadacentral.redis.azure.net:10000/";
const REDIS_PHASE4_QUEUE: &str = "phase4_todo_queue";
const REDIS_TIMEOUT_SECS: f64 = 5.0;

/// Job struct received from Redis
#[derive(Debug, Serialize, Deserialize, Clone)]
struct EmbeddingJob {
    input_path: String,
    output_path: String,
}

/// Mean pooling of token embeddings with attention mask
fn mean_pooling(
    token_embeddings: &[f32],
    attention_mask: &[i64],
    seq_len: usize,
    hidden_dim: usize,
) -> Vec<f32> {
    let mut sum = vec![0.0f32; hidden_dim];
    let mut count = 0.0f32;
    
    for i in 0..seq_len {
        if attention_mask[i] == 1 {
            for j in 0..hidden_dim {
                sum[j] += token_embeddings[i * hidden_dim + j];
            }
            count += 1.0;
        }
    }
    
    if count > 0.0 {
        for j in 0..hidden_dim {
            sum[j] /= count;
        }
    }
    
    // L2 normalize
    let norm: f32 = sum.iter().map(|x| x * x).sum::<f32>().sqrt();
    if norm > 0.0 {
        for j in 0..hidden_dim {
            sum[j] /= norm;
        }
    }
    
    sum
}

/// Embedding worker that processes jobs from Redis
struct EmbeddingWorker {
    session: Session,
    tokenizer: Tokenizer,
    redis_conn: redis::Connection,
    running: Arc<AtomicBool>,
    jobs_processed: Arc<AtomicU64>,
}

impl EmbeddingWorker {
    fn new(running: Arc<AtomicBool>, jobs_processed: Arc<AtomicU64>) -> Result<Self> {
        info!("Loading ONNX model from {:?}...", MODEL_DIR);
        
        let model_path = PathBuf::from(MODEL_DIR).join("model.onnx");
        let tokenizer_path = PathBuf::from(MODEL_DIR).join("tokenizer.json");
        
        // Verify files exist
        if !model_path.exists() {
            anyhow::bail!("Model file not found: {:?}. Run the export script first.", model_path);
        }
        if !tokenizer_path.exists() {
            anyhow::bail!("Tokenizer file not found: {:?}", tokenizer_path);
        }
        
        // Load tokenizer
        let mut tokenizer = Tokenizer::from_file(&tokenizer_path)
            .map_err(|e| anyhow::anyhow!("Failed to load tokenizer: {}", e))?;
        
        // Configure truncation and padding
        tokenizer.with_truncation(Some(tokenizers::utils::truncation::TruncationParams {
            max_length: 512,
            strategy: tokenizers::utils::truncation::TruncationStrategy::LongestFirst,
            ..Default::default()
        })).map_err(|e| anyhow::anyhow!("Failed to set truncation: {}", e))?;

        tokenizer.with_padding(Some(tokenizers::utils::padding::PaddingParams {
            strategy: tokenizers::utils::padding::PaddingStrategy::BatchLongest,
            pad_to_multiple_of: None,
            ..Default::default()
        }));
        
        info!("✓ Loaded tokenizer");
        
        // Load ONNX model with optimization
        let session = SessionBuilder::new()
            .context("Failed to create ONNX session builder")?
            .with_optimization_level(GraphOptimizationLevel::Level3)
            .context("Failed to set optimization level")?
            .with_intra_threads(4)
            .context("Failed to set intra threads")?
            .commit_from_file(&model_path)
            .context("Failed to load ONNX model")?;
        
        info!("✓ Loaded ONNX model");
        
        // Connect to Redis
        let redis_client = redis::Client::open(REDIS_URL)
            .context("Failed to create Redis client")?;
        
        let redis_conn = redis_client.get_connection()
            .context("Failed to get Redis connection")?;
        
        info!("✓ Connected to Redis");
        
        Ok(Self {
            session,
            tokenizer,
            redis_conn,
            running,
            jobs_processed,
        })
    }
    
    /// Embed a batch of texts
    fn embed_batch(&mut self, texts: &[String]) -> Result<Vec<Vec<f32>>> {
        if texts.is_empty() {
            return Ok(vec![]);
        }
        
        let batch_size = texts.len();
        
        // Tokenize all texts
        let encodings = self.tokenizer.encode_batch(texts.to_vec(), true)
            .map_err(|e| anyhow::anyhow!("Tokenization failed: {}", e))?;
        
        let max_len = encodings.iter().map(|e| e.get_ids().len()).max().unwrap_or(128);
        
        // Build padded input tensors
        let mut padded_input_ids = Array2::<i64>::zeros((batch_size, max_len));
        let mut padded_attention_mask = Array2::<i64>::zeros((batch_size, max_len));
        let mut padded_token_type_ids = Array2::<i64>::zeros((batch_size, max_len));
        
        for (i, encoding) in encodings.iter().enumerate() {
            let ids = encoding.get_ids();
            let mask = encoding.get_attention_mask();
            let ttids = encoding.get_type_ids();
            
            for (j, &id) in ids.iter().enumerate() {
                padded_input_ids[[i, j]] = id as i64;
            }
            for (j, &m) in mask.iter().enumerate() {
                padded_attention_mask[[i, j]] = m as i64;
            }
            for (j, &t) in ttids.iter().enumerate() {
                padded_token_type_ids[[i, j]] = t as i64;
            }
        }
        
        // Convert to ort Values
        let input_ids_val = Value::from_array((
            padded_input_ids.shape().to_vec(),
            padded_input_ids.clone().into_raw_vec().into_boxed_slice()
        ))?;
        let attention_mask_val = Value::from_array((
            padded_attention_mask.shape().to_vec(),
            padded_attention_mask.clone().into_raw_vec().into_boxed_slice()
        ))?;
        let token_type_ids_val = Value::from_array((
            padded_token_type_ids.shape().to_vec(),
            padded_token_type_ids.into_raw_vec().into_boxed_slice()
        ))?;
        
        // Run inference
        let outputs = self.session.run(ort::inputs![
            "input_ids" => input_ids_val,
            "attention_mask" => attention_mask_val,
            "token_type_ids" => token_type_ids_val
        ])?;
        
        // Get last_hidden_state output (shape: batch_size x seq_len x hidden_dim)
        let (output_shape, output_data) = outputs["last_hidden_state"]
            .try_extract_tensor::<f32>()
            .context("Failed to extract output tensor")?;
        
        let hidden_dim = output_shape[2] as usize;
        let seq_len = output_shape[1] as usize;
        
        // Mean pooling for each sample in batch
        let mut embeddings = Vec::with_capacity(batch_size);
        
        for i in 0..batch_size {
            // Get token embeddings for this sample
            let start_idx = i * seq_len * hidden_dim;
            let end_idx = start_idx + seq_len * hidden_dim;
            let token_emb = &output_data[start_idx..end_idx];
            
            // Get attention mask for this sample
            let mask_row: Vec<i64> = (0..max_len)
                .map(|j| padded_attention_mask[[i, j]])
                .collect();
            
            // Mean pool
            let embedding = mean_pooling(token_emb, &mask_row, seq_len, hidden_dim);
            embeddings.push(embedding);
        }
        
        Ok(embeddings)
    }
    
    /// Process a single embedding job
    fn process_job(&mut self, job: &EmbeddingJob) -> Result<()> {
        let input_path = PathBuf::from(&job.input_path);
        let output_path = PathBuf::from(&job.output_path);
        
        // Double-check idempotency
        if output_path.exists() {
            info!("Output already exists, skipping: {:?}", output_path);
            return Ok(());
        }
        
        // Read input parquet
        let file = std::fs::File::open(&input_path)
            .context(format!("Failed to open input file: {:?}", input_path))?;
        
        let df = ParquetReader::new(file)
            .finish()
            .context(format!("Failed to read parquet: {:?}", input_path))?;
        
        if df.height() == 0 {
            info!("Empty file, skipping: {:?}", input_path);
            return Ok(());
        }
        
        // Extract text column (try common names)
        let text_columns = ["body", "text", "selftext", "content", "message"];
        let text_col_name = text_columns.iter()
            .find(|&col| df.column(col).is_ok())
            .context("No text column found in parquet file")?;
        
        let texts: Vec<String> = df.column(text_col_name)?
            .str()?
            .into_iter()
            .map(|opt| opt.unwrap_or("").to_string())
            .collect();
        
        // Generate embeddings in batches
        let mut all_embeddings: Vec<Vec<f32>> = Vec::with_capacity(texts.len());
        
        for chunk in texts.chunks(BATCH_SIZE) {
            let chunk_texts: Vec<String> = chunk.to_vec();
            let embeddings = self.embed_batch(&chunk_texts)?;
            all_embeddings.extend(embeddings);
        }
        
        // Create output dataframe with embeddings
        // Store as individual columns for each dimension
        let embedding_series: Vec<Series> = (0..EMBEDDING_DIM)
            .map(|dim| {
                let values: Vec<f32> = all_embeddings.iter()
                    .map(|emb| emb.get(dim).copied().unwrap_or(0.0))
                    .collect();
                Series::new(&format!("emb_{:03}", dim), values)
            })
            .collect();
        
        // Clone original columns and add embeddings
        let mut output_columns: Vec<Series> = df.get_columns()
            .iter()
            .map(|s| s.clone())
            .collect();
        
        output_columns.extend(embedding_series);
        
        let output_df = DataFrame::new(output_columns)
            .context("Failed to create output DataFrame")?;
        
        // Create output directory
        if let Some(parent) = output_path.parent() {
            std::fs::create_dir_all(parent)
                .context(format!("Failed to create output directory: {:?}", parent))?;
        }
        
        // Write to temp file first (atomic write)
        let temp_path = output_path.with_extension("parquet.tmp");
        
        {
            let file = std::fs::File::create(&temp_path)
                .context(format!("Failed to create temp file: {:?}", temp_path))?;
            
            ParquetWriter::new(file)
                .with_compression(ParquetCompression::Zstd(None))
                .finish(&mut output_df.clone())
                .context("Failed to write parquet")?;
        }
        
        // Rename temp to final (atomic on most filesystems)
        std::fs::rename(&temp_path, &output_path)
            .context(format!("Failed to rename {:?} to {:?}", temp_path, output_path))?;
        
        Ok(())
    }
    
    /// Main worker loop: consume jobs from Redis
    fn run(&mut self) -> Result<()> {
        info!("Starting worker loop...");
        
        let pb = ProgressBar::new_spinner();
        pb.set_style(ProgressStyle::default_spinner()
            .template("{spinner:.green} [{elapsed_precise}] Jobs processed: {pos} | {msg}")
            .unwrap());
        
        while self.running.load(Ordering::SeqCst) {
            // BLPOP with timeout
            let result: Result<Option<(String, String)>, _> = 
                self.redis_conn.blpop(REDIS_PHASE4_QUEUE, REDIS_TIMEOUT_SECS);
            
            match result {
                Ok(Some((_key, job_json))) => {
                    // Parse job
                    let job: EmbeddingJob = match serde_json::from_str(&job_json) {
                        Ok(j) => j,
                        Err(e) => {
                            warn!("Failed to parse job JSON: {}", e);
                            continue;
                        }
                    };
                    
                    pb.set_message(format!("Processing: {}", 
                        PathBuf::from(&job.input_path)
                            .file_name()
                            .unwrap_or_default()
                            .to_string_lossy()));
                    
                    // Process the job
                    match self.process_job(&job) {
                        Ok(()) => {
                            let count = self.jobs_processed.fetch_add(1, Ordering::SeqCst) + 1;
                            pb.set_position(count);
                        },
                        Err(e) => {
                            error!("Failed to process job {:?}: {}", job.input_path, e);
                            // Job is lost - consider re-queueing for production
                        }
                    }
                },
                Ok(None) => {
                    // Timeout, no jobs available
                    pb.set_message("Waiting for jobs...");
                },
                Err(e) => {
                    error!("Redis error: {}", e);
                    std::thread::sleep(std::time::Duration::from_secs(1));
                }
            }
        }
        
        pb.finish_with_message("Worker stopped");
        Ok(())
    }
}

fn main() -> Result<()> {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();
    
    info!("╔══════════════════════════════════════════════════════════╗");
    info!("║   Phase 4 Worker (ONNX): Embedding Generation            ║");
    info!("╚══════════════════════════════════════════════════════════╝");

    // Set up graceful shutdown
    let running = Arc::new(AtomicBool::new(true));
    let running_ctrlc = running.clone();
    ctrlc::set_handler(move || {
        info!("⚠️  Shutdown signal received, finishing current job...");
        running_ctrlc.store(false, Ordering::SeqCst);
    }).context("Failed to set Ctrl+C handler")?;
    
    let jobs_processed = Arc::new(AtomicU64::new(0));
    
    // Create and run worker
    let mut worker = EmbeddingWorker::new(running.clone(), jobs_processed.clone())?;
    worker.run()?;
    
    let total = jobs_processed.load(Ordering::SeqCst);
    info!("╔══════════════════════════════════════════════════════════╗");
    info!("║   Phase 4 Worker: Shutdown Complete                      ║");
    info!("╠══════════════════════════════════════════════════════════╣");
    info!("║   Jobs processed: {:>10}                            ║", total);
    info!("╚══════════════════════════════════════════════════════════╝");

    Ok(())
}
