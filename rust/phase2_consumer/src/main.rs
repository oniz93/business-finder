use anyhow::Result;
use clap::Parser;
use log::{error, info, warn};
use ndarray::Array2;
use ort::session::{Session, builder::{GraphOptimizationLevel, SessionBuilder}};
use ort::value::Value;
use redis::AsyncCommands;
use serde::{Deserialize, Serialize};
use std::time::{Duration, Instant};
use tokenizers::Tokenizer;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    // #[arg(long, env = "REDIS_URL", default_value = "redis://localhost:6379/0")]
    #[arg(long, env = "REDIS_URL", default_value = "redis://:kRoGWJXNK75zMIcJz4RDDhNhz1hfKq6OLAzCaCFPVIw%3D@businessfinder.canadacentral.redis.azure.net:10000/0")]
    redis_url: String,

    #[arg(long, env = "MODEL_PATH", default_value = "models/onnx/zeroshot/model.onnx")]
    model_path: String,

    #[arg(long, env = "TOKENIZER_PATH", default_value = "models/onnx/zeroshot/tokenizer.json")]
    tokenizer_path: String,

    #[arg(long, env = "BATCH_SIZE", default_value_t = 1000)]
    batch_size: usize,
}

#[derive(Debug, Deserialize, Serialize)]
struct Job {
    file_path: String,
    row_id: String,
    text: String,
}

#[derive(Debug, Serialize)]
struct NlpResult {
    file_path: String,
    row_id: String,
    nlp_label: String,
    nlp_score: f32,
}

const REDIS_TODO_QUEUE: &str = "nlp_todo_queue";
const REDIS_RESULTS_QUEUE: &str = "nlp_results_queue";
const CANDIDATE_LABELS: [&str; 2] = ["pain point", "idea"];
const HYPOTHESIS_TEMPLATE: &str = "This example is {}.";

struct Classifier {
    session: Session,
    tokenizer: Tokenizer,
}

impl Classifier {
    fn new(model_path: &str, tokenizer_path: &str) -> Result<Self> {
        // Load Tokenizer
        let mut tokenizer = Tokenizer::from_file(tokenizer_path)
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

        // Initialize ONNX Session
        let session = SessionBuilder::new()?
            .with_optimization_level(GraphOptimizationLevel::Level3)?
            .with_intra_threads(4)?
            .commit_from_file(model_path)?;

        Ok(Self { session, tokenizer })
    }

    fn predict(&mut self, text: &str) -> Result<(String, f32)> {
        // Construct input pairs for NLI
        // (premise, hypothesis)
        let mut input_ids_batch = Vec::new();
        let mut attention_mask_batch = Vec::new();
        let mut token_type_ids_batch = Vec::new();

        for label in CANDIDATE_LABELS {
            let hypothesis = HYPOTHESIS_TEMPLATE.replace("{}", label);
            // Encode the pair (text, hypothesis) with truncation and padding
            let encoding = self.tokenizer.encode(
                tokenizers::EncodeInput::Dual(text.into(), hypothesis.into()),
                true
            ).map_err(|e| anyhow::anyhow!("Tokenization error: {}", e))?;

            let input_ids: Vec<i64> = encoding.get_ids().iter().map(|&x| x as i64).collect();
            let attention_mask: Vec<i64> = encoding.get_attention_mask().iter().map(|&x| x as i64).collect();
            let token_type_ids: Vec<i64> = encoding.get_type_ids().iter().map(|&x| x as i64).collect();

            input_ids_batch.push(input_ids);
            attention_mask_batch.push(attention_mask);
            token_type_ids_batch.push(token_type_ids);
        }

        // Pad batch
        let max_len = input_ids_batch.iter().map(|v| v.len()).max().unwrap_or(0);
        let batch_size = CANDIDATE_LABELS.len();

        let mut padded_input_ids = Array2::<i64>::zeros((batch_size, max_len));
        let mut padded_attention_mask = Array2::<i64>::zeros((batch_size, max_len));
        let mut padded_token_type_ids = Array2::<i64>::zeros((batch_size, max_len));

        for (i, seq) in input_ids_batch.iter().enumerate() {
            for (j, &val) in seq.iter().enumerate() {
                padded_input_ids[[i, j]] = val;
                padded_attention_mask[[i, j]] = attention_mask_batch[i][j];
                padded_token_type_ids[[i, j]] = token_type_ids_batch[i][j];
            }
        }

        // Run Inference
        // Convert ndarray to (shape, data) tuples for ort compatibility
        let input_ids_val = Value::from_array((
            padded_input_ids.shape().to_vec(),
            padded_input_ids.into_raw_vec().into_boxed_slice()
        ))?;
        let attention_mask_val = Value::from_array((
            padded_attention_mask.shape().to_vec(),
            padded_attention_mask.into_raw_vec().into_boxed_slice()
        ))?;
        let token_type_ids_val = Value::from_array((
            padded_token_type_ids.shape().to_vec(),
            padded_token_type_ids.into_raw_vec().into_boxed_slice()
        ))?;

        let outputs = self.session.run(ort::inputs![
            "input_ids" => input_ids_val,
            "attention_mask" => attention_mask_val,
            "token_type_ids" => token_type_ids_val
        ])?;


        // try_extract_tensor returns (&Shape, &[T])
        let (logits_shape, logits_data) = outputs["logits"].try_extract_tensor::<f32>()?;

        // NLI models usually output: [entailment, neutral, contradiction] or similar.
        // We need to check the config. For xtremedistil-l6-h256-zeroshot-v1.1-all-33:
        // It's trained on MNLI/NLI.
        // Usually index 0 is "entailment" or index 1.
        // Actually, for `MoritzLaurer/xtremedistil...` the label mapping is often:
        // 0: contradiction, 1: entailment (or vice versa).
        // Standard pipeline assumes: entailment_id is the one we want.
        // Let's assume standard MNLI: 0=contradiction, 1=entailment, 2=neutral.
        // BUT, many zero-shot models are binary or just check entailment vs not-entailment.
        // Let's assume the "entailment" logits are at index 1 (common for these models).
        // To be safe, we should check `config.json` but for now we'll assume index 1 is entailment.
        
        // Softmax over the entailment logits across the candidate labels
        let entailment_idx = 1; // This might need adjustment based on specific model config
        
        // Extract entailment logits from the flat data array
        // Shape is (batch_size, num_classes), data is row-major
        let num_classes = logits_shape[1] as usize;
        let mut entailment_logits = Vec::new();
        for i in 0..batch_size {
            // Access flat array: row i, column entailment_idx
            let logit = logits_data[i * num_classes + entailment_idx];
            entailment_logits.push(logit);
        }

        // Softmax
        let max_logit = entailment_logits.iter().cloned().fold(f32::NEG_INFINITY, f32::max);
        let exp_sum: f32 = entailment_logits.iter().map(|&x| (x - max_logit).exp()).sum();
        let probs: Vec<f32> = entailment_logits.iter().map(|&x| (x - max_logit).exp() / exp_sum).collect();

        // Find best label
        let mut best_idx = 0;
        let mut best_score = 0.0;

        for (i, &score) in probs.iter().enumerate() {
            if score > best_score {
                best_score = score;
                best_idx = i;
            }
        }

        // Map "pain point" -> "pain_point" for consistency with Python script
        let label = CANDIDATE_LABELS[best_idx].replace(" ", "_");
        
        Ok((label, best_score))
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();
    let args = Args::parse();

    info!("Starting Rust NLP Consumer...");
    info!("Redis URL: {}", args.redis_url);
    info!("Model Path: {}", args.model_path);

    // Initialize Classifier
    info!("Loading model...");
    let mut classifier = Classifier::new(&args.model_path, &args.tokenizer_path)?;
    info!("Model loaded successfully.");

    // Connect to Redis
    let client = redis::Client::open(args.redis_url.clone())?;
    let mut con = client.get_async_connection().await?;

    info!("Connected to Redis. Waiting for jobs...");

    loop {
        // Backpressure check
        let results_len: u64 = con.llen(REDIS_RESULTS_QUEUE).await.unwrap_or(0);
        if results_len > 10000 {
            warn!("Results queue full ({}), pausing...", results_len);
            tokio::time::sleep(Duration::from_secs(5)).await;
            continue;
        }

        // Fetch batch of jobs
        // We use lpop with count (Redis 6.2+)
        let jobs_json: Vec<String> = match redis::cmd("LPOP")
            .arg(REDIS_TODO_QUEUE)
            .arg(args.batch_size)
            .query_async(&mut con)
            .await
        {
            Ok(jobs) => jobs,
            Err(e) => {
                error!("Redis error fetching jobs: {}", e);
                tokio::time::sleep(Duration::from_secs(1)).await;
                continue;
            }
        };

        if jobs_json.is_empty() {
            // Wait a bit if queue is empty to avoid busy loop
            // Alternatively use blpop, but that's harder with batching
            tokio::time::sleep(Duration::from_millis(100)).await;
            continue;
        }

        let start = Instant::now();
        let mut results = Vec::new();
        let mut processed_count = 0;

        for job_str in jobs_json {
            let job: Job = match serde_json::from_str(&job_str) {
                Ok(j) => j,
                Err(e) => {
                    error!("Failed to parse job JSON: {}", e);
                    continue;
                }
            };

            // Run inference
            // Note: We are running inference sequentially for each job in the batch here.
            // Ideally, we would batch the inference itself (tensor batching), but 
            // since we are doing NLI (expanding 1 text to N pairs), we are already batching 
            // inside `predict` across the candidate labels.
            // Further optimization: Batch M texts -> M * N pairs.
            match classifier.predict(&job.text) {
                Ok((label, score)) => {
                    let result = NlpResult {
                        file_path: job.file_path,
                        row_id: job.row_id,
                        nlp_label: label,
                        nlp_score: score,
                    };
                    if let Ok(json) = serde_json::to_string(&result) {
                        results.push(json);
                    }
                    processed_count += 1;
                }
                Err(e) => {
                    error!("Inference failed for job {}: {}", job.row_id, e);
                }
            }
        }

        // Push results
        if !results.is_empty() {
            if let Err(e) = con.rpush::<_, _, ()>(REDIS_RESULTS_QUEUE, &results).await {
                error!("Failed to push results to Redis: {}", e);
            }
        }

        let elapsed = start.elapsed();
        if processed_count > 0 {
            let fps = processed_count as f64 / elapsed.as_secs_f64();
            info!("Processed {} jobs in {:.2?} ({:.2} msg/s)", processed_count, elapsed, fps);
        }
    }
}
