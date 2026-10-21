"""Run the pipeline on a split and report stage-wise metrics.

    python -m scripts.evaluate --split dev --n 40 --name dev40
Results are cached per visit in runs/<name>.jsonl (re-running resumes); the report goes to runs/<name>_report.md.

Error attribution links every gold code to the extracted diagnosis it corresponds to (or none). That link is
made by an eval-only Qwen call ("which extracted diagnosis is this?"), cached in runs/<name>_match.json.
"""
import argparse
import json
from collections import Counter
from itertools import combinations
from statistics import mean

from src import config
from src.catalog import get_catalog
from src.data import load_annotations, load_gold, load_visits

# Prompt for the eval-only judge that links a gold code to an extracted diagnosis
MATCH_SYSTEM = """You compare diagnoses. A physician coded a clinical visit with an ICD-10-CM code. An automatic system extracted a list of diagnoses from the same note.
Which extracted diagnosis refers to the same clinical problem as the physician's code (even if worded differently, or more or less specific)? Answer 0 if none of them does.
Respond only with JSON: {"match": <number>}"""


# Micro precision / recall / F1 over visits
def prf(pairs):
    """pairs: list of (pred_set, gold_set) -> micro precision, recall, F1"""
    tp = sum(len(p & g) for p, g in pairs)
    n_p, n_g = sum(len(p) for p, _ in pairs), sum(len(g) for _, g in pairs)
    P, R = tp / max(n_p, 1), tp / max(n_g, 1)
    return P, R, 2 * P * R / max(P + R, 1e-9)


def fmt(P, R, F):
    return f"P={P:.3f} R={R:.3f} F1={F:.3f}"


# Run the pipeline on the first n visits of a split, appending each result to runs/<name>.jsonl
def run(split, n, name, workers=1):
    """With workers > 1, visits are processed concurrently (needs OLLAMA_NUM_PARALLEL >= workers);
    per-visit seconds then include queueing, so throughput is reported from wall-clock time."""
    import threading
    import time
    from concurrent.futures import ThreadPoolExecutor
    from src.pipeline import Coder
    ids = json.loads((config.ROOT / "splits.json").read_text())[split][:n]
    path = config.ROOT / "runs" / f"{name}.jsonl"
    # Resume: skip visits already saved
    done = {json.loads(l)["visit_id"] for l in path.open()} if path.exists() else set()
    todo = [vid for vid in ids if vid not in done]
    visits, local, lock, t0 = load_visits(), threading.local(), threading.Lock(), time.time()

    # Process one visit and save it immediately (so an interrupted run loses nothing)
    def work(vid):
        if not hasattr(local, "coder"):
            local.coder = Coder()  # one per thread: keeps call counting per visit correct
        res = local.coder.predict(visits[vid])
        with lock:
            f.write(json.dumps(res, ensure_ascii=False) + "\n")
            f.flush()
            print(f"[{len(done) + 1}/{len(ids)}] {vid} {res['seconds']}s calls={res['llm_calls']} "
                  f"pred={[p['code'] for p in res['predictions']]}")
            done.add(vid)

    with path.open("a") as f, ThreadPoolExecutor(workers) as pool:
        list(pool.map(work, todo))
    if todo:
        print(f"wall-clock: {time.time() - t0:.0f}s for {len(todo)} visits "
              f"= {(time.time() - t0) / len(todo):.1f}s/visit throughput with {workers} workers")
    results = [json.loads(l) for l in path.open()]
    return [r for r in results if r["visit_id"] in set(ids)]


# Link each gold code to the extracted diagnosis it corresponds to (for error attribution)
def match_gold_to_diagnoses(results, name):
    """{visit_id|code: index of the matching extracted diagnosis, or -1}. Eval-only LLM call, cached."""
    from src.llm import LLM
    path = config.ROOT / "runs" / f"{name}_match.json"
    cache = json.loads(path.read_text()) if path.exists() else {}
    cat, gold, visits, llm = get_catalog(), load_gold(), load_visits(), LLM(model=config.JUDGE_MODEL)
    for r in results:
        dxs = [t["diagnosis"] for t in r["trace"]]
        for code in gold[r["visit_id"]]:
            key = f"{r['visit_id']}|{code}"
            if key in cache:
                continue
            if not dxs:
                cache[key] = -1
                continue
            node = cat.nodes.get(code)
            user = (f"Note:\n{visits[r['visit_id']]['note_text']}\n\nPhysician's code: {code} "
                    f"{node.desc if node else ''}\n\nExtracted diagnoses:\n"
                    + "\n".join(f"{i}. {d}" for i, d in enumerate(dxs, 1)))
            schema = {"type": "object", "required": ["match"],
                      "properties": {"match": {"type": "integer", "enum": list(range(len(dxs) + 1))}}}
            out = llm.ask(MATCH_SYSTEM, user, schema)
            cache[key] = (out["match"] - 1) if out else -1
    path.write_text(json.dumps(cache, indent=1))
    return cache


# Report section: per-visit (multi-label) metrics, overall and split by the number of gold codes in the visit
def per_visit_details(results, gold):
    L = []
    pr = L.append

    def visit_scores(rs):
        rows = []
        for r in rs:
            p, g = {x["code"] for x in r["predictions"]}, gold[r["visit_id"]]
            tp = len(p & g)
            rows.append({"P": tp / len(p) if p else 0.0, "R": tp / len(g), "F1": 2 * tp / (len(p) + len(g)),
                         "jaccard": tp / len(p | g), "exact": p == g, "all": g <= p, "any": tp > 0, "n_pred": len(p)})
        return {k: mean(row[k] for row in rows) for k in rows[0]}

    s = visit_scores(results)
    pr("\n## Per-visit (multi-label) metrics")
    pr("Micro P/R/F1 above pools all (visit, code) pairs; here every visit counts once.")
    pr(f"- Per-visit average: P={s['P']:.3f} R={s['R']:.3f} F1={s['F1']:.3f} Jaccard={s['jaccard']:.3f}")
    pr(f"- Exact set match {s['exact']:.2f}; all gold codes found {s['all']:.2f}; at least one found {s['any']:.2f}")
    pr("\n| Gold codes in visit | Visits | Micro P / R / F1 | Per-visit F1 | Exact set match | Gold found: all / some / none (visits) | Codes predicted per visit |")
    pr("|---|---|---|---|---|---|---|")
    for k in sorted({len(gold[r["visit_id"]]) for r in results}):
        rs = [r for r in results if len(gold[r["visit_id"]]) == k]
        P, R, F = prf([({x["code"] for x in r["predictions"]}, gold[r["visit_id"]]) for r in rs])
        v = visit_scores(rs)
        hits = [len({x["code"] for x in r["predictions"]} & gold[r["visit_id"]]) for r in rs]
        found = f"{sum(h == k for h in hits)} / {sum(0 < h < k for h in hits)} / {sum(h == 0 for h in hits)}"
        pr(f"| {k} | {len(rs)} | {P:.3f} / {R:.3f} / {F:.3f} | {v['F1']:.3f} | {v['exact']:.2f} | {found} | {v['n_pred']:.2f} |")
    return L


# Report section: paths taken, options shown, step accuracy, confidence analysis
def step_details(results, match, gold, chapters_of):
    """Per-step view: which path each diagnosis took, how many options the model saw at each step,
    step accuracy (conditional on the previous step being right), and what the final confidence is worth."""
    cat, L = get_catalog(), []
    pr = L.append
    traces = [t for r in results for t in r["trace"]]
    stats = lambda xs: f"mean {mean(xs):.1f}, median {sorted(xs)[len(xs) // 2]}, max {max(xs)}" if xs else "n/a"

    def top_group(code):  # the node directly under the section (a category, or a 3-character billable code)
        n = cat.codes[code]
        while n.parent.kind != "section":
            n = n.parent
        return n.id

    # Path: straight from section to code, or through category (and deeper) narrowing
    direct = [t for t in traces if not t["narrowing"]]
    narrowed = [t for t in traces if t["narrowing"]]
    pr("\n## Step-by-step details")
    pr(f"\n### Path per extracted diagnosis (MAX_CODES = {config.MAX_CODES})")
    pr(f"- Section → code directly (≤ {config.MAX_CODES} codes under the chosen sections): "
       f"{len(direct)}/{len(traces)} ({len(direct) / len(traces):.0%})")
    pr(f"- Section → category (→ deeper) → code (> {config.MAX_CODES} codes): {len(narrowed)}/{len(traces)} "
       f"({len(narrowed) / len(traces):.0%}); narrowing levels used: "
       f"{dict(sorted(Counter(len(t['narrowing']) for t in narrowed).items()))}")
    pr(f"- Codes under the chosen sections — direct path: {stats([t['n_codes_sections'] for t in direct])}; "
       f"narrowed path: {stats([t['n_codes_sections'] for t in narrowed])}")

    # How many options the model saw at each step
    pr("\n### Options shown to the model at each step (per diagnosis)")
    pr(f"- Chapter step: {len(cat.chapters)} options; chapters chosen: {stats([len(chapters_of(t)) for t in traces])}")
    sec_opts = [sum(len(cat.nodes[c].children) for c in chapters_of(t)) for t in traces]
    pr(f"- Section step: options {stats(sec_opts)}; sections chosen: {stats([len(t['sections']) for t in traces])}")
    for lvl in (0, 1, 2):
        lv = [t["narrowing"][lvl] for t in narrowed if len(t["narrowing"]) > lvl]
        if lv:
            name = "Category step" if lvl == 0 else f"Deeper level {lvl + 1}"
            pr(f"- {name} ({len(lv)} diagnoses): options {stats([s['n_options'] for s in lv])}; "
               f"codes left after it {stats([s['n_codes_after'] for s in lv])}")
    pr(f"- Final code step: candidates {stats([len(t['candidates']) for t in traces])} "
       f"(direct path {stats([len(t['candidates']) for t in direct])}; "
       f"narrowed path {stats([len(t['candidates']) for t in narrowed])})")

    # step accuracy, following each gold code through the diagnosis it was linked to
    c = Counter()
    for r in results:
        for code in gold[r["visit_id"]]:
            i = match.get(f"{r['visit_id']}|{code}", -1)
            if i < 0 or not cat.is_billable(code):
                continue
            t, node = r["trace"][i], cat.codes[code]
            c["linked"] += 1
            if node.ancestor("chapter").id not in chapters_of(t):
                continue
            c["chapter"] += 1
            if node.ancestor("section").id not in t["sections"]:
                continue
            c["section"] += 1
            path = "narrowed" if t["narrowing"] else "direct"
            c[f"section_{path}"] += 1
            if t["narrowing"]:
                c["category"] += top_group(code) in t["narrowing"][0]["selected"]
            if code not in t["candidates"]:
                continue
            c["candidates"] += 1
            c[f"candidates_{path}"] += 1
            c["code"] += t["code"] == code
            c[f"code_{path}"] += t["code"] == code
    f = lambda a, b: f"{c[a]}/{c[b]} = {c[a] / max(c[b], 1):.3f}"
    pr("\n### Step accuracy (gold codes whose diagnosis was extracted; each step given the previous one was right)")
    pr(f"- Chapter: gold chapter among chosen chapters: {f('chapter', 'linked')}")
    pr(f"- Section: gold section among chosen sections | chapter right: {f('section', 'chapter')}")
    pr(f"- Category: gold category kept at the category step | section right & narrowing ran: "
       f"{f('category', 'section_narrowed')}")
    pr(f"- Narrowing overall: gold still in final candidates | section right & narrowing ran: "
       f"{f('candidates_narrowed', 'section_narrowed')}")
    pr(f"- Code: correct final code | gold in candidates: {f('code', 'candidates')} "
       f"(direct path {f('code_direct', 'candidates_direct')}; narrowed path {f('code_narrowed', 'candidates_narrowed')})")
    pr(f"- End to end, for extracted diagnoses: {f('code', 'linked')}")

    # Is the confidence useful? Precision per level, and P/R/F1 if low-confidence codes were dropped
    pr("\n### Confidence (final step only; no threshold is applied by the system)")
    by_score = Counter()
    for r in results:
        g = gold[r["visit_id"]]
        for p in r["predictions"]:
            by_score[(p["score"], "n")] += 1
            by_score[(p["score"], "tp")] += p["code"] in g
    for s in sorted({k[0] for k in by_score}, reverse=True):
        label = {v: k for k, v in config.CONFIDENCE_SCORE.items()}.get(s, s)
        pr(f"- {label} ({s}): {by_score[(s, 'n')]} codes, precision {by_score[(s, 'tp')] / by_score[(s, 'n')]:.3f}")
    for thr in sorted(set(config.CONFIDENCE_SCORE.values())):
        pairs = [({p["code"] for p in r["predictions"] if p["score"] >= thr}, gold[r["visit_id"]]) for r in results]
        pr(f"- If only codes with score ≥ {thr} were returned: {fmt(*prf(pairs))}")
    return L


# Main report: final-code metrics, human ceiling, stage recalls, error attribution, cost, examples
def report(results, split, name):
    cat, gold, ann = get_catalog(), load_gold(), load_annotations()
    dev_codes = set().union(*(gold[v] for v in json.loads((config.ROOT / "splits.json").read_text())["dev"]))
    match = match_gold_to_diagnoses(results, name)
    L = []
    pr = lambda s="": L.append(s)

    def chapters_of(t):  # older runs selected sections directly; derive their chapters
        return t.get("chapters") or [cat.section_by_id[s].parent.id for s in t["sections"]]

    pairs, pairs3, any_ann_hits, n_pred = [], [], 0, 0
    stage = Counter()
    recall = Counter()  # visit-level union recalls, and recalls given the diagnosis was extracted
    fp_kind = Counter()
    seen = {True: [0, 0], False: [0, 0]}
    for r in results:
        g = gold[r["visit_id"]]
        p = {x["code"] for x in r["predictions"]}
        pairs.append((p, g))
        pairs3.append(({c[:3] for c in p}, {c[:3] for c in g}))
        any_ann_hits += len(p & set().union(*ann[r["visit_id"]].values()))
        n_pred += len(p)
        all_ch = {c for t in r["trace"] for c in chapters_of(t)}
        all_sec = {s for t in r["trace"] for s in t["sections"]}
        # Follow each gold code through the stages and record where it was lost
        for code in g:
            if not cat.is_billable(code):
                stage["0 unreachable: gold code not billable in FY2027"] += 1
                continue
            node = cat.codes[code]
            ch, sec = node.ancestor("chapter").id, node.ancestor("section").id
            recall["reachable"] += 1
            recall["chapter_any"] += ch in all_ch
            recall["section_any"] += sec in all_sec
            seen[code in dev_codes][0] += 1
            seen[code in dev_codes][1] += code in p
            i = match[f"{r['visit_id']}|{code}"]
            t = r["trace"][i] if i >= 0 else None
            if t is not None:
                recall["extracted"] += 1
                recall["chapter_given_extracted"] += ch in chapters_of(t)
                recall["section_given_extracted"] += sec in t["sections"]
                if code in t["candidates"]:
                    recall["reached_final"] += 1
                    recall["final_correct"] += t["code"] == code
            if code in p:
                stage["1 correct"] += 1
            elif t is None:
                stage["2 diagnosis never extracted"] += 1
            elif ch not in chapters_of(t):
                stage["3 extracted, wrong CHAPTER"] += 1
            elif sec not in t["sections"]:
                stage["4 extracted, right chapter, wrong SECTION"] += 1
            elif code not in t["candidates"]:
                stage["5 extracted, lost in CATEGORY/deeper narrowing"] += 1
            else:
                stage["6 reached final list, wrong FINAL choice"] += 1
        # Classify false positives: wrong specificity vs a different diagnosis
        for c in p - g:
            fp_kind["same 3-char category as a gold code (granularity)"
                    if c[:3] in {x[:3] for x in g} else "different category (extra/wrong diagnosis)"] += 1

    n_gold = sum(len(g) for _, g in pairs)
    reach = recall["reachable"]
    ratio = lambda a, b: f"{recall[a]}/{recall[b]} = {recall[a] / max(recall[b], 1):.3f}"
    pr(f"# Evaluation report — {name}: split={split}, visits={len(results)}, gold codes={n_gold} (majority ≥2/3)\n")
    # Write the report sections
    pr("## Final codes")
    pr(f"- Exact code: {fmt(*prf(pairs))}")
    pr(f"- 3-char category (lenient): {fmt(*prf(pairs3))}")
    pr(f"- Visit exact-set match: {mean(p == g for p, g in pairs):.3f}")
    pr(f"- Precision vs ANY annotator: {any_ann_hits / max(n_pred, 1):.3f}")
    pr(f"- Predicted codes per visit: {n_pred / len(results):.2f} (gold {n_gold / len(results):.2f})")
    L.extend(per_visit_details(results, gold))

    # How much the physicians agree with each other (upper bound for any system)
    pr("\n## Human ceiling (pairwise annotator agreement, same visits)")
    for a, b in combinations(["DR_A", "DR_B", "DR_C"], 2):
        pr(f"- {a} vs {b}: {fmt(*prf([(ann[r['visit_id']][a], ann[r['visit_id']][b]) for r in results]))}")

    pr("\n## Stage recalls (billable gold codes)")
    pr(f"- Chapter Recall@{config.MAX_CHAPTERS} (any diagnosis of the visit): {ratio('chapter_any', 'reachable')}")
    pr(f"- Section Recall@{config.MAX_SECTIONS} (any diagnosis of the visit): {ratio('section_any', 'reachable')}")
    pr(f"- Diagnosis extracted (matched by eval judge): {ratio('extracted', 'reachable')}")
    pr(f"- Chapter recall given extracted: {ratio('chapter_given_extracted', 'extracted')}")
    pr(f"- Section recall given extracted: {ratio('section_given_extracted', 'extracted')}")
    pr(f"- Gold reached the final candidate list: {ratio('reached_final', 'reachable')}")
    pr(f"- Final choice correct when gold reached the final list: {ratio('final_correct', 'reached_final')}")

    pr("\n## Where each gold code ends up (first failing stage)")
    for k, v in sorted(stage.items()):
        pr(f"- {k[2:]}: {v} ({v / n_gold:.1%})")

    pr("\n## False positives")
    for k, v in fp_kind.most_common():
        pr(f"- {k}: {v}")

    if split == "test":
        pr("\n## Seen (code in dev gold) vs unseen")
        for k, (n, hit) in seen.items():
            pr(f"- {'seen' if k else 'unseen'}: recall {hit}/{n} = {hit / max(n, 1):.3f}")

    traces = [t for r in results for t in r["trace"]]
    pr("\n## Validity & cost")
    all_pred = [x for r in results for x in r["predictions"]]
    pr(f"- Valid billable codes: {sum(cat.is_billable(x['code']) for x in all_pred)}/{len(all_pred)}")
    pr(f"- Evidence verbatim in note: {sum(t['evidence_exact'] for t in traces)}/{len(traces)} diagnoses "
       f"(others snapped to the closest note line)")
    pr(f"- Diagnoses extracted per visit: {len(traces) / len(results):.2f}; NONE answers: "
       f"{sum(t['code'] == 'NONE' for t in traces)}")
    pr(f"- Narrowing depth per diagnosis: {dict(sorted(Counter(len(t['narrowing']) for t in traces).items()))}")
    pr(f"- Final candidate list size: mean {mean(len(t['candidates']) for t in traces):.1f}, "
       f"max {max(len(t['candidates']) for t in traces)}")
    pr(f"- Seconds/visit: {mean(r['seconds'] for r in results):.1f}; LLM calls/visit: "
       f"{mean(r['llm_calls'] for r in results):.1f}")

    L.extend(step_details(results, match, gold, chapters_of))

    # Up to 15 visits with errors, with the full trace and the gold codes' paths
    pr("\n## Failure examples")
    visits = load_visits()
    for r in [r for r in results if {x['code'] for x in r['predictions']} != gold[r['visit_id']]][:15]:
        g = gold[r["visit_id"]]
        pr(f"\n### {r['visit_id']}  gold={sorted(g)}  pred={[x['code'] for x in r['predictions']]}")
        pr("```\n" + visits[r["visit_id"]]["note_text"] + "\n```")
        for t in r["trace"]:
            nar = " → ".join(f"{'/'.join(s['selected'])}({s['n_codes_after']})" for s in t["narrowing"])
            pr(f"- **{t['diagnosis']}** | chapters {chapters_of(t)} → sections {t['sections']} "
               f"({t['n_codes_sections']} codes){' → ' + nar if nar else ''} → {len(t['candidates'])} cands"
               f" → **{t['code']}** ({t['confidence']})")
        for code in sorted(g):
            n, i = cat.nodes.get(code), match.get(f"{r['visit_id']}|{code}", -1)
            pr(f"  - gold {code} [matched dx: {r['trace'][i]['diagnosis'] if i >= 0 else 'NONE'}]: "
               f"{n.path() if n else 'NOT IN FY2027'}")
    return "\n".join(L)


# CLI: run (or only re-score with --report-only) and write runs/<name>_report.md
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev")
    ap.add_argument("--n", type=int, default=None)
    ap.add_argument("--name", default=None)
    ap.add_argument("--report-only", action="store_true", help="re-score cached results without running the pipeline")
    ap.add_argument("--workers", type=int, default=1, help="concurrent visits (set OLLAMA_NUM_PARALLEL accordingly)")
    a = ap.parse_args()
    name = a.name or f"{a.split}{a.n or ''}"
    if a.report_only:
        ids = set(json.loads((config.ROOT / "splits.json").read_text())[a.split][:a.n])
        results = [json.loads(l) for l in (config.ROOT / "runs" / f"{name}.jsonl").open()]
        results = [r for r in results if r["visit_id"] in ids]
    else:
        results = run(a.split, a.n, name, a.workers)
    text = report(results, a.split, name)
    (config.ROOT / "runs" / f"{name}_report.md").write_text(text)
    print(text)
