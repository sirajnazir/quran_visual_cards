"""Ibn Kathir Tafsir retrieval and caching module.

Fetches English Ibn Kathir tafsir per verse from multiple API sources,
caches locally in JSON for instant subsequent lookups.

API Sources (tried in order):
1. Quran.com API v4 — /api/v4/tafsirs/en-tafisr-ibn-kathir/by_ayah/{surah}:{ayah}
2. spa5k tafsir_api CDN — jsdelivr hosted JSON files per surah
3. quranapi.pages.dev — /api/tafsir/{surah}_{ayah}.json

All sources provide Ibn Kathir's Tafsir in English, abridged version.
"""
import json
import os
import re
import urllib.request
import urllib.error

TAFSIR_CACHE_FILE = os.path.join(
    os.path.dirname(__file__), "static", "tafsir_cache.json"
)


def _load_cache():
    if os.path.exists(TAFSIR_CACHE_FILE):
        try:
            with open(TAFSIR_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_cache(cache):
    os.makedirs(os.path.dirname(TAFSIR_CACHE_FILE), exist_ok=True)
    with open(TAFSIR_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def _fetch_url(url, timeout=15):
    """Fetch a URL and return the parsed JSON or None."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "QuranVisualCards/1.0", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode("utf-8")
            return json.loads(data)
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError,
            OSError, TimeoutError) as e:
        print(f"[Tafsir] Fetch failed for {url}: {e}")
        return None


def _clean_html(text):
    """Strip HTML tags from tafsir text."""
    if not text:
        return ""
    # Remove HTML tags
    clean = re.sub(r"<[^>]+>", "", text)
    # Normalize whitespace
    clean = re.sub(r"\s+", " ", clean).strip()
    # Decode HTML entities
    clean = clean.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    clean = clean.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    return clean


def _fetch_from_quran_com(surah, ayah):
    """Try Quran.com API v4 for Ibn Kathir tafsir."""
    url = f"https://api.quran.com/api/v4/tafsirs/en-tafisr-ibn-kathir/by_ayah/{surah}:{ayah}"
    data = _fetch_url(url)
    if data and "tafsir" in data:
        tafsir = data["tafsir"]
        text = tafsir.get("text", "")
        return _clean_html(text) if text else None
    # Alternative structure
    if data and "tafsirs" in data and len(data["tafsirs"]) > 0:
        text = data["tafsirs"][0].get("text", "")
        return _clean_html(text) if text else None
    return None


def _fetch_from_spa5k_cdn(surah, ayah):
    """Try spa5k tafsir_api CDN (jsdelivr) — fetches entire surah, caches all verses."""
    url = f"https://cdn.jsdelivr.net/gh/spa5k/tafsir_api@main/tafsir/en-tafisr-ibn-kathir/{surah}.json"
    data = _fetch_url(url)
    if not data:
        return None, {}

    # This returns an object with verse data — structure varies
    # Try to extract the specific ayah
    all_verses = {}
    if isinstance(data, dict):
        # Could be keyed by ayah number or have an "ayahs" array
        if "ayahs" in data:
            for item in data["ayahs"]:
                a_num = item.get("ayah", item.get("verse_number", 0))
                text = _clean_html(item.get("text", ""))
                if text:
                    all_verses[str(a_num)] = text
        else:
            # Might be keyed directly
            for key, val in data.items():
                if isinstance(val, dict) and "text" in val:
                    all_verses[str(key)] = _clean_html(val["text"])
                elif isinstance(val, str):
                    all_verses[str(key)] = _clean_html(val)
    elif isinstance(data, list):
        for item in data:
            a_num = item.get("ayah", item.get("verse_number", item.get("id", 0)))
            text = _clean_html(item.get("text", ""))
            if text:
                all_verses[str(a_num)] = text

    specific = all_verses.get(str(ayah))
    return specific, all_verses


def _fetch_from_quranapi(surah, ayah):
    """Try quranapi.pages.dev for tafsir."""
    url = f"https://quranapi.pages.dev/api/tafsir/{surah}_{ayah}.json"
    data = _fetch_url(url)
    if not data:
        return None

    # Look for Ibn Kathir specifically
    if isinstance(data, dict):
        # May have multiple tafsirs
        for key in ["ibn-kathir", "en-tafisr-ibn-kathir", "ibnkathir"]:
            if key in data:
                return _clean_html(data[key].get("text", "") if isinstance(data[key], dict) else str(data[key]))
        # Or might be a list of tafsirs
        if "tafsirs" in data:
            for t in data["tafsirs"]:
                name = (t.get("name", "") + t.get("slug", "")).lower()
                if "kathir" in name or "ibn" in name:
                    return _clean_html(t.get("text", ""))
        # Fallback: take first available English tafsir
        if "text" in data:
            return _clean_html(data["text"])
    elif isinstance(data, list) and len(data) > 0:
        return _clean_html(data[0].get("text", ""))
    return None


def get_tafsir(surah, ayah):
    """Get Ibn Kathir tafsir for a specific verse.

    Returns: {
        "surah": int,
        "ayah": int,
        "text": str (the tafsir text),
        "source": str (which API provided it),
        "cached": bool
    }
    """
    cache = _load_cache()
    key = f"{surah}:{ayah}"

    # Check cache first
    if key in cache and cache[key].get("text"):
        return {
            "surah": surah,
            "ayah": ayah,
            "text": cache[key]["text"],
            "source": cache[key].get("source", "cache"),
            "cached": True,
        }

    # Try API sources in order
    text = None
    source = ""

    # Source 1: Quran.com API
    text = _fetch_from_quran_com(surah, ayah)
    if text:
        source = "quran.com"

    # Source 2: spa5k CDN (fetches entire surah)
    if not text:
        specific, all_verses = _fetch_from_spa5k_cdn(surah, ayah)
        if specific:
            text = specific
            source = "spa5k-cdn"
        # Cache all fetched verses from this surah
        if all_verses:
            for a, t in all_verses.items():
                vkey = f"{surah}:{a}"
                if vkey not in cache:
                    cache[vkey] = {"text": t, "source": "spa5k-cdn"}

    # Source 3: quranapi.pages.dev
    if not text:
        text = _fetch_from_quranapi(surah, ayah)
        if text:
            source = "quranapi"

    if text:
        cache[key] = {"text": text, "source": source}
        _save_cache(cache)
        return {
            "surah": surah,
            "ayah": ayah,
            "text": text,
            "source": source,
            "cached": False,
        }

    return {
        "surah": surah,
        "ayah": ayah,
        "text": "",
        "source": "",
        "cached": False,
        "error": f"Could not fetch tafsir for {surah}:{ayah} from any source",
    }


def get_tafsir_surah(surah):
    """Get Ibn Kathir tafsir for all verses in a surah.

    Tries to fetch the entire surah at once for efficiency.
    Returns list of {surah, ayah, text, source}.
    """
    cache = _load_cache()

    # First try spa5k CDN which returns entire surah
    _, all_verses = _fetch_from_spa5k_cdn(surah, 1)
    if all_verses:
        results = []
        for ayah_str, text in sorted(all_verses.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
            key = f"{surah}:{ayah_str}"
            cache[key] = {"text": text, "source": "spa5k-cdn"}
            results.append({
                "surah": surah,
                "ayah": int(ayah_str) if ayah_str.isdigit() else 0,
                "text": text,
                "source": "spa5k-cdn",
            })
        _save_cache(cache)
        return results

    return []


def get_tafsir_cache_stats():
    """Get statistics about the tafsir cache."""
    cache = _load_cache()
    return {
        "total_cached": len(cache),
        "sources": list(set(v.get("source", "unknown") for v in cache.values())),
    }
