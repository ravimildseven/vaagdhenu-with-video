"""Abuse guards shared by the demo server (ece) and the HF Space:
 - one shloka per request (block bulk paste / bulk download)
 - a per-IP daily render quota
Pure-stdlib, in-memory (resets on process restart — fine for a public demo)."""
import threading, datetime

import os
DAILY_LIMIT  = int(os.environ.get("DAILY_LIMIT", "1000"))    # renders per IP per day (1000 for local use)
MAX_AKSHARAS = 100   # one verse: longest common vṛtta (sragdharā) is 84 syllables; >100 = multiple shlokas

_lock = threading.Lock()
_counts = {}  # ip -> [date_iso, count]


def _n_aksharas(s):
    """Count akṣaras across any Indian script (Devanagari, Kannada, Telugu, Malayalam, etc.)."""
    try:
        import prep_text as PT
        s = PT.to_deva(s or "")
    except Exception:
        s = s or ""
    n = 0; L = len(s)
    for i, c in enumerate(s):
        o = ord(c)
        indep = (0x0905 <= o <= 0x0914) or (0x0C85 <= o <= 0x0C94)
        cons  = (0x0915 <= o <= 0x0939) or (0x0C95 <= o <= 0x0CB9)
        if indep:
            n += 1
        elif cons:
            nxt = s[i+1] if i+1 < L else ""
            if nxt not in ("्", "್"):
                n += 1
    return n


def client_ip(request):
    """Real visitor IP — prefer Cloudflare's header (tunnel), then X-Forwarded-For, then peer."""
    try:
        h = getattr(request, "headers", {}) or {}
        get = h.get if hasattr(h, "get") else (lambda k, d=None: d)
        ip = get("cf-connecting-ip") or (get("x-forwarded-for", "") or "").split(",")[0].strip()
        if not ip and getattr(request, "client", None):
            ip = request.client.host
        return ip or "unknown"
    except Exception:
        return "unknown"


def validate_composition(text, max_shlokas=50):
    """Validate a shloka or multi-verse composition for synthesis."""
    if not text or not text.strip():
        return "Please paste or upload a Sanskrit verse 🙏"
    num_ak = _n_aksharas(text)
    if num_ak == 0:
        return "No chantable Sanskrit syllables found. Please ensure text is in Devanagari or another Indian script 🙏"
    if num_ak > 4200:
        return f"Input is very large ({num_ak} syllables). Please process up to ~50 shlokas at a time to prevent timeouts 🙏"
    return None


def check_and_count(ip):
    """True if under today's limit (and records the use); False if the daily quota is exhausted."""
    today = datetime.date.today().isoformat()
    with _lock:
        rec = _counts.get(ip)
        if not rec or rec[0] != today:
            rec = [today, 0]; _counts[ip] = rec
        if rec[1] >= DAILY_LIMIT:
            return False
        rec[1] += 1
        return True
