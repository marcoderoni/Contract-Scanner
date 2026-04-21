# Copyright (c) 2026 Marco De Roni. All rights reserved.
# Licensed under the MIT License — see LICENSE file for details.

import os
import json
import hashlib
from datetime import datetime

AUDIT_LOG_PATH = "audit_log.jsonl"


def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def log_analysis(contract_name: str, overall_score: str, missing_clauses: list, metadata: dict):
    """Append an audit entry to the log file."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "contract": contract_name,
        "overall_score": overall_score,
        "missing_clauses": missing_clauses,
        "governing_law": metadata.get("governing_law", "Not detected"),
        "notice_period": metadata.get("notice_period", "Not detected"),
    }
    entry_str = json.dumps(entry, sort_keys=True)
    entry["hash"] = compute_hash(entry_str)

    with open(AUDIT_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return entry


def read_audit_log() -> list:
    if not os.path.exists(AUDIT_LOG_PATH):
        return []
    entries = []
    with open(AUDIT_LOG_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries