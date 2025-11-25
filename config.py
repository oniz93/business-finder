import os
import re

# --- File Paths ---
# Use absolute paths for robustness
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, "reddit", "raw")
PROCESSED_DATA_DIR = "/Volumes/2TBSSD/reddit/processed"
INTERMEDIATE_DATA_DIR = "/Volumes/2TBSSD/reddit/intermediate"

# --- Multiprocessing ---
# N_WORKERS = os.cpu_count()
N_WORKERS = 1
NLP_PROCESS_COUNT = 4

# --- Data Processing ---
CHUNK_SIZE = 300000  # Number of lines to process in each chunk

# --- Filtering Keywords and Patterns (ported from old script) ---
IDEA_KEYWORDS = [
    "idea", "solution", "concept", "opportunity", "build", "create", 
    "develop", "imagine", "what if", "improve", "new way", "innovate"
]

# Pre-compile for efficiency
IDEA_KEYWORD_PATTERN_STRING = "|".join(IDEA_KEYWORDS)

# Red flags that indicate low-quality "ideas"
EXCLUDE_PATTERNS = [
    r"why doesn't someone",     # Pure speculation
    r"wouldn't it be cool if",  # Fantasy thinking
    r"in a perfect world",      # Unrealistic
    r"they should just",        # Passive complaining
    r"if I won the lottery",    # Not serious
    r"magical solution",
    r"cure for cancer",         # Too ambitious/vague
    r"world peace",
    r"free .* for everyone"     # Economically naive
]

# Store the uncompiled regex string for Polars
EXCLUDE_PATTERN_STRING = "|".join(EXCLUDE_PATTERNS)
