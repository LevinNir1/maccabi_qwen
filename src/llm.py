"""Minimal Ollama client: one chat call with a JSON-schema-constrained output."""
import json
import time

import requests

from src import config


# Thin wrapper around Ollama's /api/chat that also counts calls and time
class LLM:
    def __init__(self, model=config.MODEL, url=config.OLLAMA_URL):
        self.model, self.url = model, url
        self.calls, self.seconds, self.failures = 0, 0.0, 0

    def ask(self, system: str, user: str, schema: dict) -> dict | None:
        """Returns the parsed JSON, or None if the model failed to produce valid JSON twice."""
        # Try up to twice; the second try uses a different seed
        for attempt in range(2):
            t0 = time.time()
            r = requests.post(f"{self.url}/api/chat", timeout=600, json={
                "model": self.model,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "format": schema,        # constrained decoding: output must match the schema (incl. enums)
                "stream": False,
                "think": config.THINK,
                "keep_alive": "60m",
                "options": {"temperature": config.TEMPERATURE, "num_ctx": config.NUM_CTX,
                            "num_predict": config.MAX_OUTPUT_TOKENS, "seed": attempt},
            })
            # Fail loudly on HTTP errors; count the call and its duration
            r.raise_for_status()
            self.calls += 1
            self.seconds += time.time() - t0
            # The schema guarantees JSON shape, but a cut-off answer can still be invalid JSON
            try:
                return json.loads(r.json()["message"]["content"])
            except json.JSONDecodeError:
                self.failures += 1
        return None
