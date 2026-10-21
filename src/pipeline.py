"""Hierarchical ICD-10-CM coding with one LLM.

note -> diagnoses (+evidence) -> chapters -> sections -> [drill down only while > MAX_CODES codes] -> final code

All choices are presented as numbered options (neutral ids); Python maps the numbers back to ICD nodes,
so constrained decoding never has to follow ICD-like prefixes.
"""
import difflib
import re
import time

from src import config, prompts
from src.catalog import get_catalog
from src.llm import LLM


# Normalize whitespace/quotes so evidence can be compared with the note
def _norm(s):
    return re.sub(r"\s+", " ", s).strip().strip('"\'״׳ .')


def _plain(desc):
    """Drop the code range from chapter/section titles: 'Diabetes mellitus (E08-E13)' -> 'Diabetes mellitus'."""
    return re.sub(r"\s*\([A-Z][0-9A-Z.]*(-[A-Z][0-9A-Z.]*)?\)\s*$", "", desc)


def verify_evidence(evidence, note):
    """Return (evidence, exact). Non-verbatim evidence is snapped to the closest line of the note."""
    if evidence and _norm(evidence) in _norm(note):
        return _norm(evidence), True
    lines = [l.strip() for l in note.splitlines() if l.strip()]
    best = max(lines, key=lambda l: difflib.SequenceMatcher(None, evidence or "", l).ratio())
    return best, False


# The hierarchical coder: one instance holds the catalog and the LLM client
class Coder:
    def __init__(self, llm=None):
        self.cat = get_catalog()
        self.llm = llm or LLM()

    # Shared helper for steps 2-4: show numbered options, constrain the answer to valid numbers
    def choose(self, ctx, what, nodes, labels, k):
        """Ask the model to pick up to k of the numbered options; returns the chosen nodes (or None on failure)."""
        options = "\n".join(f"{i}. {label}" for i, label in enumerate(labels, 1))
        # JSON schema: a list of 1..k option numbers, each one of the shown numbers
        schema = {"type": "object", "required": ["selected"], "properties": {"selected": {
            "type": "array", "items": {"type": "integer", "enum": list(range(1, len(nodes) + 1))},
            "minItems": 1, "maxItems": k}}}
        out = self.llm.ask(prompts.CHOOSE_SYSTEM.format(what=what, k=k),
                           prompts.DX_USER.format(**ctx, options=options), schema)
        if out is None:
            return None
        # Map numbers back to ICD nodes (deduplicated, at most k)
        return [nodes[i - 1] for i in dict.fromkeys(out["selected"])][:k]

    # Step 2a: diagnoses + evidence
    def extract(self, visit):
        schema = {"type": "object", "required": ["diagnoses"], "properties": {"diagnoses": {
            "type": "array", "maxItems": config.MAX_DIAGNOSES, "items": {
                "type": "object", "required": ["diagnosis", "evidence"],
                "properties": {"diagnosis": {"type": "string"}, "evidence": {"type": "string"}}}}}}
        out = self.llm.ask(prompts.EXTRACT_SYSTEM, prompts.EXTRACT_USER.format(**visit), schema)
        return (out or {"diagnoses": []})["diagnoses"][: config.MAX_DIAGNOSES]

    # Step 2b: chapters (each shown with its section titles)
    def select_chapters(self, ctx):
        chapters = self.cat.chapters
        labels = [f"{_plain(c.desc)}. Sections: {'; '.join(_plain(s.desc) for s in c.children)}" for c in chapters]
        return self.choose(ctx, "chapters", chapters, labels, config.MAX_CHAPTERS) or []

    # Step 2c: sections of the chosen chapters (each shown with its category titles)
    def select_sections(self, ctx, chapters):
        sections = [s for c in chapters for s in c.children]
        if len(sections) <= 1:
            return sections
        labels = [f"{_plain(s.desc)} [chapter: {_plain(s.parent.desc)}]. Includes: "
                  f"{'; '.join(c.desc for c in s.children)}" for s in sections]
        return self.choose(ctx, "sections", sections, labels, config.MAX_SECTIONS) or []

    # Steps 3-4: drill down the hierarchy only while there are too many codes
    def narrow(self, ctx, nodes, trace):
        depth = 0
        # Go one level deeper only while the selected nodes hold more than MAX_CODES billable codes
        while sum(n.n_codes for n in nodes) > config.MAX_CODES and depth < config.MAX_DEPTH:
            # Options = children of the selected nodes (a billable code stays as itself)
            options = [c for n in nodes for c in ([n] if n.is_code else n.children)]
            labels = [f"{o.id} {o.desc} [within: {o.parent.label()}]" for o in options]
            chosen = self.choose(ctx, "groups", options, labels, config.MAX_CHILDREN)
            if chosen is None:  # model failed: stop here rather than guess
                trace.append({"n_options": len(options), "selected": [], "n_codes_after": 0, "failed": True})
                return []
            nodes = chosen
            trace.append({"n_options": len(options), "selected": [n.id for n in nodes],
                          "n_codes_after": sum(n.n_codes for n in nodes)})
            depth += 1
        # Few enough codes: they become the final candidate list
        return self.cat.codes_under(nodes)

    # Step 5: final code (0 = none of the candidates fits)
    def select_code(self, ctx, candidates):
        if not candidates:
            return None, "low"
        # Number the candidate codes; option 0 lets the model reject them all
        options = "0. none of these codes fits\n" + "\n".join(
            f"{i}. {c.id} {c.desc}" for i, c in enumerate(candidates, 1))
        schema = {"type": "object", "required": ["choice", "confidence"], "properties": {
            "choice": {"type": "integer", "enum": list(range(len(candidates) + 1))},
            "confidence": {"type": "string", "enum": list(config.CONFIDENCE_SCORE)}}}
        out = self.llm.ask(prompts.FINAL_SYSTEM, prompts.DX_USER.format(**ctx, options=options), schema)
        if not out or out["choice"] == 0:
            return None, (out or {}).get("confidence", "low")
        return candidates[out["choice"] - 1], out["confidence"]

    # Full pipeline for one visit: extract diagnoses, then code each one top-down
    def predict(self, visit):
        t0, calls0 = time.time(), self.llm.calls
        note = visit["note_text"]
        trace, predictions = [], {}
        for dx in self.extract(visit):
            # Check the evidence quote against the note before using it
            evidence, exact = verify_evidence(dx["evidence"], note)
            ctx = {**visit, "diagnosis": dx["diagnosis"], "evidence": evidence}
            chapters = self.select_chapters(ctx)
            sections = self.select_sections(ctx, chapters)
            # Record every step in a trace (used by the evaluation and ?debug=true)
            t = {"diagnosis": dx["diagnosis"], "evidence": evidence, "evidence_exact": exact,
                 "chapters": [c.id for c in chapters], "sections": [s.id for s in sections],
                 "n_codes_sections": sum(s.n_codes for s in sections), "narrowing": []}
            candidates = self.narrow(ctx, sections, t["narrowing"])
            t["candidates"] = [c.id for c in candidates]
            node, confidence = self.select_code(ctx, candidates)
            t.update(code=node.id if node else "NONE", confidence=confidence)
            trace.append(t)

            # Keep only valid billable codes; if two diagnoses give the same code, keep the higher score
            if node is None or not self.cat.is_billable(node.id):
                continue
            score = config.CONFIDENCE_SCORE[confidence]
            if node.id not in predictions or score > predictions[node.id]["score"]:
                predictions[node.id] = {"code": node.id, "description": node.desc, "score": score,
                                        "evidence": evidence, "evidence_verbatim": exact}
        # Predictions sorted by score, plus the trace and cost of this visit
        return {
            "visit_id": visit.get("visit_id"),
            "predictions": sorted(predictions.values(), key=lambda p: -p["score"]),
            "trace": trace,
            "llm_calls": self.llm.calls - calls0,
            "seconds": round(time.time() - t0, 2),
        }
