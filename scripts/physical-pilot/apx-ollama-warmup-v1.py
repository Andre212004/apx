#!/usr/bin/env python3
"""Load the admitted local model before Ollama is reported ready."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path


BASE = "http://127.0.0.1:11434"
SELECTION_FILE = Path("/var/lib/apx/model-selection-v1/selected")
MODELS = {
    "fast": "qwen2.5-coder:3b",
    "balanced": "qwen2.5-coder:7b",
    "quality": "qwen3-coder:30b",
}


def selected_model() -> str:
    try:
        profile = SELECTION_FILE.read_text(encoding="ascii").strip()
    except FileNotFoundError:
        profile = "fast"
    try:
        return MODELS[profile]
    except KeyError as error:
        raise RuntimeError("persistent model selection differs") from error


def request(path: str, payload: dict[str, object] | None = None, timeout: int = 5) -> dict[str, object]:
    data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode()
    value = urllib.request.Request(
        BASE + path, data=data,
        headers={"Content-Type": "application/json"} if data is not None else {},
    )
    with urllib.request.urlopen(value, timeout=timeout) as response:
        result = json.load(response)
    if type(result) is not dict:
        raise RuntimeError("Ollama warm-up response differs")
    return result


def main() -> None:
    model = selected_model()
    deadline = time.monotonic() + 20
    while True:
        try:
            request("/api/version")
            break
        except (OSError, urllib.error.URLError, json.JSONDecodeError):
            if time.monotonic() >= deadline:
                raise RuntimeError("Ollama API did not become ready")
            time.sleep(0.25)
    result = request(
        "/api/generate",
        {
            "model": model,
            "prompt": "",
            "stream": False,
            "keep_alive": -1,
            "options": {"num_ctx": 8192, "num_predict": 0},
        },
        timeout=150,
    )
    if result.get("model") != model or result.get("done") is not True:
        raise RuntimeError("admitted model warm-up did not complete")


if __name__ == "__main__":
    main()
