import json
from pathlib import Path


LEDGER_FILE = Path("data/ledger.jsonl")


def record(event: str, data: dict):
    LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "event": event,
        "data": data,
    }

    with LEDGER_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def history():
    if not LEDGER_FILE.exists():
        return []

    return [
        json.loads(line)
        for line in LEDGER_FILE.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
