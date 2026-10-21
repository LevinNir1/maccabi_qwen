# Evaluation

All numbers come from `scripts/evaluate.py`; every run's per-visit results and full report (with failure
examples and step-by-step traces) are in `runs/`.

## Method

- **Gold standard.** The three physicians' codes are combined by majority vote: a code is gold when ≥ 2 of 3
  assigned it (1–3 codes per visit). Pairwise physician agreement is high (exact-code F1 0.94–0.96 over all 510 annotated visits), which is the
  human ceiling. 7 annotated codes are not billable in FY2027 and are reported as unreachable.
- **Split.** 510 annotated visits → dev 150 / test 360 (seed 42, `splits.json`). Nothing is trained. Design, prompt
  and model choices used only the first 40 dev visits. With the configuration frozen, both models were run on the
  same first 100 test visits (fixed in advance by sorted id, no overlap with dev). Because of time, the remaining
  test visits were not used, except a partial Qwen3-4B run (134 visits) used as a consistency check.
- **Unit of evaluation.** Visit level, multiple codes per visit: micro precision / recall / F1 of the predicted code
  set vs the gold set (exact code), plus a lenient version on the 3-character category.
- **Step recalls.** For each gold code: was its chapter chosen, its section chosen, did it survive the category
  (and deeper) narrowing, did it reach the final candidate list, was it chosen.
- **Where errors happen.** Each gold code is linked to the extracted diagnosis it corresponds to (an eval-only call
  to a fixed judge, Qwen3-4B, cached in `runs/*_match.json` and spot-checked by hand). That separates
  *never extracted* from *extracted but sent to the wrong chapter / section / category* and *wrong final choice*.
- **Also reported:** false-positive types (wrong specificity vs a different diagnosis), seen vs unseen codes (seen =
  code appears in dev gold), validity of codes, evidence quality, model calls and time per visit, options shown to
  the model at each step, and whether the confidence separates right from wrong.

## Development experiments (same 40 dev visits, 60 gold codes)

| Configuration                                   | Diagnosis extracted | Chapter R@3 | Section R@3 | Gold reaches final list | Final choice correct (given reached) | **Exact F1** | s/visit |
| ----------------------------------------------- | ------------------- | ----------- | ----------- | ----------------------- | ------------------------------------ | ------------ | ------- |
| Qwen3-4B, flat list of 285 sections             | 0.75                | 0.80        | 0.32        | 0.23                    | 0.57                                 | 0.17         | 14      |
| Qwen3-4B, chapter → section, numeric ids        | 0.75                | 0.85        | 0.60        | 0.42                    | 0.68                                 | 0.30         | 18      |
| … + evidence-first extraction prompt (rejected) | 0.72                | 0.88        | 0.57        | 0.38                    | 0.52                                 | 0.25         | 19      |
| **Qwen3.5-9B, chapter → section, numeric ids**  | **0.92**            | **0.97**    | **0.87**    | **0.75**                | **0.84**                             | **0.65**     | 39      |

Where the 60 gold codes ended up:

| First failing step                         | 4B flat list | 4B chapter→section | 9B chapter→section |
| ------------------------------------------ | ------------ | ------------------ | ------------------ |
| Correct                                    | 10           | 18                 | **40**             |
| Diagnosis never extracted                  | 14           | 15                 | 4                  |
| Extracted, wrong chapter                   | 14           | 5                  | 2                  |
| Extracted, right chapter, wrong section    | 14           | 9                  | 5                  |
| Lost in category / deeper narrowing        | 2            | 5                  | 3                  |
| Reached the final list, wrong final choice | 6            | 8                  | 6                  |

Findings:
1. **A flat list of 285 sections is too much for a 4B model**, and ICD-like ids break constrained decoding: when the
   model starts writing the code it has in mind ("E1…" for diabetes), the only valid id with that prefix is
   "E15-E16", so it is forced into the wrong section. A chapter step and neutral numeric ids nearly doubled section
   recall.
2. **The remaining errors were mostly Hebrew comprehension.** Qwen3-4B misread terms (שקדים "tonsils" → "chest pain",
   עגבת "syphilis" → "hepatitis B", טסיות "platelets" → "leukopenia"). A targeted extraction prompt did not fix it;
   Qwen3.5-9B, with the identical pipeline and prompts, did (more correct codes in 19 of 40 visits, fewer in 1).

## Test results (same 100 test visits for both models, 150 gold codes)

95% confidence intervals are from 2,000 bootstrap resamples of visits.

|                                        | Qwen3-4B               | Qwen3.5-9B             |
| -------------------------------------- | ---------------------- | ---------------------- |
| **Exact-code F1**                      | **0.285** [0.22, 0.35] | **0.463** [0.39, 0.54] |
| Exact-code precision / recall          | 0.277 / 0.293          | 0.431 / 0.500          |
| 3-character category F1 (lenient)      | 0.409                  | 0.625                  |
| Visits with exactly the gold code set  | 0.19                   | 0.34                   |
| Precision vs any single physician      | 0.289                  | 0.448                  |
| Codes predicted per visit (gold: 1.50) | 1.59                   | 1.74                   |
| Human ceiling (pairwise physician F1)  | 0.93–0.95              | 0.93–0.95              |

**Paired comparison:** Qwen3.5-9B − Qwen3-4B = **+0.178 F1** (95% CI +0.10 to +0.26); the 9B finds more gold codes
in 37 visits and fewer in 8. Consistency check: Qwen3-4B on 134 test visits scores F1 0.300 [0.25, 0.36], in line
with its 100-visit result.

**Dev vs test:** both models score lower on test than on the 40 dev visits (9B: 0.65 → 0.46; 4B: 0.30 → 0.29). The
dev set was small (dev 9B CI [0.54, 0.77]) and was used to choose the design, so the dev numbers were optimistic;
the test numbers are the estimate to rely on.

### Per-visit (multi-label) metrics

The main metric is **micro** P/R/F1: every (visit, code) pair is one sample, pooled over all visits. Below, every
visit counts once, and visits are split by how many gold codes they have.

|                                                  | Qwen3-4B              | Qwen3.5-9B            |
| ------------------------------------------------ | --------------------- | --------------------- |
| Micro F1 over (visit, code) pairs (main metric)  | 0.285                 | 0.463                 |
| Per-visit average P / R / F1                     | 0.309 / 0.310 / 0.302 | 0.484 / 0.532 / 0.498 |
| Per-visit Jaccard (overlap ÷ union of code sets) | 0.266                 | 0.448                 |
| Exact set match                                  | 0.19                  | 0.34                  |
| All gold codes of the visit found                | 0.21                  | 0.42                  |
| At least one gold code found                     | 0.43                  | 0.66                  |

By number of gold codes in the visit:

| Gold codes in visit | Visits | Micro F1 (4B / 9B) | Per-visit F1 (4B / 9B) | Exact set match (4B / 9B) | All gold found (4B / 9B) | Codes predicted per visit (4B / 9B) |
| ------------------- | ------ | ------------------ | ---------------------- | ------------------------- | ------------------------ | ----------------------------------- |
| 1                   | 58     | 0.35 / 0.53        | 0.33 / 0.54            | 0.31 / 0.47               | 0.34 / 0.59              | 0.98 / 1.21                         |
| 2                   | 34     | 0.26 / 0.45        | 0.27 / 0.46            | 0.03 / 0.21               | 0.03 / 0.24              | 2.06 / 2.32                         |
| 3                   | 8      | 0.21 / 0.33        | 0.22 / 0.34            | 0.00 / 0.00               | 0.00 / 0.00              | 4.00 / 3.12                         |

How many of each visit's gold codes were found (number of visits; "all" may still include extra, wrong codes —
"exact" = all found and nothing extra):

| Gold codes in visit | Visits | 4B: all / some / none found | 4B exact | 9B: all / some / none found | 9B exact |
| ------------------- | ------ | --------------------------- | -------- | --------------------------- | -------- |
| 1                   | 58     | 20 / – / 38                 | 18       | 34 / – / 24                 | 27       |
| 2                   | 34     | 1 / 16 / 17                 | 1        | 8 / 17 / 9                  | 7        |
| 3                   | 8      | 0 / 6 / 2                   | 0        | 0 / 7 / 1                   | 0        |

For multi-code visits, "some found" is the most common outcome: with the 9B, 24 of the 42 multi-code visits get some
but not all codes right, 8 get all right and 10 get none; with the 4B, 22 / 1 / 19.

- **More diagnoses → lower scores:** each extra diagnosis is another chance to miss, and no 3-code visit is coded
  completely by either model (only 8 such visits, so that row is noisy).
- **The number of codes predicted tracks the number of gold codes** (9B: 1.2 / 2.3 / 3.1), so errors are mostly
  wrong codes, not missed or invented problems.
- Per-visit averages are a little higher than micro because single-code visits, where the system does best, are the
  majority.

### Recall at each step (148 billable gold codes; 2 gold codes are not billable in FY2027)

| Step                                                             | Qwen3-4B | Qwen3.5-9B |
| ---------------------------------------------------------------- | -------- | ---------- |
| Diagnosis extracted                                              | 0.736    | 0.858      |
| Chapter Recall@3 (any diagnosis of the visit)                    | 0.872    | 0.912      |
| Section Recall@3 (any diagnosis of the visit)                    | 0.581    | 0.818      |
| Gold code reached the final candidate list                       | 0.399    | 0.649      |
| Final choice correct, given the gold code reached the final list | 0.661    | 0.729      |

### Step accuracy (gold codes whose diagnosis was extracted; each step given the previous one was right)

| Step                                                        | Qwen3-4B      | Qwen3.5-9B     |
| ----------------------------------------------------------- | ------------- | -------------- |
| Chapter                                                     | 92/109 = 0.84 | 118/127 = 0.93 |
| Section, given chapter right                                | 70/92 = 0.76  | 104/118 = 0.88 |
| Category, given section right and the category step ran     | 36/46 = 0.78  | 51/58 = 0.88   |
| All narrowing levels, given section right and narrowing ran | 35/46 = 0.76  | 50/58 = 0.86   |
| Final code, given the gold code was among the candidates    | 39/59 = 0.66  | 70/96 = 0.73   |
| — straight from section to code                             | 13/24 = 0.54  | 35/46 = 0.76   |
| — after category narrowing                                  | 26/35 = 0.74  | 35/50 = 0.70   |
| End to end, for extracted diagnoses                         | 39/109 = 0.36 | 70/127 = 0.55  |

### Where each gold code ended up (first failing step)

|                                            | Qwen3-4B | Qwen3.5-9B   |
| ------------------------------------------ | -------- | ------------ |
| Correct                                    | 44 (29%) | **75 (50%)** |
| Diagnosis never extracted                  | 37 (25%) | 19 (13%)     |
| Extracted, wrong chapter                   | 16 (11%) | 7 (5%)       |
| Extracted, right chapter, wrong section    | 21 (14%) | 14 (9%)      |
| Lost in category / deeper narrowing        | 11 (7%)  | 8 (5%)       |
| Reached the final list, wrong final choice | 19 (13%) | 25 (17%)     |
| Not billable in FY2027 (unreachable)       | 2 (1%)   | 2 (1%)       |

False positives: 4B 94 different-diagnosis + 21 wrong-specificity (same 3-character category); 9B 73 + 26.
With the 9B, the largest remaining loss is the final choice among candidates (mostly specificity), then extraction.

### Path through the hierarchy and options shown to the model (per extracted diagnosis)

|                                                                       | Qwen3-4B       | Qwen3.5-9B      |
| --------------------------------------------------------------------- | -------------- | --------------- |
| Straight from section to code (≤ 100 codes under the chosen sections) | 67/181 (37%)   | 65/190 (34%)    |
| Through the category step (> 100 codes)                               | 114/181 (63%)  | 125/190 (66%)   |
| — of those, needing a second (deeper) level                           | 16             | 21              |
| Codes under the chosen sections: direct / narrowed path (median)      | 48 / 271       | 67 / 255        |
| Chapter step: options / chosen (mean)                                 | 22 / 1.7       | 22 / 1.9        |
| Section step: options / chosen (mean)                                 | 22.0 / 1.6     | 24.9 / 1.6      |
| Category step: options (mean) → codes left (median)                   | 19.6 → 24      | 18.2 → 28       |
| Final step: candidates mean / median / max                            | 37.6 / 31 / 99 | 41.1 / 35 / 100 |
| Model calls per visit                                                 | 7.7            | 8.2             |

### Confidence and thresholds

The model gives a confidence only at the final step (high / medium / low → score 0.9 / 0.6 / 0.3); the system
applies **no threshold**. The confidence barely separates right from wrong, so a threshold would not help:

|                                  | Qwen3-4B   | Qwen3.5-9B |
| -------------------------------- | ---------- | ---------- |
| "high": codes, precision         | 135, 0.289 | 158, 0.437 |
| "medium": codes, precision       | 24, 0.208  | 16, 0.375  |
| "low"                            | 0          | 0          |
| F1 with all codes (no threshold) | 0.285      | 0.463      |
| F1 keeping only "high"           | 0.274      | 0.448      |

### "None fits" answers

At the final step the model can answer 0 = "none of these codes fits" instead of picking a code; that diagnosis then
gets no code.

|                                                                     | Qwen3-4B        | Qwen3.5-9B    |
| ------------------------------------------------------------------- | --------------- | ------------- |
| Diagnoses answered "none fits"                                      | 18 of 181 (10%) | 7 of 190 (4%) |
| — the model chose 0 (not an empty list or a failed call)            | 18              | 7             |
| — linked to a gold code                                             | 5               | 4             |
| — the gold code was actually among the candidates (wrong rejection) | 0               | 2             |

Mostly the option does its job: when an earlier step went wrong (so the correct code is not in the list), or the
diagnosis is an extra one with no gold code, declining avoids a false positive. Only the 9B twice rejected a list
that contained the gold code.

### Visits with no code

Every one of the 510 annotated visits has at least one majority gold code, and every physician coded every visit;
the only visits without labels are the 90 unannotated ones (used only for manual demos). So when the system returns
no code for a visit, it is always a miss. On the 100 test visits this happened 5 times per model:

| Model      | Visit | Why no code                        | Gold          |
| ---------- | ----- | ---------------------------------- | ------------- |
| Qwen3-4B   | V0029 | all diagnoses answered "none fits" | H90.3         |
| Qwen3-4B   | V0038 | all diagnoses answered "none fits" | Z01.810       |
| Qwen3-4B   | V0073 | all diagnoses answered "none fits" | J34.2         |
| Qwen3-4B   | V0101 | all diagnoses answered "none fits" | L63.9         |
| Qwen3-4B   | V0114 | all diagnoses answered "none fits" | M20.12        |
| Qwen3.5-9B | V0038 | no diagnosis extracted             | Z01.810       |
| Qwen3.5-9B | V0075 | no diagnosis extracted             | E07.9         |
| Qwen3.5-9B | V0086 | no diagnosis extracted             | D48.5         |
| Qwen3.5-9B | V0067 | all diagnoses answered "none fits" | C82.90        |
| Qwen3.5-9B | V0099 | all diagnoses answered "none fits" | E22.1, K29.00 |

V0038 (Z01.810, encounter for a pre-procedure examination) failed with both models: administrative "encounter" codes
are hard for this pipeline.

### Seen vs unseen codes, validity, evidence

|                                                                  | Qwen3-4B      | Qwen3.5-9B    |
| ---------------------------------------------------------------- | ------------- | ------------- |
| Recall on codes seen in dev gold (37 codes)                      | 0.405         | 0.486         |
| Recall on unseen codes (111 codes)                               | 0.261         | 0.514         |
| Valid billable FY2027 codes                                      | 159/159       | 174/174       |
| Evidence = model's exact quote (otherwise the closest note line) | 167/181 (92%) | 169/190 (89%) |

Nothing is trained, so "seen" only means the code appeared in the dev visits used for design choices; the 9B shows
no advantage on seen codes, as expected.

Full reports with failure examples and traces: `runs/test100_qwen3_4b_report.md`, `runs/test100_qwen35_9b_report.md`.

## Speed

Measured on an Apple M1 Max (64 GB). A visit needs ~8 model calls (1 extraction call, then 3–4 per diagnosis).

| Model      | Native Python + Ollama (GPU)                                                                                                                                | Docker on the same Mac (CPU only)                                                                 |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Qwen3-4B   | 17.5 s mean, 12 s median, 5–44 s (40 dev visits, one at a time); 19 s/visit throughput on the test run (4 concurrent visits)                                | ~18.5 min for one 3-diagnosis visit (12 calls), measured while the GPU evaluation ran in parallel |
| Qwen3.5-9B | 38.8 s mean, 43 s median, 1.5–104 s (40 dev visits, one at a time); 42 s/visit throughput on the test run (2 concurrent visits — concurrency does not help) | not measured (image built and health-checked only)                                                |

- **Docker on a Mac has no GPU.** Docker Desktop runs containers in a Linux VM; the Apple GPU (Metal) is not passed
  into it, so Ollama falls back to the CPU, where reading the 3–5k-token chapter/section prompts runs at ~20
  tokens/s.
- **Linux + NVIDIA GPU:** the Ollama base image includes CUDA. Install the NVIDIA Container Toolkit and add to the
  service in `docker-compose.yml`:
  ```yaml
      deploy:
        resources:
          reservations:
            devices: [{driver: nvidia, count: all, capabilities: [gpu]}]
  ```
- **Concurrency:** Qwen3.5-9B has a hybrid (partly recurrent) architecture, so Ollama cannot reuse cached prompt
  prefixes or batch requests efficiently; Qwen3-4B gains little (17.5 → 19 s/visit) because reading the prompt
  already saturates the GPU.

## Reproduce

Copy the provided `visits.csv` and `physician_annotations.csv` into `data/`, pull the model(s) with Ollama (the
judge needs `qwen3:4b-instruct-2507-q8_0`), then:

```bash
.venv/bin/python -m scripts.split                         # dev 150 / test 360 (splits.json is included)
MODEL=qwen3.5:9b-q8_0 .venv/bin/python -m scripts.evaluate --split dev --n 40 --name my_dev_run
.venv/bin/python -m scripts.evaluate --split test --n 100 --name test100_qwen35_9b --report-only   # re-score saved results
```

`--workers N` processes N visits concurrently (start Ollama with `OLLAMA_NUM_PARALLEL=N`).
