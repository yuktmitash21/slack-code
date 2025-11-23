import json
import os
import threading
import fcntl
from datetime import datetime, timezone
from typing import List, Dict, Optional

STATS_DIR = os.path.join(os.path.dirname(__file__), "data")
STATS_FILE = os.path.join(STATS_DIR, "pr_activity.json")

class FileLock:
    def __init__(self):
        self.lock_path = STATS_FILE + ".lock"
        self.fd = None
    
    def __enter__(self):
        self.fd = open(self.lock_path, "w")
        fcntl.flock(self.fd, fcntl.LOCK_EX)
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        fcntl.flock(self.fd, fcntl.LOCK_UN)
        self.fd.close()

_LOCK = FileLock()

os.makedirs(STATS_DIR, exist_ok=True)


def _ensure_file() -> None:
    if not os.path.exists(STATS_FILE):
        with open(STATS_FILE, "w", encoding="utf-8") as stats_fp:
            json.dump([], stats_fp, indent=2)


def _load_records() -> List[Dict]:
    _ensure_file()
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as stats_fp:
            return json.load(stats_fp)
    except json.JSONDecodeError:
        return []


def _write_records(records: List[Dict]) -> None:
    temp_path = STATS_FILE + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as stats_fp:
        json.dump(records, stats_fp, indent=2)
    os.replace(temp_path, STATS_FILE)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_pr_creation(
    pr_number: Optional[int],
    channel_id: Optional[str],
    channel_name: Optional[str],
    created_at: Optional[str] = None,
    thread_ts: Optional[str] = None,
    processing_time_ms: Optional[int] = None,
) -> None:
    """
    Persist a PR creation event so the dashboard can build analytics.
    """
    if not pr_number:
        return

    print(f"DEBUG: Attempting to log PR #{pr_number} for channel {channel_name} to {STATS_FILE}")

    record = {
        "pr_number": int(pr_number),
        "channel_id": channel_id,
        "channel_name": channel_name or channel_id,
        "created_at": created_at or _iso_now(),
        "merged": False,
        "merged_at": None,
        "thread_ts": thread_ts,
    }
    
    if processing_time_ms is not None:
        record["processing_time_ms"] = int(processing_time_ms)

    with _LOCK:
        records = _load_records()
        existing = next((r for r in records if r.get("pr_number") == pr_number), None)
        if existing:
            existing.update(record)
            print(f"DEBUG: Updated existing PR #{pr_number} in records")
        else:
            records.append(record)
            print(f"DEBUG: Added new PR #{pr_number} to records")
        _write_records(records)
        print(f"DEBUG: Successfully wrote to {STATS_FILE}")


def mark_pr_merged(pr_number: Optional[int], merged_at: Optional[str] = None) -> None:
    """
    Mark a PR as merged for analytics.
    """
    if not pr_number:
        return

    with _LOCK:
        records = _load_records()
        updated = False
        for record in records:
            if record.get("pr_number") == pr_number:
                record["merged"] = True
                record["merged_at"] = merged_at or _iso_now()
                updated = True
                break

        if updated:
            _write_records(records)


def get_pr_activity() -> List[Dict]:
    """
    Helper to retrieve the raw activity list (useful for debugging/tests).
    """
    with _LOCK:
        return list(_load_records())

