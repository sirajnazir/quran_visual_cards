#!/usr/bin/env python3
"""Provision complete Quran text data locally.

Downloads all 6236 verses (Arabic + Sahih International English) from
alquran.cloud API and saves them to static/quran_verse_cache.json.

Run this once to enable fully offline verse auto-population:
    python3 provision_quran_data.py

The script fetches one surah at a time (114 API calls total) and shows
progress. If interrupted, re-running picks up where it left off using
the existing cache.
"""

import json
import os
import sys
import time

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(__file__))
from quran_verses import get_surah_verses, get_cache_stats, _load_cache, _cache_key

SURAHS_FILE = os.path.join(os.path.dirname(__file__), "static", "quran_surahs.json")


def main():
    # Load surah metadata
    with open(SURAHS_FILE, "r", encoding="utf-8") as f:
        surahs = json.load(f)

    print("=" * 60)
    print("  Quran Verse Provisioning Tool")
    print("  Source: alquran.cloud API (Uthmani Arabic + Sahih International)")
    print("=" * 60)

    # Check current cache state
    stats = get_cache_stats()
    print(f"\n  Current cache: {stats['total_cached']} / 6236 verses ({stats['cache_percent']}%)")
    if stats['total_cached'] == 6236:
        print("  All verses already cached! Nothing to do.")
        return

    # Check which surahs still need fetching
    cache = _load_cache()
    surahs_to_fetch = []
    for s in surahs:
        num = s["number"]
        # Check if first verse of this surah is in cache
        if _cache_key(num, 1) not in cache:
            surahs_to_fetch.append(s)

    print(f"  Surahs to fetch: {len(surahs_to_fetch)} / 114\n")

    if not surahs_to_fetch:
        print("  All surahs appear to be cached.")
        return

    fetched = 0
    errors = 0

    for i, s in enumerate(surahs_to_fetch):
        num = s["number"]
        name = s["name_english"]
        verse_count = s["verses"]

        print(f"  [{i+1}/{len(surahs_to_fetch)}] Surah {num}. {name} ({verse_count} verses)...", end=" ", flush=True)

        result = get_surah_verses(num)

        if isinstance(result, dict) and "error" in result:
            print(f"FAILED: {result['error']}")
            errors += 1
        elif isinstance(result, list):
            print(f"OK ({len(result)} verses)")
            fetched += len(result)
        else:
            print("UNKNOWN RESULT")
            errors += 1

        # Small delay to be respectful to the API
        if i < len(surahs_to_fetch) - 1:
            time.sleep(0.5)

    print("\n" + "=" * 60)
    final_stats = get_cache_stats()
    print(f"  Provisioning complete!")
    print(f"  Verses fetched this run: {fetched}")
    print(f"  Errors: {errors}")
    print(f"  Total cached: {final_stats['total_cached']} / 6236 ({final_stats['cache_percent']}%)")
    print("=" * 60)


if __name__ == "__main__":
    main()
