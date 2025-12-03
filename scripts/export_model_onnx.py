import argparse
from pathlib import Path
from optimum.onnxruntime import ORTModelForSequenceClassification
from transformers import AutoTokenizer

def export_model(model_id, output_dir):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Exporting model: {model_id} to {output_path}")

    # Load and export to ONNX
    model = ORTModelForSequenceClassification.from_pretrained(
        model_id,
        export=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_id)

    # Save model and tokenizer
    model.save_pretrained(output_path)
    tokenizer.save_pretrained(output_path)
    
    print(f"✅ Model exported successfully to {output_path}")
    print(f"Files created: {[f.name for f in output_path.glob('*')]}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export Hugging Face model to ONNX for Rust")
    parser.add_argument("--model", type=str, default="MoritzLaurer/xtremedistil-l6-h256-zeroshot-v1.1-all-33", help="Model ID")
    parser.add_argument("--output", type=str, default="models/onnx/zeroshot", help="Output directory")
    args = parser.parse_args()

    export_model(args.model, args.output)
