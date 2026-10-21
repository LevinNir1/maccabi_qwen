# ClinicalNote2Diagnoses — hierarchical ICD-10-CM coding with one local LLM

A small POC that receives a Hebrew outpatient visit and suggests ICD-10-CM codes, each with a score and
supporting evidence taken from the note. One local LLM (Qwen via Ollama) walks down the official ICD-10-CM
hierarchy (chapter → section → category → code); parsing, counting, filtering and validation are plain Python.
After the Docker image is built, everything runs offline.

**ICD-10-CM release:** FY2027 Tabular List XML (`data/icd10cm-tabular-2027.xml`, CDC/NCHS) — chosen because the
visit dates (Oct 2026 – Sep 2027) fall in fiscal year 2027.

## Quick start (Docker, one command)

```bash
docker compose up --build                          # default model: Qwen3-4B
MODEL=qwen3.5:9b-q8_0 docker compose up --build    # alternative: Qwen3.5-9B (more accurate, slower)
```

The model is downloaded **once, during the build** — the only step that needs internet; the container then runs
fully offline. `MODEL` is the only setting to change between models (it is passed to the build and to the API;
keep `--build` when switching, because the model is baked into the image). Docker Desktop memory: ≥ 10 GB for
Qwen3-4B, ≥ 16 GB for Qwen3.5-9B (Settings → Resources).

```bash
curl -s localhost:8000/health
# {"status":"ok","model":"qwen3:4b-instruct-2507-q8_0","icd10cm_release":"FY2027"}

curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' -d @docs/demo_visit.json
```

Only `note_text` is required; the other fields of a `visits.csv` row are optional context (extra fields are
ignored, so a whole row can be sent). `docs/demo_visit.json` is a made-up visit (diabetes symptoms with HbA1c 8.1%,
plus right-knee pain with joint-space narrowing on X-ray). Actual response (Qwen3-4B):

```json
{"visit_id": "DEMO1", "predictions": [
  {"code": "E11.9", "description": "Type 2 diabetes mellitus without complications", "score": 0.9, "evidence": "בבדיקות הדם: HbA1c 8.1% וסוכר בצום 168", "evidence_verbatim": true},
  {"code": "M17.11", "description": "Unilateral primary osteoarthritis, right knee", "score": 0.9, "evidence": "הממצא המחזק: צילום מראה היצרות של המרווח המפרקי בברך ימין", "evidence_verbatim": true}]}
```

- `score`: the model's stated confidence in the final code (high/medium/low → 0.9/0.6/0.3) — a ranking aid, **not**
  a calibrated probability.
- `evidence`: always text from the note. `evidence_verbatim: true` = the exact phrase the model quoted;
  `false` = the model's quote did not match the note exactly, so the closest whole line of the note is returned.
- `?debug=true` adds the full step-by-step trace, the number of model calls and seconds. API docs: `/docs`.
- Every prompt and the model's answer at each step for this demo visit: [docs/example_flow.md](docs/example_flow.md).

### Time per visit

| Model              | Native Python (Mac M1 Max GPU) | Docker on the same Mac (CPU only)                                                                                 |
| ------------------ | ------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| Qwen3-4B (default) | ~18–19 s                       | ~18 min (measured on one 3-diagnosis visit)                                                                       |
| Qwen3.5-9B         | ~39–42 s                       | not measured (image built and checked offline: starts and serves the 9B, no prediction run); expected 2–3× the 4B |

**Why Docker is so slow on a Mac:** Docker Desktop runs containers inside a Linux virtual machine, and the Apple GPU
(reachable only through Apple's Metal API) is not passed into that VM — so Ollama in the container runs the model on
the CPU, where reading the 3–5k-token prompts is ~20 tokens/s. On a Linux machine with an NVIDIA GPU the same image
can use the GPU (see [EVALUATION.md](EVALUATION.md#speed)). On a Mac, the native run below uses the GPU:

```bash
ollama pull qwen3:4b-instruct-2507-q8_0            # or qwen3.5:9b-q8_0
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn src.api:app --port 8000          # MODEL=qwen3.5:9b-q8_0 .venv/bin/uvicorn ... for the 9B
```

## Inputs and outputs

There are two ways to run it. Both call the model through Ollama (on your machine for a native run, inside the
container for Docker) with the same Python code.

**1. API — inference for one visit**

- Start: `docker compose up --build`, or natively `uvicorn src.api:app --port 8000`.
- Input: `POST /predict` with one visit as JSON — `note_text` is required; age, sex, specialty, visit type etc. are
  optional (example: `docs/demo_visit.json`).
- Output: the HTTP response —
  `{"visit_id", "predictions": [{"code", "description", "score", "evidence", "evidence_verbatim"}]}`;
  `?debug=true` also returns the step-by-step trace, the number of model calls and seconds.
- Nothing is saved: the API returns the result to the caller.

**2. Evaluation script — many visits plus metrics**

- Start: `python -m scripts.evaluate --split test --n 100 --name my_run`.
- Input: `data/visits.csv` (visits), `splits.json` (which visit ids are dev / test),
  `data/physician_annotations.csv` (gold codes), and `data/icd10cm-tabular-2027.xml` (the ICD catalog, used by both
  modes).
- Output, written to `runs/`:
  - `runs/<name>.jsonl` — one line per visit (the same structure as the API response, plus the full trace and
    timing), written as soon as each visit finishes; an interrupted run resumes from where it stopped;
  - `runs/<name>_match.json` — cached links between gold codes and extracted diagnoses (from the eval-only judge);
  - `runs/<name>_report.md` — the full report (metrics, per-step analysis, failure examples), also printed.
- `--report-only` rebuilds the report from the saved `.jsonl` without calling the model.

## How it works

```
Hebrew note ─► 1. extract diagnoses: English term + supporting text from the note        (1 LLM call)
              for each diagnosis:
               ─► 2. choose ≤3 of the 22 Chapters (each shown with its section titles)     (1 call)
               ─► 3. choose ≤3 Sections of those chapters (each shown with its categories) (1 call)
               ─► 4. if > MAX_CODES (100) billable codes remain: choose ≤3 categories,
                     and repeat one level deeper until ≤ 100                               (0–2 calls)
               ─► 5. choose 1 code from the ≤ 100 candidates, or "none fits" + confidence  (1 call)
              ─► validate codes against the catalog, check evidence against the note, deduplicate
```

- `src/catalog.py` parses the XML into the official hierarchy: 22 chapters, 285 sections, 74,955 billable codes
  (7th-character extensions expanded). No custom categories.
- Every choice is made over **numbered options** with a JSON-schema-constrained answer, and Python maps the numbers
  back to ICD nodes — so the model can only return official, billable codes.
- The category step runs only when needed, and the candidate list is never silently truncated.
- Settings (`MODEL`, `MAX_CODES`, `MAX_CHAPTERS`, `MAX_SECTIONS`, …) are in `src/config.py`.
- The exact prompts and the model's answer at every step, for one demo visit: [docs/example_flow.md](docs/example_flow.md).

### How the answer structure is enforced

- **Constrained decoding.** Every call sends Ollama a JSON schema (the `format` field), and Ollama only lets the
  model generate tokens that keep the output valid against it — so the answer is always JSON with the required
  fields:
  - choice steps: `{"selected": [...]}` — 1–3 integers, each one of the shown option numbers (an `enum`), so the
    model cannot pick an option that does not exist;
  - final step: `"choice"` must be a candidate number or 0 ("none fits"), and `"confidence"` one of
    `high` / `medium` / `low`;
  - extraction: a list of at most 6 `{"diagnosis", "evidence"}` objects.
- **Python checks again.** It maps the numbers back to ICD nodes, drops duplicate selections, validates that the
  final code is billable in the FY2027 catalog, and checks the evidence against the note.
- **Safety net.** If an answer is cut off and is not valid JSON, the call is retried once; if it fails again, that
  step is skipped rather than guessed. Answers are capped at 600 tokens to prevent runaway generation.

## Approach in my own words

My explanation of the approach, the flow, the experiments, the evaluation and the conclusions, written in my own
words: [my_own_words.md](my_own_words.md).

## Data exploration (EDA)

[`notebooks/eda.ipynb`](notebooks/eda.ipynb) explores the visits, the physician annotations and the ICD-10-CM
hierarchy, and links each finding to a design choice. It is saved with its outputs (charts and numbers only, no
note text), so it can be read on GitHub without the data. Key findings:

- Notes are short (median 265 characters) → the whole note goes into every prompt, no chunking or retrieval.
- Physicians agree strongly (identical code sets in 80% of visits, pairwise F1 0.94–0.96) → majority vote is the gold
  standard, and their agreement is the human ceiling.
- About half the visits have 2–3 codes → the output is a list of codes per visit; evaluation is per visit.
- Long tail: 493 different codes, 282 appear once, 77% of test codes never appear in dev → no training; the model
  works zero-shot over the full official catalog.
- 36% of sections hold more than 100 billable codes (largest: 5,118) → the category step runs only above
  `MAX_CODES = 100`.
- Visit dates run Oct 1, 2026 – Sep 30, 2027 → the FY2027 release.

To re-run it: copy the provided CSVs into `data/`, `pip install -r requirements-eda.txt`, then open the notebook.

## Evaluation (summary — full results in [EVALUATION.md](EVALUATION.md))

- **Gold standard:** no single gold label is given, so a code is gold when ≥ 2 of the 3 physicians assigned it.
  Physicians agree strongly (pairwise exact-code F1 0.94–0.96 over all 510 annotated visits) — that is the human ceiling.
- **When physicians disagree:** the vote is per code, not per visit. Codes given by only one physician are dropped
  (19 of 793 (visit, code) pairs; 678 were unanimous, 96 had 2 votes). Every visit keeps at least one gold code, and
  ties cannot happen with 3 voters. A lenient check, "precision vs any physician", credits a code if any single
  physician gave it (9B: 0.448 vs 0.431 strict).
- **Split:** the 510 annotated visits were split once (seed 42) into dev 150 / test 360. Nothing is trained; dev
  (its first 40 visits) was used only to compare designs, prompts and models. The configuration was then frozen
  and both models were run on the same first 100 test visits (fixed in advance; the other test visits were not used
  because of time).
- **Metrics:** exact-code precision/recall/F1 per visit, a lenient 3-character-category F1, recall at every step
  (chapter, section, category, final list), the step where each missed code was lost, options shown per step,
  confidence analysis, seen vs unseen codes, evidence quality and time per visit.

| Data                      | Model          | Exact-code P / R / **F1**          | 3-char F1 | Section recall | s/visit (native) |
| ------------------------- | -------------- | ---------------------------------- | --------- | -------------- | ---------------- |
| dev, 40 visits            | Qwen3-4B       | 0.31 / 0.30 / **0.30**             | 0.45      | 0.60           | 18               |
| dev, 40 visits            | Qwen3.5-9B     | 0.64 / 0.67 / **0.65**             | 0.76      | 0.87           | 39               |
| **test, same 100 visits** | **Qwen3-4B**   | 0.28 / 0.29 / **0.29** [0.22–0.35] | 0.41      | 0.58           | 19               |
| **test, same 100 visits** | **Qwen3.5-9B** | 0.43 / 0.50 / **0.46** [0.39–0.54] | 0.63      | 0.82           | 42               |

Brackets: 95% bootstrap confidence interval. On the same 100 test visits, Qwen3.5-9B is better by **+0.18 F1**
(95% CI +0.10 to +0.26) and finds more gold codes in 37 visits vs fewer in 8. Dev scores were optimistic (small,
used for design); the test numbers are the estimate. Full per-step metrics: [EVALUATION.md](EVALUATION.md).

**"None fits" answers:** at the final step the model may reject all candidates (option 0). On the 100 test visits
this happened for 18 of 181 diagnoses with Qwen3-4B (10%) and 7 of 190 with Qwen3.5-9B (4%) — always the model's
own choice, never an empty list or a failed call. It mostly avoids a wrong code when the correct one was not in
the list (an earlier step went wrong, or the diagnosis was extra); only the 9B rejected a list that contained the
gold code (2 times). Details in [EVALUATION.md](EVALUATION.md).

**Visits with no code:** every annotated visit has at least one gold code (the only unlabeled visits are the 90
unannotated ones), so an empty output is always a miss. Each model returned no code for 5 of the 100 test visits:
Qwen3-4B because it answered "none fits" for all their diagnoses, Qwen3.5-9B in 3 cases because it extracted no
diagnosis at all. V0038 (gold Z01.810, an encounter for a pre-procedure examination) failed with both — administrative
"encounter" codes are hard for this pipeline. Details in [EVALUATION.md](EVALUATION.md).

**Strengths:** every returned code is a valid billable FY2027 code; evidence always comes from the note; each
prediction has a readable trace (chapter → section → category → code), so errors can be located; the hierarchy
narrows 74,955 codes to a median of ~30–35 candidates, and once the diagnosis and section are right the category
step keeps the gold code ~88% of the time (9B); runs offline
with one small model.

**Main findings:** (1) giving a 4B model a flat list of 285 sections failed (section recall 0.32); a chapter step plus
neutral numeric option ids nearly doubled it. (2) Many errors come from Hebrew medical comprehension (e.g. "tonsils"
read as "chest pain"), not from the hierarchy: with the identical pipeline, Qwen3.5-9B extracts more diagnoses
(0.86 vs 0.74) and keeps the right section far more often (0.82 vs 0.58). A targeted prompt change did not help.
(3) With the 9B, the largest remaining loss is the final choice among candidates (mostly specificity), then
extraction; it also predicts slightly too many codes (1.74 per visit vs 1.50 gold), so precision < recall.
(4) Visits with more diagnoses are harder: 9B micro F1 is 0.53 / 0.45 / 0.33 for visits with 1 / 2 / 3 gold codes,
and no 3-code visit is coded completely; of the 42 multi-code visits the 9B gets all codes right in 8, some in 24
and none in 10 (per-visit metrics in EVALUATION.md).

## Assumptions and limitations

- **Gold = majority vote** of 3 physicians. 7 annotated codes are not billable in FY2027 (e.g. `G35`, `I47.1` are
  now parent codes); the system outputs only billable codes, so these can never match and are counted as misses.
- **Errors compound:** chapter/section/category choices are hard filters — a wrong early choice cannot be recovered.
- **Model choice is a trade-off:** Qwen3-4B is the default because it is faster and fits a typical Docker memory
  limit, but it misreads Hebrew medical terms; Qwen3.5-9B is much more accurate and ~2× slower.
- **Score** is the model's own confidence, not calibrated; in practice almost all codes get "high", so it barely
  separates right from wrong (see EVALUATION.md). No threshold is applied.
- **Specificity** errors remain at the final step (e.g. "unspecified" vs a documented site or episode), and one
  problem is sometimes extracted twice, giving an extra neighbouring code.
- **Evidence:** ~86% is the model's exact quote; otherwise the closest note line is returned. Clinical support of
  the evidence was checked by manual review of examples, not measured automatically.
- **Speed:** ~8 model calls per visit; Docker on a Mac has no GPU access (minutes per visit). Docker image ≈ 15.5 GB
  with Qwen3-4B, ≈ 27 GB with Qwen3.5-9B (Ollama base image + model, baked in for offline use).
- **Data:** the notes look template-generated (each problem = complaint + supporting finding), so results may not
  transfer to real free-text notes. Design decisions used only 40 dev visits; the test numbers are the estimate.
- **Test scope:** both models were tested on the same 100 of the 360 test visits (time constraints), so the
  confidence intervals are wide (±0.07 F1). The 90 unannotated visits were used only for manual demos.

## Repository layout

```
src/config.py        settings: MODEL, MAX_CODES=100, ...
src/catalog.py       XML → official hierarchy and billable codes
src/prompts.py       prompt templates
src/llm.py           small Ollama client (JSON-schema constrained, temperature 0)
src/pipeline.py      the hierarchical coder
src/api.py           FastAPI app (/predict, /health)
src/data.py          visits, annotations, majority-vote gold
scripts/split.py     dev/test split → splits.json
scripts/evaluate.py  run + report:  python -m scripts.evaluate --split dev --n 40 --name my_run
runs/                saved per-visit results and reports of every run
Dockerfile, docker-compose.yml, docker/entrypoint.sh   offline container
EVALUATION.md        full evaluation results
my_own_words.md      the approach in my own words
notebooks/eda.ipynb  data exploration: the facts behind each design choice (saved with outputs)
docs/example_flow.md every prompt and model answer for one demo visit (docs/demo_visit.json)
```

The provided assignment data (`visits.csv`, `physician_annotations.csv`) is not included; copy it into `data/` to
re-run the evaluation (the API and Docker image need only the ICD-10-CM XML, which is included).
