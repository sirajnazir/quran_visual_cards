"""Quran Verse Retrieval Module

Fetches Arabic text and English translation for any Quran verse.
Uses alquran.cloud API as the primary source with a local JSON cache
that builds up over time so repeated lookups are instant and offline-friendly.

Cache file: static/quran_verse_cache.json
API: https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/editions/quran-uthmani,en.sahih
"""

import json
import os
import urllib.request
import urllib.error
from pathlib import Path

# ---------- Configuration ----------
CACHE_DIR = os.path.join(os.path.dirname(__file__), "static")
CACHE_FILE = os.path.join(CACHE_DIR, "quran_verse_cache.json")

# alquran.cloud editions
ARABIC_EDITION = "quran-uthmani"        # Standard Uthmani script
ENGLISH_EDITION = "en.sahih"            # Sahih International (widely trusted)

API_BASE = "https://api.alquran.cloud/v1"
API_TIMEOUT = 10  # seconds


# ---------- Cache Management ----------

def _load_cache():
    """Load the local verse cache from disk."""
    if os.path.isfile(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[QuranVerses] Cache load error: {e}")
    return {}


def _save_cache(cache):
    """Save the verse cache to disk."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[QuranVerses] Cache save error: {e}")


def _cache_key(surah, ayah):
    """Generate a cache key like '2:255'."""
    return f"{surah}:{ayah}"


# ---------- API Fetching ----------

def _fetch_from_api(surah, ayah):
    """Fetch a single verse (Arabic + English) from alquran.cloud API.

    Uses the /ayah/{reference}/editions endpoint to get both
    Arabic and English in a single request.

    Returns:
        dict with 'arabic', 'english', 'surah_name', 'surah_english' keys
        or None on failure
    """
    url = f"{API_BASE}/ayah/{surah}:{ayah}/editions/{ARABIC_EDITION},{ENGLISH_EDITION}"
    print(f"[QuranVerses] Fetching {surah}:{ayah} from API...")

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "QuranVisualCards/1.0",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if data.get("code") != 200 or data.get("status") != "OK":
            print(f"[QuranVerses] API returned status: {data.get('status')}")
            return None

        editions = data.get("data", [])
        if not editions or len(editions) < 2:
            print(f"[QuranVerses] Expected 2 editions, got {len(editions)}")
            return None

        arabic_data = editions[0]
        english_data = editions[1]

        result = {
            "arabic": arabic_data.get("text", ""),
            "english": english_data.get("text", ""),
            "surah_number": arabic_data.get("surah", {}).get("number", surah),
            "surah_name": arabic_data.get("surah", {}).get("name", ""),
            "surah_english": arabic_data.get("surah", {}).get("englishName", ""),
            "ayah_number": arabic_data.get("numberInSurah", ayah),
        }

        print(f"[QuranVerses] Fetched: {result['surah_english']} {surah}:{ayah}")
        return result

    except urllib.error.URLError as e:
        print(f"[QuranVerses] Network error: {e}")
        return None
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"[QuranVerses] Parse error: {e}")
        return None
    except Exception as e:
        print(f"[QuranVerses] Unexpected error: {e}")
        return None


def _fetch_full_surah_from_api(surah):
    """Fetch ALL verses of a surah at once (Arabic + English).

    More efficient than fetching one-by-one. Caches everything.
    Uses /surah/{number}/editions endpoint.

    Returns:
        list of dicts with 'arabic', 'english' keys, or None on failure
    """
    url = f"{API_BASE}/surah/{surah}/editions/{ARABIC_EDITION},{ENGLISH_EDITION}"
    print(f"[QuranVerses] Fetching full Surah {surah} from API...")

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "QuranVisualCards/1.0",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if data.get("code") != 200 or data.get("status") != "OK":
            print(f"[QuranVerses] API returned status: {data.get('status')}")
            return None

        editions = data.get("data", [])
        if not editions or len(editions) < 2:
            return None

        arabic_ayahs = editions[0].get("ayahs", [])
        english_ayahs = editions[1].get("ayahs", [])

        surah_name = editions[0].get("name", "")
        surah_english = editions[0].get("englishName", "")

        if len(arabic_ayahs) != len(english_ayahs):
            print(f"[QuranVerses] Mismatch: {len(arabic_ayahs)} arabic vs {len(english_ayahs)} english")
            return None

        verses = []
        for ar, en in zip(arabic_ayahs, english_ayahs):
            verses.append({
                "arabic": ar.get("text", ""),
                "english": en.get("text", ""),
                "surah_number": surah,
                "surah_name": surah_name,
                "surah_english": surah_english,
                "ayah_number": ar.get("numberInSurah", 0),
            })

        print(f"[QuranVerses] Fetched {len(verses)} verses for Surah {surah} ({surah_english})")
        return verses

    except Exception as e:
        print(f"[QuranVerses] Full surah fetch error: {e}")
        return None


# ---------- Bismillah Stripping ----------

# The Bismillah text in various forms found in the quran-uthmani edition
_BISMILLAH_PATTERNS = [
    "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
    "بِسۡمِ ٱللَّهِ ٱلرَّحۡمَـٰنِ ٱلرَّحِيمِ",
    "بسم الله الرحمن الرحيم",
    "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ",
    "بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ",
]


def _strip_bismillah(arabic_text, surah, ayah):
    """Strip the Bismillah prefix from verse 1 of surahs where it's not part of the verse.

    Rules:
    - Surah 1 (Al-Fatihah): Bismillah IS the first verse — DO NOT strip
    - Surah 9 (At-Tawbah): Has no Bismillah at all — nothing to strip
    - All other surahs (2-8, 10-114): Bismillah is a pre-verse prefix that
      the API sometimes concatenates with verse 1 — STRIP it

    Uses Unicode NFC normalization to handle diacritical mark ordering differences
    between different API sources (e.g., shadda+fatha vs fatha+shadda).

    Returns: cleaned Arabic text
    """
    import unicodedata

    if ayah != 1:
        return arabic_text
    if surah == 1 or surah == 9:
        return arabic_text

    if not arabic_text:
        return arabic_text

    # Normalize the input text for comparison
    normalized_text = unicodedata.normalize("NFC", arabic_text)

    for pattern in _BISMILLAH_PATTERNS:
        normalized_pattern = unicodedata.normalize("NFC", pattern)
        if normalized_text.startswith(normalized_pattern):
            # Strip the Bismillah using the normalized length
            remainder = normalized_text[len(normalized_pattern):].strip()
            return remainder if remainder else arabic_text

    # Fallback: try a simpler approach — strip any text before the first
    # non-Bismillah Arabic word by checking for the core "بسم" root
    if normalized_text.startswith("\u0628\u0650\u0633\u0652") or normalized_text.startswith("\u0628\u0650\u0633\u06e1"):
        # Find the end of "الرحيم" and take everything after
        for end_marker in ["ٱلرَّحِيمِ", "الرَّحِيمِ", "الرحيم"]:
            norm_marker = unicodedata.normalize("NFC", end_marker)
            idx = normalized_text.find(norm_marker)
            if idx >= 0:
                remainder = normalized_text[idx + len(norm_marker):].strip()
                return remainder if remainder else arabic_text

    return arabic_text


def _clean_verse_data(result):
    """Apply Bismillah stripping and any other cleaning to a verse result."""
    if not result or "error" in result:
        return result
    surah = result.get("surah_number", 0)
    ayah = result.get("ayah_number", 0)
    if result.get("arabic"):
        result["arabic"] = _strip_bismillah(result["arabic"], surah, ayah)
    return result


# ---------- Cache Migration (clean Bismillah from existing cached data) ----------

def _migrate_cache_bismillah():
    """One-time migration: strip Bismillah from any cached verse 1 entries."""
    cache = _load_cache()
    if not cache:
        return
    changed = False
    for key, val in cache.items():
        if ":" not in key:
            continue
        parts = key.split(":")
        surah_num = int(parts[0])
        ayah_num = int(parts[1])
        if ayah_num == 1 and surah_num not in (1, 9) and val.get("arabic"):
            original = val["arabic"]
            cleaned = _strip_bismillah(original, surah_num, ayah_num)
            if cleaned != original:
                val["arabic"] = cleaned
                changed = True
    if changed:
        _save_cache(cache)
        print("[QuranVerses] Cache migrated: stripped Bismillah from verse 1 entries")

# Run migration on module load
_migrate_cache_bismillah()


# ---------- Public API ----------

def get_verse(surah, ayah):
    """Get a Quran verse's Arabic text and English translation.

    Checks local cache first, then fetches from alquran.cloud API.
    Caches the result for future lookups.

    Args:
        surah: Surah number (1-114)
        ayah: Ayah/verse number within the surah

    Returns:
        dict with 'arabic', 'english', 'surah_name', 'surah_english',
        'surah_number', 'ayah_number' keys, or error dict
    """
    try:
        surah = int(surah)
        ayah = int(ayah)
    except (ValueError, TypeError):
        return {"error": f"Invalid surah ({surah}) or ayah ({ayah}) number"}

    if surah < 1 or surah > 114:
        return {"error": f"Surah number must be 1-114, got {surah}"}

    key = _cache_key(surah, ayah)

    # Check cache first
    cache = _load_cache()
    if key in cache:
        print(f"[QuranVerses] Cache hit: {key}")
        return _clean_verse_data(dict(cache[key]))

    # Not in cache — fetch from API
    result = _fetch_from_api(surah, ayah)
    if not result:
        return {"error": f"Could not fetch verse {surah}:{ayah} from API"}

    # Clean Bismillah before caching
    result = _clean_verse_data(result)

    # Save to cache
    cache[key] = result
    _save_cache(cache)

    return result


def get_surah_verses(surah):
    """Get ALL verses for an entire surah. Caches them all at once.

    More efficient than individual lookups — single API call for the whole surah.

    Args:
        surah: Surah number (1-114)

    Returns:
        list of verse dicts, or error dict
    """
    try:
        surah = int(surah)
    except (ValueError, TypeError):
        return {"error": f"Invalid surah number: {surah}"}

    if surah < 1 or surah > 114:
        return {"error": f"Surah number must be 1-114, got {surah}"}

    cache = _load_cache()

    # Check if first verse is cached (likely means whole surah is cached)
    first_key = _cache_key(surah, 1)
    if first_key in cache:
        # Collect all cached verses for this surah
        cached_verses = []
        ayah = 1
        while True:
            k = _cache_key(surah, ayah)
            if k in cache:
                cached_verses.append(_clean_verse_data(dict(cache[k])))
                ayah += 1
            else:
                break
        if cached_verses:
            print(f"[QuranVerses] Cache hit: Surah {surah} ({len(cached_verses)} verses)")
            return cached_verses

    # Fetch full surah from API
    verses = _fetch_full_surah_from_api(surah)
    if not verses:
        return {"error": f"Could not fetch Surah {surah} from API"}

    # Clean and cache all verses
    for v in verses:
        v = _clean_verse_data(v)
        key = _cache_key(v["surah_number"], v["ayah_number"])
        cache[key] = v
    _save_cache(cache)

    return [_clean_verse_data(v) for v in verses]


def get_cache_stats():
    """Get statistics about the local verse cache."""
    cache = _load_cache()
    if not cache:
        return {"total_cached": 0, "total_quran_verses": 6236, "cache_percent": 0.0, "surahs_with_cache": []}

    surahs = set()
    for key in cache:
        if ":" in key:
            s = key.split(":")[0]
            surahs.add(int(s))

    return {
        "total_cached": len(cache),
        "total_quran_verses": 6236,
        "cache_percent": round(len(cache) / 6236 * 100, 1),
        "surahs_with_cache": sorted(surahs),
    }
