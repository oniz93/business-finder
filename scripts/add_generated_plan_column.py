#!/usr/bin/env python3
"""
Migration script to add 'generated_plan' column to existing ideas.parquet files.

This script scans all ideas.parquet files in the IDEAS_OUTPUT_DIR and adds
the 'generated_plan' column (empty string) if it doesn't exist.

Usage:
    python scripts/add_generated_plan_column.py [--dry-run]
"""

import os
import sys
import glob
import argparse

import polars as pl
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

console = Console()

# Configuration
IDEAS_OUTPUT_DIR = "/Volumes/2TBSSD/reddit/ideas"


def migrate_file(filepath: str, dry_run: bool = False) -> bool:
    """
    Add 'generated_plan' column to a parquet file if it doesn't exist.
    Returns True if file was modified, False otherwise.
    """
    try:
        df = pl.read_parquet(filepath)
        
        if "generated_plan" in df.columns:
            return False  # Already has the column
        
        # Add the column with empty string
        df = df.with_columns(pl.lit("").alias("generated_plan"))
        
        if not dry_run:
            # Write back to the same file
            df.write_parquet(filepath, compression="zstd")
        
        return True
        
    except Exception as e:
        console.print(f"[red]Error processing {filepath}: {e}[/red]")
        return False


def main():
    parser = argparse.ArgumentParser(description="Add generated_plan column to ideas.parquet files")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually modify files, just report what would be done")
    args = parser.parse_args()
    
    console.rule("[bold blue]Migration: Add generated_plan column[/bold blue]")
    
    if args.dry_run:
        console.print("[yellow]DRY RUN MODE - no files will be modified[/yellow]\n")
    
    # Find all ideas.parquet files
    pattern = os.path.join(IDEAS_OUTPUT_DIR, "**", "ideas.parquet")
    files = glob.glob(pattern, recursive=True)
    
    if not files:
        console.print(f"[yellow]No ideas.parquet files found in {IDEAS_OUTPUT_DIR}[/yellow]")
        return
    
    console.print(f"Found {len(files)} ideas.parquet files\n")
    
    modified_count = 0
    skipped_count = 0
    error_count = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Processing files...", total=len(files))
        
        for filepath in files:
            rel_path = os.path.relpath(filepath, IDEAS_OUTPUT_DIR)
            progress.update(task, description=f"Processing {rel_path}")
            
            try:
                df = pl.read_parquet(filepath)
                
                if "generated_plan" in df.columns:
                    skipped_count += 1
                    progress.advance(task)
                    continue
                
                # Add the column
                df = df.with_columns(pl.lit("").alias("generated_plan"))
                
                if not args.dry_run:
                    df.write_parquet(filepath, compression="zstd")
                
                console.print(f"[green]✓ Modified: {rel_path}[/green]")
                modified_count += 1
                
            except Exception as e:
                console.print(f"[red]✗ Error: {rel_path} - {e}[/red]")
                error_count += 1
            
            progress.advance(task)
    
    # Summary
    console.print()
    console.rule("[bold]Summary[/bold]")
    console.print(f"[green]Modified: {modified_count}[/green]")
    console.print(f"[dim]Skipped (already had column): {skipped_count}[/dim]")
    if error_count > 0:
        console.print(f"[red]Errors: {error_count}[/red]")
    
    if args.dry_run:
        console.print("\n[yellow]This was a dry run. Run without --dry-run to apply changes.[/yellow]")


if __name__ == "__main__":
    main()
