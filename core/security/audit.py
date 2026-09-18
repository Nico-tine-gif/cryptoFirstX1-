import hashlib
import json
import time
from pathlib import Path


AUDIT_FILE = Path("logs/admin_audit.jsonl")


def record(event: str, actor: str = "system", **data) -> dict:
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": int(time.time()),
        "event": event,
        "actor": actor,
        "data": data,
    }

    canonical = json.dumps(
        entry,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()

    entry["record_hash"] = hashlib.sha256(canonical).hexdigest()

    with AUDIT_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")

    return entry
