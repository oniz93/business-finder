#!/usr/bin/env python3
"""
Export Sentence-Transformers Model to ONNX

This script exports a sentence-transformers model to ONNX format for use with
the Rust ONNX worker (phase4_worker).

Usage:
    python export_onnx.py --model sentence-transformers/all-MiniLM-L6-v2 --output models/onnx/minilm/

Requirements:
    pip install sentence-transformers onnx onnxruntime optimum[onnxruntime]
"""

import os
import sys
import argparse
import shutil
from pathlib import Path

from rich.console import Console

console = Console()


def export_model(model_name: str, output_dir: str, quantize: bool = False):
    """
    Export a sentence-transformers model to ONNX format.
    
    Args:
        model_name: HuggingFace model name or path
        output_dir: Directory to save the ONNX model and tokenizer
        quantize: Whether to quantize the model (smaller but potentially less accurate)
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    console.print(f"[blue]Exporting model: {model_name}[/blue]")
    console.print(f"[blue]Output directory: {output_path}[/blue]")
    
    try:
        from optimum.onnxruntime import ORTModelForFeatureExtraction
        from transformers import AutoTokenizer
    except ImportError:
        console.print("[red]Missing dependencies. Install with:[/red]")
        console.print("pip install optimum[onnxruntime] sentence-transformers transformers")
        sys.exit(1)
    
    # For sentence-transformers models, we need to get the underlying transformer
    # The model name format is usually: sentence-transformers/all-MiniLM-L6-v2
    # or just: all-MiniLM-L6-v2
    
    if not model_name.startswith("sentence-transformers/"):
        hf_model_name = f"sentence-transformers/{model_name}"
    else:
        hf_model_name = model_name
    
    console.print(f"[blue]Loading from HuggingFace: {hf_model_name}[/blue]")
    
    # Export to ONNX using optimum
    console.print("[blue]Exporting to ONNX format...[/blue]")
    
    try:
        model = ORTModelForFeatureExtraction.from_pretrained(
            hf_model_name,
            export=True,
            provider="CPUExecutionProvider"
        )
        
        # Save the ONNX model
        model.save_pretrained(output_path)
        console.print("[green]✓ Model exported to ONNX[/green]")
        
    except Exception as e:
        console.print(f"[yellow]Optimum export failed: {e}[/yellow]")
        console.print("[blue]Trying alternative export method...[/blue]")
        
        # Alternative: use transformers + torch.onnx directly
        try:
            import torch
            from transformers import AutoModel, AutoTokenizer
            
            tokenizer = AutoTokenizer.from_pretrained(hf_model_name)
            model = AutoModel.from_pretrained(hf_model_name)
            model.eval()
            
            # Create dummy inputs
            dummy_text = "This is a sample sentence for export."
            inputs = tokenizer(
                dummy_text,
                padding="max_length",
                max_length=128,
                truncation=True,
                return_tensors="pt"
            )
            
            # Export to ONNX
            onnx_path = output_path / "model.onnx"
            
            torch.onnx.export(
                model,
                (inputs["input_ids"], inputs["attention_mask"], inputs["token_type_ids"]),
                str(onnx_path),
                input_names=["input_ids", "attention_mask", "token_type_ids"],
                output_names=["last_hidden_state"],
                dynamic_axes={
                    "input_ids": {0: "batch_size", 1: "sequence"},
                    "attention_mask": {0: "batch_size", 1: "sequence"},
                    "token_type_ids": {0: "batch_size", 1: "sequence"},
                    "last_hidden_state": {0: "batch_size", 1: "sequence"}
                },
                opset_version=14,
                do_constant_folding=True
            )
            
            console.print("[green]✓ Model exported via torch.onnx[/green]")
            
            # Save tokenizer
            tokenizer.save_pretrained(output_path)
            console.print("[green]✓ Tokenizer saved[/green]")
            
        except Exception as e2:
            console.print(f"[red]Alternative export also failed: {e2}[/red]")
            sys.exit(1)
    
    # Load and save tokenizer separately to ensure we have tokenizer.json
    console.print("[blue]Saving tokenizer...[/blue]")
    try:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(hf_model_name)
        tokenizer.save_pretrained(output_path)
        
        # Ensure tokenizer.json exists (needed by Rust tokenizers crate)
        if not (output_path / "tokenizer.json").exists():
            console.print("[yellow]tokenizer.json not found, creating from tokenizer...[/yellow]")
            # Some tokenizers need to be saved in fast format
            if hasattr(tokenizer, 'save_pretrained'):
                tokenizer.save_pretrained(output_path, legacy_format=False)
        
        console.print("[green]✓ Tokenizer saved[/green]")
        
    except Exception as e:
        console.print(f"[yellow]Warning: Could not save tokenizer separately: {e}[/yellow]")
    
    # Optionally quantize
    if quantize:
        console.print("[blue]Quantizing model...[/blue]")
        try:
            from optimum.onnxruntime import ORTQuantizer
            from optimum.onnxruntime.configuration import AutoQuantizationConfig
            
            quantizer = ORTQuantizer.from_pretrained(output_path)
            qconfig = AutoQuantizationConfig.avx512_vnni(is_static=False)
            
            quantized_path = output_path / "quantized"
            quantizer.quantize(qconfig, save_dir=quantized_path)
            
            console.print(f"[green]✓ Quantized model saved to: {quantized_path}[/green]")
            
        except Exception as e:
            console.print(f"[yellow]Quantization failed: {e}[/yellow]")
    
    # Verify the export
    console.print("\n[blue]Verifying export...[/blue]")
    
    onnx_file = output_path / "model.onnx"
    tokenizer_file = output_path / "tokenizer.json"
    
    if onnx_file.exists():
        size_mb = onnx_file.stat().st_size / (1024 * 1024)
        console.print(f"[green]✓ model.onnx ({size_mb:.1f} MB)[/green]")
    else:
        # Check for model_optimized.onnx from optimum
        alt_onnx = output_path / "model_optimized.onnx"
        if alt_onnx.exists():
            shutil.copy(alt_onnx, onnx_file)
            console.print("[green]✓ model.onnx (copied from model_optimized.onnx)[/green]")
        else:
            console.print("[red]✗ model.onnx not found![/red]")
    
    if tokenizer_file.exists():
        console.print("[green]✓ tokenizer.json[/green]")
    else:
        console.print("[yellow]⚠ tokenizer.json not found (may need vocab.txt instead)[/yellow]")
    
    # List all exported files
    console.print("\n[blue]Exported files:[/blue]")
    for f in sorted(output_path.iterdir()):
        if f.is_file():
            size = f.stat().st_size
            if size > 1024 * 1024:
                size_str = f"{size / (1024*1024):.1f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} B"
            console.print(f"  {f.name}: {size_str}")
    
    console.print("\n[green]Export complete![/green]")
    console.print(f"\nUse with Rust worker by setting MODEL_DIR to: {output_path.absolute()}")


def main():
    parser = argparse.ArgumentParser(
        description="Export Sentence-Transformers model to ONNX"
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default="all-MiniLM-L6-v2",
        help="Model name (default: all-MiniLM-L6-v2)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="models/onnx/minilm",
        help="Output directory (default: models/onnx/minilm)"
    )
    parser.add_argument(
        "--quantize", "-q",
        action="store_true",
        help="Quantize the model for smaller size"
    )
    
    args = parser.parse_args()
    
    console.print("╔══════════════════════════════════════════════════════════╗")
    console.print("║   ONNX Model Export for Sentence-Transformers            ║")
    console.print("╚══════════════════════════════════════════════════════════╝")
    
    export_model(args.model, args.output, args.quantize)


if __name__ == "__main__":
    main()
