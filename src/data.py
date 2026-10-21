"""Load visits and physician annotations; build the majority-vote gold standard."""
import csv
from collections import defaultdict

from src import config


# Visits by visit_id (all CSV columns as strings)
def load_visits():
    with open(config.VISITS_CSV, encoding="utf-8-sig") as f:
        return {r["visit_id"]: r for r in csv.DictReader(f)}


# Raw annotations: which codes each physician assigned to each visit
def load_annotations():
    """visit_id -> annotator_id -> set of codes"""
    ann = defaultdict(lambda: defaultdict(set))
    with open(config.ANNOTATIONS_CSV, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            ann[r["visit_id"]][r["annotator_id"]].add(r["icd10cm_code"].strip())
    return ann


# Codes chosen by at least min_votes annotators
def majority(code_sets, min_votes=2):
    codes = set().union(*code_sets)
    return {c for c in codes if sum(c in s for s in code_sets) >= min_votes}


# Gold standard used for evaluation: majority vote of the 3 physicians
def load_gold():
    """visit_id -> set of codes chosen by >= 2 of the 3 annotators"""
    return {vid: majority(list(by_ann.values())) for vid, by_ann in load_annotations().items()}
