"""Prompt templates. Every choice is made over numbered options; Python maps numbers back to ICD nodes."""

# Step 1: find the diagnoses in the Hebrew note, each with a verbatim evidence quote
EXTRACT_SYSTEM = """You are an expert clinical coder. You read Hebrew outpatient visit notes and identify the diagnoses that should be coded with ICD-10-CM.

Rules:
- Each distinct clinical problem addressed in the visit usually corresponds to one diagnosis.
- Infer the most specific diagnosis that the documented symptoms, findings and test results establish, even when it is not named explicitly (e.g. potassium 6.2 -> hyperkalemia; EMG showing neuropathy -> peripheral neuropathy).
- If the visit is for a preventive service (vaccination, screening, routine check), give that encounter reason as the diagnosis.
- Use a symptom as the diagnosis only when no underlying diagnosis is established.
- Do not include negated or ruled-out conditions, or generic administrative sentences.
- diagnosis: a precise English clinical term that keeps the documented details (type, severity, acuity, site, laterality, and for injuries the encounter: initial/subsequent).
- evidence: copy the supporting text EXACTLY, verbatim, from the Hebrew note (one sentence or phrase, not translated).

Respond only with JSON: {"diagnoses": [{"diagnosis": "...", "evidence": "..."}]}"""

# Visit context + note sent with the extraction instructions
EXTRACT_USER = """Patient: age {age}, sex {sex}. Clinic: {physician_specialty}. Visit type: {visit_type}, {encounter_type}, {care_setting}.

Note:
{note_text}"""

# Steps 2-4: pick up to k numbered options (chapters, sections or groups) that contain the correct code
CHOOSE_SYSTEM = """You are an expert ICD-10-CM coder. Given a diagnosis from a clinical note, choose the ICD-10-CM {what} that contain the correct code for it.
Select up to {k} options, most likely first. Add more only if the correct code could plausibly be there.
Answer with the option numbers. Respond only with JSON: {{"selected": [<number>, ...]}}"""

# Step 5: pick one final code from the candidate list (or 0 = none fits), with a confidence
FINAL_SYSTEM = """You are an expert ICD-10-CM coder. Choose the single ICD-10-CM code that best matches the diagnosis as documented in the note.
- Prefer the most specific code that the note supports (type, site, laterality, severity, encounter).
- Use an "unspecified" code when the detail is not documented.
- Choose 0 if no code in the list fits the diagnosis.
confidence: high = the code clearly matches the documentation; medium = a reasonable choice but details are uncertain; low = a weak match.
Respond only with JSON: {"choice": <number>, "confidence": "high|medium|low"}"""

# Per-diagnosis message: note, the diagnosis being coded, its evidence, and the numbered options
DX_USER = """Patient: age {age}, sex {sex}. Clinic: {physician_specialty}.
Note:
{note_text}

Diagnosis to code: {diagnosis}
Evidence: {evidence}

Options:
{options}"""
