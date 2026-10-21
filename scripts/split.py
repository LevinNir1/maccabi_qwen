"""Deterministic dev/test split of the annotated visits. Test is held out until the approach is frozen."""
import json
import random

from src import config
from src.data import load_gold

# Visits used for design decisions; the rest is the held-out test set
DEV_SIZE = 150

if __name__ == "__main__":
    # Shuffle the annotated visit ids with a fixed seed so the split is reproducible
    ids = sorted(load_gold())
    random.Random(42).shuffle(ids)
    split = {"dev": sorted(ids[:DEV_SIZE]), "test": sorted(ids[DEV_SIZE:])}
    # Save the split for the evaluation script
    out = config.ROOT / "splits.json"
    out.write_text(json.dumps(split, indent=1))
    print({k: len(v) for k, v in split.items()}, "->", out)
