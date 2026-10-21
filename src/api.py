"""FastAPI inference service.

    POST /predict   one visit in, ICD-10-CM codes + score + evidence out (?debug=true adds the stage trace)
    GET  /health
"""
from fastapi import FastAPI
from pydantic import BaseModel

from src import config
from src.pipeline import Coder

app = FastAPI(title="ClinicalNote2Diagnoses", version="1.0")
_coder = None


# Create the coder lazily on first use (parsing the XML takes a moment)
def coder():
    global _coder
    if _coder is None:
        _coder = Coder()
    return _coder


# Request body: only note_text is required; the rest is optional context for the model
class Visit(BaseModel):
    note_text: str
    visit_id: str | None = None
    age: int | str = "unknown"
    sex: str = "unknown"
    physician_specialty: str = "unknown"
    encounter_type: str = "unknown"
    visit_type: str = "unknown"
    care_setting: str = "unknown"


# Liveness check; also reports the served model and ICD-10-CM release
@app.get("/health")
def health():
    return {"status": "ok", "model": config.MODEL, "icd10cm_release": f"FY{coder().cat.version}"}


# Main endpoint: one visit in, codes + score + evidence out (debug adds the stage trace)
@app.post("/predict")
def predict(visit: Visit, debug: bool = False):
    res = coder().predict(visit.model_dump())
    out = {"visit_id": visit.visit_id, "predictions": res["predictions"]}
    if debug:
        out.update(trace=res["trace"], llm_calls=res["llm_calls"], seconds=res["seconds"])
    return out
