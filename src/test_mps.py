
import torch
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer

try:
    if torch.backends.mps.is_available():
        print("MPS is available")
        device = "mps"
    else:
        print("MPS not available")
        device = -1
except:
    device = -1

print(f"Testing pipeline with device={device}")

try:
    model_name = "tasksource/deberta-small-long-nli"
    # Load model and tokenizer explicitly to avoid pipeline defaults
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    # Move model to MPS if device is mps
    if device == "mps":
        model.to(torch.device("mps"))

    # If we pass model object, pipeline ignores 'device' arg usually, or we should pass device=None or similar?
    # Actually pipeline documentation says if model is passed, device argument is ignored? No, it says "device (int, optional, defaults to -1) — Device ordinal for CPU/GPU supports. Setting this to -1 will leverage CPU, a positive will run the model on the associated CUDA device id."
    # It doesn't explicitly mention "mps" string support in older docs, but newer ones do.
    
    # Let's try passing device="mps" to pipeline
    classifier = pipeline("zero-shot-classification", model=model, tokenizer=tokenizer, device=device)
    print("Pipeline created successfully")
    
    result = classifier("This is a test", candidate_labels=["a", "b"])
    print(result)
    print(f"Model device: {classifier.model.device}")

except Exception as e:
    print(f"Error: {e}")
