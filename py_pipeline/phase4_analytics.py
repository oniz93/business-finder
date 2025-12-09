#!/usr/bin/env python3
"""
Phase 4: AI-Powered Aggregation & Business Plan Generation

This module performs:
1. Data Loading (Polars) - Reads Parquet files from Phase 3 chains output.
2. Embedding (SentenceTransformers) - Generates vectors using MPS (Mac GPU).
3. Clustering (HDBSCAN) - Clusters vectors to identify common business themes.
4. Summarization (Gemini Async) - Summarizes clusters into opportunities.
5. Business Plan Generation (Gemini Async) - Generates full business plans.
6. Storage (Polars) - Saves all outputs to Parquet.
"""

import os
import sys
import glob
import json
import asyncio
import argparse
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field

import polars as pl
import numpy as np
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, SpinnerColumn
from rich.table import Table

# Import project config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.utils import sanitize_for_filesystem

# Initialize console for logging
console = Console()

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Embedding model - good balance of speed and quality
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
# HDBSCAN parameters
MIN_CLUSTER_SIZE = 5
MIN_SAMPLES = 3
# Gemini settings
GEMINI_MODEL_NAME = "gemini-1.5-pro-latest"
MAX_CONCURRENT_GEMINI_CALLS = 10
# Output directory
ANALYSIS_OUTPUT_DIR = os.path.join(config.PROCESSED_DATA_DIR, "..", "analysis")
# Batching
EMBEDDING_BATCH_SIZE = 32


# -----------------------------------------------------------------------------
# Data Classes
# -----------------------------------------------------------------------------

@dataclass
class Opportunity:
    """Represents a clustered business opportunity."""
    cluster_id: int
    representative_texts: List[str]
    cluster_size: int
    avg_quality_score: float
    opportunity_summary: Optional[str] = None
    business_plan_json: Optional[str] = None


# -----------------------------------------------------------------------------
# Embedder Class
# -----------------------------------------------------------------------------

class Embedder:
    """
    Handles embedding text using SentenceTransformers.
    Uses MPS (Metal Performance Shaders) on Mac for GPU acceleration.
    """
    
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self.model = None
        self.device = None
    
    def load_model(self):
        """Load the embedding model with optimal device selection."""
        import torch
        from sentence_transformers import SentenceTransformer
        
        # Determine best available device
        if torch.backends.mps.is_available():
            self.device = "mps"
            console.print("[green]Using MPS (Metal) for GPU acceleration[/green]")
        elif torch.cuda.is_available():
            self.device = "cuda"
            console.print("[green]Using CUDA for GPU acceleration[/green]")
        else:
            self.device = "cpu"
            console.print("[yellow]Using CPU (no GPU detected)[/yellow]")
        
        console.print(f"[blue]Loading embedding model: {self.model_name}[/blue]")
        self.model = SentenceTransformer(self.model_name, device=self.device)
        console.print("[green]Embedding model loaded successfully[/green]")
    
    def embed(self, texts: List[str], batch_size: int = EMBEDDING_BATCH_SIZE, 
              show_progress: bool = True) -> np.ndarray:
        """
        Embed a list of texts into vectors.
        
        Args:
            texts: List of text strings to embed.
            batch_size: Batch size for encoding.
            show_progress: Whether to show a progress bar.
        
        Returns:
            NumPy array of embeddings with shape (len(texts), embedding_dim).
        """
        if self.model is None:
            self.load_model()
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True  # Normalize for cosine similarity
        )
        return embeddings


# -----------------------------------------------------------------------------
# Clusterer Class
# -----------------------------------------------------------------------------

class Clusterer:
    """
    Wraps HDBSCAN clustering logic for grouping similar ideas.
    """
    
    def __init__(self, min_cluster_size: int = MIN_CLUSTER_SIZE, 
                 min_samples: int = MIN_SAMPLES):
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
    
    def cluster(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Cluster embeddings using HDBSCAN.
        
        Args:
            embeddings: NumPy array of embeddings (N, D).
        
        Returns:
            Array of cluster labels for each embedding. -1 indicates noise.
        """
        try:
            import hdbscan
            console.print("[blue]Using HDBSCAN for clustering[/blue]")
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=self.min_cluster_size,
                min_samples=self.min_samples,
                metric="euclidean",
                cluster_selection_method="eom"
            )
        except ImportError:
            # Fallback to sklearn if hdbscan not installed
            console.print("[yellow]HDBSCAN not found, falling back to sklearn DBSCAN[/yellow]")
            from sklearn.cluster import DBSCAN
            clusterer = DBSCAN(eps=0.5, min_samples=self.min_samples)
        
        cluster_labels = clusterer.fit_predict(embeddings)
        
        # Log clustering stats
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        n_noise = list(cluster_labels).count(-1)
        console.print(f"[green]Clustering complete: {n_clusters} clusters, {n_noise} noise points[/green]")
        
        return cluster_labels


# -----------------------------------------------------------------------------
# IdeaGenerator Class (Async Gemini)
# -----------------------------------------------------------------------------

class IdeaGenerator:
    """
    Handles async Gemini API calls for summarization and business plan generation.
    """
    
    def __init__(self, model_name: str = GEMINI_MODEL_NAME, 
                 max_concurrent: int = MAX_CONCURRENT_GEMINI_CALLS):
        self.model_name = model_name
        self.max_concurrent = max_concurrent
        self._semaphore = None
        self._model = None
    
    def _setup_client(self):
        """Initialize the Gemini client."""
        import google.generativeai as genai
        
        # Check for API key
        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "Gemini API key not found. Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable."
            )
        
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(self.model_name)
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        console.print(f"[green]Gemini client initialized with model: {self.model_name}[/green]")
    
    async def _call_gemini(self, prompt: str) -> str:
        """
        Make a single API call to Gemini with rate limiting.
        
        Args:
            prompt: The prompt to send.
        
        Returns:
            The generated text response.
        """
        if self._model is None:
            self._setup_client()
        
        async with self._semaphore:
            try:
                response = await self._model.generate_content_async(prompt)
                return response.text
            except Exception as e:
                console.print(f"[red]Gemini API error: {e}[/red]")
                return f"Error: {str(e)}"
    
    async def summarize_cluster(self, texts: List[str]) -> str:
        """
        Summarize a cluster of related ideas into a single opportunity statement.
        
        Args:
            texts: List of representative texts from the cluster.
        
        Returns:
            A concise 1-2 sentence opportunity summary.
        """
        prompt = f"""You are a business analyst identifying market opportunities from Reddit discussions.

Below are {len(texts)} related Reddit posts/comments that share a common theme:

---
{chr(10).join(f"- {t[:500]}" for t in texts[:10])}
---

Synthesize these into ONE clear, actionable business opportunity statement (1-2 sentences).
Focus on:
1. The core unmet need or pain point
2. The potential solution or product category
3. The target audience

Respond with ONLY the opportunity statement, no preamble."""

        return await self._call_gemini(prompt)
    
    async def generate_business_plan(self, opportunity_summary: str, 
                                     supporting_texts: List[str]) -> str:
        """
        Generate a full business plan for a given opportunity.
        
        Args:
            opportunity_summary: The synthesized opportunity statement.
            supporting_texts: Sample texts that support this opportunity.
        
        Returns:
            A JSON-formatted business plan.
        """
        prompt = f"""You are a startup business consultant. Generate a comprehensive business plan for the following opportunity:

**Opportunity:** {opportunity_summary}

**Supporting Evidence from Reddit:**
{chr(10).join(f"- {t[:300]}" for t in supporting_texts[:5])}

Generate a business plan in the following JSON structure:
{{
    "executive_summary": "2-3 sentence overview",
    "problem_statement": "The core problem being solved",
    "proposed_solution": "Product/service description",
    "target_market": {{
        "primary_audience": "Description",
        "market_size_estimate": "Small/Medium/Large with reasoning"
    }},
    "value_proposition": "Why customers would choose this",
    "revenue_model": "How this makes money",
    "competitive_advantages": ["advantage1", "advantage2"],
    "key_risks": ["risk1", "risk2"],
    "initial_mvp_steps": ["step1", "step2", "step3"],
    "estimated_complexity": "Low/Medium/High",
    "confidence_score": 0.0-1.0
}}

Respond with ONLY valid JSON, no markdown code blocks or preamble."""

        return await self._call_gemini(prompt)
    
    async def process_opportunities(self, opportunities: List[Opportunity], 
                                    progress: Optional[Progress] = None) -> List[Opportunity]:
        """
        Process all opportunities: summarize clusters and generate business plans.
        
        Args:
            opportunities: List of Opportunity objects with representative_texts populated.
            progress: Optional Rich progress bar.
        
        Returns:
            List of Opportunity objects with summaries and business plans filled in.
        """
        if self._model is None:
            self._setup_client()
        
        # Phase 1: Summarize all clusters concurrently
        console.print(f"[blue]Summarizing {len(opportunities)} clusters...[/blue]")
        
        async def summarize_one(opp: Opportunity) -> Opportunity:
            opp.opportunity_summary = await self.summarize_cluster(opp.representative_texts)
            return opp
        
        summarize_tasks = [summarize_one(opp) for opp in opportunities]
        opportunities = await asyncio.gather(*summarize_tasks)
        
        # Phase 2: Generate business plans concurrently
        console.print(f"[blue]Generating business plans for {len(opportunities)} opportunities...[/blue]")
        
        async def generate_plan_one(opp: Opportunity) -> Opportunity:
            opp.business_plan_json = await self.generate_business_plan(
                opp.opportunity_summary,
                opp.representative_texts
            )
            return opp
        
        plan_tasks = [generate_plan_one(opp) for opp in opportunities]
        opportunities = await asyncio.gather(*plan_tasks)
        
        return list(opportunities)


# -----------------------------------------------------------------------------
# Pipeline Class
# -----------------------------------------------------------------------------

class Pipeline:
    """
    Orchestrates the entire Phase 4 pipeline:
    1. Load data from Parquet
    2. Embed texts
    3. Cluster embeddings
    4. Summarize clusters
    5. Generate business plans
    6. Save results
    """
    
    def __init__(self, input_dir: str = None, output_dir: str = None):
        self.input_dir = input_dir or config.PROCESSED_DATA_DIR
        self.output_dir = output_dir or ANALYSIS_OUTPUT_DIR
        
        self.embedder = Embedder()
        self.clusterer = Clusterer()
        self.generator = IdeaGenerator()
    
    def find_input_files(self) -> List[str]:
        """
        Find all Parquet files from Phase 3 output.
        Looks for chains_chunk_*.parquet or similar patterns.
        """
        patterns = [
            os.path.join(self.input_dir, "**", "chains_*.parquet"),
            os.path.join(self.input_dir, "**", "*.parquet"),
        ]
        
        files = []
        for pattern in patterns:
            found = glob.glob(pattern, recursive=True)
            if found:
                files.extend(found)
                break  # Use first matching pattern
        
        # Deduplicate
        files = list(set(files))
        console.print(f"[blue]Found {len(files)} Parquet files to process[/blue]")
        return files
    
    def load_data(self, file_paths: List[str]) -> pl.DataFrame:
        """
        Load and combine data from multiple Parquet files.
        
        Args:
            file_paths: List of paths to Parquet files.
        
        Returns:
            Combined Polars DataFrame.
        """
        console.print(f"[blue]Loading data from {len(file_paths)} files...[/blue]")
        
        dfs = []
        for path in file_paths:
            try:
                df = pl.read_parquet(path)
                dfs.append(df)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not read {path}: {e}[/yellow]")
        
        if not dfs:
            return pl.DataFrame()
        
        combined = pl.concat(dfs)
        console.print(f"[green]Loaded {combined.height} rows total[/green]")
        return combined
    
    def extract_texts(self, df: pl.DataFrame) -> Tuple[List[str], pl.DataFrame]:
        """
        Extract text content from the DataFrame.
        
        Args:
            df: Input DataFrame.
        
        Returns:
            Tuple of (list of texts, filtered DataFrame).
        """
        # Try various column names for text content
        text_columns = ["body", "text", "selftext", "content", "message"]
        text_col = None
        
        for col in text_columns:
            if col in df.columns:
                text_col = col
                break
        
        if text_col is None:
            raise ValueError(f"No text column found. Available columns: {df.columns}")
        
        # Filter out empty/null texts
        df_filtered = df.filter(
            pl.col(text_col).is_not_null() & 
            (pl.col(text_col).str.len_chars() > 10)
        )
        
        texts = df_filtered[text_col].to_list()
        console.print(f"[green]Extracted {len(texts)} texts for embedding[/green]")
        
        return texts, df_filtered
    
    def build_opportunities(self, df: pl.DataFrame, texts: List[str], 
                           cluster_labels: np.ndarray) -> List[Opportunity]:
        """
        Build Opportunity objects from clustered data.
        
        Args:
            df: The source DataFrame.
            texts: List of texts that were clustered.
            cluster_labels: Cluster assignment for each text.
        
        Returns:
            List of Opportunity objects for non-noise clusters.
        """
        # Add cluster labels to a working copy
        df_with_clusters = df.with_columns(
            pl.Series("cluster_id", cluster_labels)
        )
        
        # Filter out noise (-1)
        df_clustered = df_with_clusters.filter(pl.col("cluster_id") >= 0)
        
        opportunities = []
        unique_clusters = df_clustered["cluster_id"].unique().to_list()
        
        for cluster_id in unique_clusters:
            cluster_df = df_clustered.filter(pl.col("cluster_id") == cluster_id)
            cluster_texts = [texts[i] for i, label in enumerate(cluster_labels) if label == cluster_id]
            
            # Get quality score if available
            quality_col = None
            for col in ["quality_score", "score", "nlp_score"]:
                if col in cluster_df.columns:
                    quality_col = col
                    break
            
            avg_quality = 0.0
            if quality_col:
                avg_quality = cluster_df[quality_col].mean() or 0.0
            
            # Sample representative texts (up to 10)
            representative = cluster_texts[:10]
            
            opportunities.append(Opportunity(
                cluster_id=int(cluster_id),
                representative_texts=representative,
                cluster_size=len(cluster_texts),
                avg_quality_score=float(avg_quality)
            ))
        
        console.print(f"[green]Built {len(opportunities)} opportunities from clusters[/green]")
        return opportunities
    
    def save_results(self, opportunities: List[Opportunity], subreddit: str = "all"):
        """
        Save opportunities to Parquet files.
        
        Args:
            opportunities: List of processed Opportunity objects.
            subreddit: Subreddit name for output directory organization.
        """
        output_dir = os.path.join(self.output_dir, sanitize_for_filesystem(subreddit))
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert to DataFrame
        data = {
            "cluster_id": [o.cluster_id for o in opportunities],
            "cluster_size": [o.cluster_size for o in opportunities],
            "avg_quality_score": [o.avg_quality_score for o in opportunities],
            "opportunity_summary": [o.opportunity_summary for o in opportunities],
            "business_plan_json": [o.business_plan_json for o in opportunities],
            "representative_texts": [json.dumps(o.representative_texts) for o in opportunities],
        }
        
        df = pl.DataFrame(data)
        output_path = os.path.join(output_dir, "opportunities.parquet")
        df.write_parquet(output_path)
        
        console.print(f"[green]Saved {len(opportunities)} opportunities to {output_path}[/green]")
        
        # Also save a CSV for easy inspection
        csv_path = os.path.join(output_dir, "opportunities.csv")
        df.write_csv(csv_path)
        console.print(f"[green]Also saved CSV to {csv_path}[/green]")
    
    async def run(self, test_mode: bool = False, input_override: Optional[str] = None):
        """
        Execute the full pipeline.
        
        Args:
            test_mode: If True, use limited data for testing.
            input_override: Override input directory path.
        """
        console.rule("[bold blue]Phase 4: AI-Powered Aggregation & Business Plan Generation[/bold blue]")
        
        # Override input if specified
        if input_override:
            self.input_dir = input_override
        
        # Step 1: Find input files
        console.print("\n[bold]Step 1: Finding input files[/bold]")
        input_files = self.find_input_files()
        
        if not input_files:
            console.print("[red]No input files found. Exiting.[/red]")
            return
        
        # Step 2: Load data
        console.print("\n[bold]Step 2: Loading data[/bold]")
        df = self.load_data(input_files)
        
        if df.height == 0:
            console.print("[red]No data loaded. Exiting.[/red]")
            return
        
        # Limit data in test mode
        if test_mode:
            df = df.head(100)
            console.print(f"[yellow]Test mode: Limited to {df.height} rows[/yellow]")
        
        # Step 3: Extract texts
        console.print("\n[bold]Step 3: Extracting texts[/bold]")
        texts, df_filtered = self.extract_texts(df)
        
        if len(texts) < MIN_CLUSTER_SIZE:
            console.print(f"[red]Not enough texts ({len(texts)}) for clustering. Need at least {MIN_CLUSTER_SIZE}.[/red]")
            return
        
        # Step 4: Embed texts
        console.print("\n[bold]Step 4: Generating embeddings[/bold]")
        embeddings = self.embedder.embed(texts)
        console.print(f"[green]Generated embeddings with shape: {embeddings.shape}[/green]")
        
        # Step 5: Cluster embeddings
        console.print("\n[bold]Step 5: Clustering[/bold]")
        cluster_labels = self.clusterer.cluster(embeddings)
        
        # Step 6: Build opportunities
        console.print("\n[bold]Step 6: Building opportunities[/bold]")
        opportunities = self.build_opportunities(df_filtered, texts, cluster_labels)
        
        if not opportunities:
            console.print("[yellow]No valid opportunities found after clustering.[/yellow]")
            return
        
        # Step 7: Generate summaries and business plans
        console.print("\n[bold]Step 7: AI-Powered Generation (Gemini)[/bold]")
        
        # Check if API key is available
        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            console.print("[yellow]Warning: No Gemini API key found. Skipping AI generation.[/yellow]")
            console.print("[yellow]Set GOOGLE_API_KEY or GEMINI_API_KEY to enable.[/yellow]")
        else:
            opportunities = await self.generator.process_opportunities(opportunities)
        
        # Step 8: Save results
        console.print("\n[bold]Step 8: Saving results[/bold]")
        self.save_results(opportunities)
        
        # Summary
        console.rule("[bold green]Pipeline Complete[/bold green]")
        
        summary_table = Table(title="Results Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green")
        summary_table.add_row("Total texts processed", str(len(texts)))
        summary_table.add_row("Clusters found", str(len(opportunities)))
        summary_table.add_row("Noise points", str(list(cluster_labels).count(-1)))
        summary_table.add_row("Output directory", self.output_dir)
        console.print(summary_table)


# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Phase 4: AI-Powered Aggregation & Business Plan Generation"
    )
    parser.add_argument(
        "--test-mode", "-t",
        action="store_true",
        help="Run in test mode with limited data"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=None,
        help="Override input directory path"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Override output directory path"
    )
    
    args = parser.parse_args()
    
    pipeline = Pipeline(
        input_dir=args.input,
        output_dir=args.output
    )
    
    asyncio.run(pipeline.run(test_mode=args.test_mode, input_override=args.input))


if __name__ == "__main__":
    main()
