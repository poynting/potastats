#!/usr/bin/env python3
import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Iterable, Dict, Optional

try:
    import requests
    from tqdm import tqdm
except ImportError:
    print("This script requires 'requests' and 'tqdm'. Install with:\n  pip install requests tqdm")
    sys.exit(1)

POTA_URL = "https://api.pota.app/activator/all"

def safe_int(x: Any) -> int:
    try:
        if x is None:
            return 0
        return int(float(x))
    except (ValueError, TypeError):
        return 0

def file_age_hours(path: str) -> Optional[float]:
    """Return file age in hours, or None if it doesn't exist."""
    if not os.path.exists(path):
        return None
    try:
        mtime = os.path.getmtime(path)
        return (time.time() - mtime) / 3600.0
    except Exception:
        return None

def load_cached_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)

def fetch_json_with_progress(url: str, timeout: float = 60.0) -> Any:
    """Stream download JSON with a progress bar."""
    with requests.get(url, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        chunks = []
        with tqdm(total=total, unit="B", unit_scale=True, desc="Downloading") as pbar:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    chunks.append(chunk)
                    pbar.update(len(chunk))
        raw = b"".join(chunks)
        return json.loads(raw)

def get_data(url: str, cache_path: Optional[str], refresh: bool, max_age: Optional[float]) -> Any:
    """
    Get data with caching behavior:
      - If cache exists and !refresh and (max_age is None or cache_age <= max_age): use cache.
      - Otherwise download (with progress), save to cache (if provided), return fresh.
    """
    if cache_path and os.path.exists(cache_path) and not refresh:
        age = file_age_hours(cache_path)
        if max_age is None or (age is not None and age <= max_age):
            try:
                data = load_cached_json(cache_path)
                print(f"Loaded cached data from {cache_path} (age: {age:.2f}h)" if age is not None else
                      f"Loaded cached data from {cache_path}")
                return data
            except Exception as e:
                print(f"Warning: failed to read cache {cache_path}: {e}", file=sys.stderr)

    # Download fresh
    data = fetch_json_with_progress(url)
    if cache_path:
        try:
            save_json(cache_path, data)
            print(f"Saved fresh data to {cache_path} at {datetime.now().isoformat(timespec='seconds')}")
        except Exception as e:
            print(f"Warning: failed to save cache {cache_path}: {e}", file=sys.stderr)
    return data

def aggregate_stats(rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    total_contacts = 0
    total_cw = 0
    total_data = 0
    total_phone = 0

    for entry in rows:
        total_contacts += safe_int(entry.get("TotalContacts"))
        total_cw       += safe_int(entry.get("TotalCWContacts"))
        total_data     += safe_int(entry.get("TotalDataContacts"))
        total_phone    += safe_int(entry.get("TotalPhoneContacts"))

    percentages = (
        {"CW": 100*total_cw/total_contacts,
         "Data": 100*total_data/total_contacts,
         "Phone": 100*total_phone/total_contacts}
        if total_contacts > 0 else {"CW":0.0, "Data":0.0, "Phone":0.0}
    )

    return {
        "Total Contacts": total_contacts,
        "Mode Totals": {"CW": total_cw, "Data": total_data, "Phone": total_phone},
        "Mode Percentages": percentages
    }

def main():
    parser = argparse.ArgumentParser(description="POTA activator stats with caching and progress bar.")
    parser.add_argument("--url", default=POTA_URL, help="Source URL (default: POTA API).")
    parser.add_argument("--cache", default="pota_cache/POTA_all.json",
                        help="Path to cache the JSON (default: pota_cache/POTA_all.json).")
    parser.add_argument("--refresh", action="store_true",
                        help="Force re-download even if cache exists.")
    parser.add_argument("--max-age", type=float, default=None,
                        help="Maximum cache age in hours before auto-refresh (default: no limit).")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print the summary JSON.")
    args = parser.parse_args()

    data = get_data(args.url, args.cache, args.refresh, args.max_age)

    summary = aggregate_stats(data)
    if args.pretty:
        print(json.dumps(summary, indent=2))
    else:
        mt = summary["Mode Totals"]
        mp = summary["Mode Percentages"]
        print(f"Total Contacts: {summary['Total Contacts']:,}")
        print(f"Mode Totals:    CW={mt['CW']:,}  Data={mt['Data']:,}  Phone={mt['Phone']:,}")
        print(f"Mode %:         CW={mp['CW']:.2f}%  Data={mp['Data']:.2f}%  Phone={mp['Phone']:.2f}%")

if __name__ == "__main__":
    main()

