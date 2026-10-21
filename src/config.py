"""All tunable settings in one place."""
import os
from pathlib import Path

# Input files (paths relative to the project root)
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
ICD_XML = DATA_DIR / "icd10cm-tabular-2027.xml"
VISITS_CSV = DATA_DIR / "visits.csv"
ANNOTATIONS_CSV = DATA_DIR / "physician_annotations.csv"

# Hierarchical narrowing
MAX_CODES = 100      # if the selected nodes contain more billable codes than this, drill one level deeper
MAX_CHAPTERS = 3     # chapters Qwen may select per diagnosis
MAX_SECTIONS = 3     # sections Qwen may select per diagnosis (within the chosen chapters)
MAX_CHILDREN = 3     # nodes Qwen may select at each drill-down level (categories, subcategories, ...)
MAX_DIAGNOSES = 6    # diagnoses extracted per visit
MAX_DEPTH = 6        # safety guard for the drill-down loop

# LLM (Ollama)
# Where the Ollama server runs, and which model it serves (MODEL is the one variable to switch models)
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL = os.environ.get("MODEL", "qwen3:4b-instruct-2507-q8_0")  # or "qwen3.5:9b-q8_0": more accurate, ~2x slower
# Decoding settings: deterministic answers, no thinking traces
TEMPERATURE = 0.0
THINK = False            # no reasoning traces (Qwen3.5 thinks by default)
JUDGE_MODEL = "qwen3:4b-instruct-2507-q8_0"  # fixed eval-only judge, independent of MODEL
# Context window (tokens) and maximum answer length per call
NUM_CTX = 16384
MAX_OUTPUT_TOKENS = 600  # guards against runaway generations under constrained decoding

# Ordinal confidence -> numeric score (a ranking aid, NOT a calibrated probability)
CONFIDENCE_SCORE = {"high": 0.9, "medium": 0.6, "low": 0.3}
