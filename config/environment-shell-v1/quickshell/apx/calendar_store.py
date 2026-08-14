#!/usr/bin/env python3
"""Tiny JSON store used by the Quickshell calendar."""

import json
import os
import sys
from pathlib import Path


DATA_DIR = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "apx-quickshell"
DATA_FILE = DATA_DIR / "calendar-events.json"


def load_calendar():
    try:
        payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            categories = sorted({
                event.get("category", "").strip()
                for event in payload
                if isinstance(event, dict) and event.get("category", "").strip()
            })
            return {"events": payload, "categories": categories}
        if isinstance(payload, dict):
            return {
                "events": payload.get("events", []),
                "categories": payload.get("categories", []),
            }
        return {"events": [], "categories": []}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {"events": [], "categories": []}


def save_calendar(raw):
    payload = json.loads(raw)
    if not isinstance(payload, dict) or not isinstance(payload.get("events"), list):
        raise ValueError("calendar data must contain an events list")
    if not isinstance(payload.get("categories", []), list):
        raise ValueError("calendar categories must be a list")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temporary = DATA_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(DATA_FILE)


def main():
    operation = sys.argv[1] if len(sys.argv) > 1 else "load"
    if operation == "load":
        print(json.dumps(load_calendar(), ensure_ascii=False))
    elif operation == "save" and len(sys.argv) == 3:
        save_calendar(sys.argv[2])
    else:
        raise SystemExit("usage: calendar_store.py load | save JSON")


if __name__ == "__main__":
    main()
