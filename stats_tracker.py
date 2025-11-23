import json
import os
import threading
from datetime import datetime, timezone
from typing import List, Dict, Optional

STATS_DIR = os.path.join(os.path.dirname(__file__), "data")
STATS_FILE = os.path.join(STATS_DIR, "pr_activity.json")
_LOCK = threading.Lock()

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
) -> None:
    """
    Persist a PR creation event so the dashboard can build analytics.
    """
    if not pr_number:
        return

    record = {
        "pr_number": int(pr_number),
        "channel_id": channel_id,
        "channel_name": channel_name or channel_id,
        "created_at": created_at or _iso_now(),
        "merged": False,
        "merged_at": None,
        "thread_ts": thread_ts,
    }

    with _LOCK:
        records = _load_records()
        existing = next((r for r in records if r.get("pr_number") == pr_number), None)
        if existing:
            existing.update(record)
        else:
            records.append(record)
        _write_records(records)


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

