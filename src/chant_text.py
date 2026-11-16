"""Text-side helpers of the Vāgdhenu render pipeline (no torch): akṣara counting, repeat
depth, the Kannada-script respelling fixes (daṇḍa-final visarga/anusvāra, satva, jihvāmūlīya
before kṣa, hna metathesis, vocalic l), the post-render gate, pāda splitting and meter detection.

These were the module-level helpers of render_core.py (copied verbatim from render.py); they
live here so the MLX backend (vagdhenu_mlx) can share them without importing torch.
render_core re-exports them, so existing imports keep working.
"""
import os, sys, re, numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import prep_text as PT  # noqa: E402

SR = 24000
# Unknown/unmatched vṛtta -> render against this meter's reference rather than erroring. An
# unrecognized verse is almost always a real metered vṛtta we failed to classify, so a flowing
# 14-syllable triṣṭubh-class reference generalizes better than crashing (or the flat gadya prose
# template). Resolves via the wav-stem alias in the bank LUT.
FALLBACK_METER = "vasantatilaka"

# ── helpers (verbatim from render.py) ───────────────────────────────────────────────
def n_aksharas(s):
    try:
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

def _aksharas(s):
    out=[]; cur=""
    for i,c in enumerate(s):
        o=ord(c); base=(0x0C85<=o<=0x0C94) or (0x0905<=o<=0x0914) or (0x0C95<=o<=0x0CB9) or (0x0915<=o<=0x0939)
        prev=s[i-1] if i>0 else ""
        if base and prev not in ("್","्"):
            if cur: out.append(cur)
            cur=c
        else: cur+=c
    if cur: out.append(cur)
    return out

def _rep_depths(aks):
    n=len(aks); mono=1; i=0
    while i<n:
        j=i+1
        while j<n and aks[j]==aks[i]: j+=1
        mono=max(mono,j-i); i=j if j>i+1 else i+1
    di=1; i=0
    while i+1<n:
        if aks[i]!=aks[i+1]:
            cnt=1; j=i+2
            while j+1<n and aks[j]==aks[i] and aks[j+1]==aks[i+1]: cnt+=1; j+=2
            di=max(di,cnt); i=j if cnt>1 else i+1
        else: i+=1
    return mono, di

_VMATRA = set("ಾಿೀುೂೃೄೆೇೈೊೋೌ")
_VECHO_SHORT = {"ಿ": "ಹಿ", "ು": "ಹು", "ೃ": "ಹೃ"}
_VLONG = set("ಾೀೂೄೆೇೈೊೋೌ")
def _danda_fix(s):
    s = s.rstrip()
    if not s: return s
    if s.endswith("ಃ"):
        core = s[:-1]; pv = core[-1] if core else ""
        if pv in _VECHO_SHORT:      s = core + _VECHO_SHORT[pv]
        elif pv in _VLONG:          pass
        else:                        s = core + "ಹ"
    elif s.endswith("ಂ"):
        s = s[:-1] + "ಮ್"
    return s

_AN_KA=set("ಕಖಗಘಙ"); _AN_CA=set("ಚಛಜಝಞ"); _AN_TTA=set("ಟಠಡಢಣ"); _AN_TA=set("ತಥದಧನ")
def _anusvara_m(s):
    res=[]; n=len(s)
    for i,c in enumerate(s):
        if c=="ಂ":
            j=i+1
            while j<n and s[j]==" ": j+=1
            nxt=s[j] if j<n else ""
            if   not nxt:        res.append("ಂ")
            elif nxt in _AN_KA:  res.append("ಙ್")
            elif nxt in _AN_CA:  res.append("ಞ್")
            elif nxt in _AN_TTA: res.append("ಣ್")
            elif nxt in _AN_TA:  res.append("ನ್")
            else:                res.append("ಮ್")
        else: res.append(c)
    return "".join(res)

_SATVA = {"ಚ": "ಶ್", "ಛ": "ಶ್", "ಟ": "ಷ್", "ಠ": "ಷ್", "ತ": "ಸ್", "ಥ": "ಸ್"}
def _satva(s):
    out = []; n = len(s); i = 0
    while i < n:
        c = s[i]
        if c == "ಃ":
            j = i + 1
            while j < n and s[j] == " ": j += 1
            nxt = s[j] if j < n else ""
            if nxt in _SATVA:
                out.append(_SATVA[nxt]); i = j; continue
        out.append(c); i += 1
    return "".join(out)

_KSHA = "ಕ್ಷ"
def _visarga_ksha(s):
    """Visarga before क्ष (ಕ್ಷ) → jihvāmūlīya vowel-echo. F5 swallows the visarga before the heavy
    kṣa conjunct, so respell it as the ह-echo of the preceding vowel — same map as _danda_fix, but
    mid-clip and ONLY before ಕ್ಷ (e.g. आहुः क्षेत्रं → आहुहु क्षेत्रं, "āhuhu kṣetraṃ").
    Short i/u/ṛ → hi/hu/hṛ · long vowel → leave the visarga · bare 'a' → ha."""
    out = []; n = len(s); i = 0
    while i < n:
        c = s[i]
        if c == "ಃ":
            j = i + 1
            while j < n and s[j] == " ": j += 1
            if s[j:j + 3] == _KSHA:
                pv = out[-1] if out else ""
                if pv in _VECHO_SHORT:   out.append(_VECHO_SHORT[pv]); i += 1; continue
                elif pv in _VLONG:       out.append("ಃ");             i += 1; continue
                else:                     out.append("ಹ");             i += 1; continue
        out.append(c); i += 1
    return "".join(out)

def _hna_metathesis(s):
    return s.replace("ಹ್ಣ", "ಣ್ಹ").replace("ಹ್ನ", "ನ್ಹ")

def _vocalic_l(s):
    return s.replace("ೢ", "್ಲೃ").replace("ೣ", "್ಲೄ").replace("ಌ", "ಲೃ").replace("ೡ", "ಲೄ")

def gate(au, voice=0.08, sil=0.012, fin=0.015, fout=0.040, lead=0.03, keep=0.06, fade=True, fric=False, halant=False):
    win = int(0.02*SR); r = [float(np.sqrt((au[i:i+win]**2).mean())) for i in range(0, len(au)-win, win)]; n = len(r)
    if n == 0: return au
    if fric:
        FR = 0.006
        s = next((i for i in range(n-1) if r[i] > FR and r[i+1] > FR), int(np.argmax(r)))
        while s > 0 and r[s-1] > FR: s -= 1
        _vdef = s
    else:
        vs = next((i for i in range(n-1) if r[i] > voice and r[i+1] > sil), int(np.argmax(r))); s = vs
        while s > 0 and r[s-1] > sil: s -= 1
        _vdef = vs
    ve_thr = 0.012 if halant else 0.035
    ve = max((i for i in range(n) if r[i] > ve_thr), default=_vdef)
    keep_s = 0.12 if halant else keep
    start = max(0, s*win - int(lead*SR))
    end = min(len(au), ve*win + int(keep_s*SR)); out = au[start:end].copy()
    if fade:
        fi = (0 if fric else int(fin*SR)); fo = int((0.018 if halant else fout)*SR)
        if fi and len(out) > fi: out[:fi] *= np.linspace(0, 1, fi)
        if fo and len(out) > fo: out[-fo:] *= (np.cos(np.linspace(0, np.pi, fo))*0.5 + 0.5)
    return out

_VIRAMA = "्್"
def _ends_halant(txt):
    t = txt.rstrip(" ।॥|.,;:!?‌‍")
    return len(t) > 0 and t[-1] in _VIRAMA

_DANDAS = "।॥|"
def split_padas(text):
    """Split a free-text shloka into hemistich/pada pieces: newlines first, then dandas. Empty drop."""
    t = re.sub(r"॥\s*[\d\u0966-\u096F\.\-]+\s*॥", "।", text or "")
    pieces = []
    for line in t.replace("॥", "।").replace("|", "।").splitlines():
        for seg in line.split("।"):
            cleaned = re.sub(r"[\d\u0966-\u096F\(\)\[\]\.\-]+", "", seg).strip()
            if cleaned and n_aksharas(cleaned) > 0:
                pieces.append(cleaned)
    return pieces or ([text.strip()] if text and text.strip() and n_aksharas(text) > 0 else [])


# Words that mark a line as a title ("कुलदेवता स्तोत्रम्") or an invocation rather than a verse.
_TITLE_WORDS = ("स्तोत्र", "स्तोत्रं", "स्तुति", "स्तुतिः", "अष्टक", "कवच", "नामावलि", "नामावली",
                "सहस्रनाम", "सुप्रभात", "पञ्चक", "पंचक", "दशक", "चालीसा", "मङ्गल", "मंगल", "शतक",
                "हृदय", "गीता", "प्रार्थना", "वन्दना", "वंदना", "आरती", "ध्यानम्", "ध्यान",
                "stotra", "stotram", "stuti", "ashtak", "aṣṭak", "astak", "kavach", "namavali",
                "nāmāvali", "sahasranam", "suprabhat", "panchak", "dashak", "chalisa", "mangal",
                "shatak", "hrudaya", "hridaya", "prarthana", "vandana", "aarti", "arati", "dhyanam")
_DIGITS = re.compile(r"[\d०-९೦-೯౦-౯]")
_MAX_HEADING_AKSHARAS = 22  # longer than any title; shorter than a full verse line of most metres


def _strip_dandas(line):
    return re.sub(r"^[\s।॥|]+|[\s।॥|]+$", "", line)


def _is_heading_line(line, followed_by_blank):
    """A short, non-verse line: wrapped in ॥…॥ with no verse number, followed by a blank line, or
    containing a title word (stotram, aṣṭakam, kavacam …). Akṣaras are counted in any Indic script."""
    core = _strip_dandas(line)
    if not core or _DIGITS.search(core):
        return False
    if re.search(r"[A-Za-z]", core):  # romanised title
        if len(core.split()) > 6:
            return False
    elif not (0 < n_aksharas(core) <= _MAX_HEADING_AKSHARAS):
        return False
    try:
        deva = PT.to_deva(core)
    except Exception:
        deva = core
    low = (deva + " " + core).lower()
    wrapped = bool(re.match(r"^\s*(॥|\|\|)", line)) and bool(re.search(r"(॥|\|\|)\s*$", line))
    titled = any(w in low for w in _TITLE_WORDS)
    return wrapped or titled or followed_by_blank


def _is_colophon_line(line):
    """The closing line of a stotra: "॥ इति श्री … सम्पूर्णम् ॥"."""
    core = _strip_dandas(line)
    try:
        deva = PT.to_deva(core)
    except Exception:
        deva = core
    low = (deva + " " + core).lower()
    return (deva.startswith("इति") or low.startswith("iti ")) and n_aksharas(core) <= 40


def split_heading(text):
    """Separate a stotra's title (and closing colophon) from its verses.

    Returns (heading, body, colophon): heading/colophon are display strings ('' when absent) that are
    NOT chanted, and body is the chantable text. Only leading lines (at most two) can be a heading,
    and only when real verse text follows, so a plain single verse is never mistaken for a title."""
    raw = (text or "").strip("\n")
    lines = raw.split("\n")
    i, heads = 0, []
    while i < len(lines) and not lines[i].strip():
        i += 1
    while i < len(lines) and len(heads) < 2:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        nxt_blank = (i + 1 < len(lines)) and not lines[i + 1].strip()
        if not _is_heading_line(line, nxt_blank):
            break
        heads.append(_strip_dandas(line))
        i += 1
    body_lines = lines[i:]
    colophon = ""
    while body_lines and not body_lines[-1].strip():
        body_lines.pop()
    if body_lines and _is_colophon_line(body_lines[-1]):
        colophon = _strip_dandas(body_lines.pop())
    body = "\n".join(body_lines).strip()
    if not heads and not colophon:
        return "", (text or "").strip(), ""
    if n_aksharas(body) < 8:  # nothing left to chant: it was all verse after all
        return "", (text or "").strip(), ""
    return " · ".join(heads), body, colophon


def split_shlokas(text):
    """Split free text or multi-verse file into individual shlokas. A title line ("॥ कुलदेवता
    स्तोत्रम् ॥") and a closing "इति … सम्पूर्णम्" line are left out — see split_heading."""
    text = split_heading(text)[1]
    if not text:
        return []

    # Method 1: Check for explicit verse number patterns: ॥ १ ॥, ॥ 1 ॥, ॥ १.१ ॥, || 1 ||
    verse_num_pattern = r"(?:॥|\|\|)\s*[\d\u0966-\u096F\.\-]+\s*(?:॥|\|\|)"
    if re.search(verse_num_pattern, text):
        parts = re.split(verse_num_pattern, text)
        res = [p.strip() for p in parts if p.strip() and n_aksharas(p) > 0]
        if res:
            return res

    # Method 2: Paragraph breaks (blank lines between verses)
    if "\n\n" in text:
        parts = re.split(r"\n\s*\n+", text)
        res = [p.strip() for p in parts if p.strip() and n_aksharas(p) > 0]
        if len(res) > 1:
            return res

    # Method 3: If multiple '॥' and sufficient length (>= 32 aksharas total)
    if text.count("॥") > 1:
        parts = [p.strip() for p in text.split("॥") if p.strip() and n_aksharas(p) > 0]
        if len(parts) > 1 and all(n_aksharas(p) >= 16 for p in parts):
            return parts

    return [text]


def detect_meter_key(text):
    """Best-effort chandas (meter) detection from raw text in ANY Indic script, so a non-technical
    user need not name the meter. Returns the detected meter name (e.g. 'anushtubh', 'vasantatilaka')
    which the bank LUT resolves via its wav-stem aliases; 'anushtubh_half' is normalized to
    'anushtubh'. Returns "" when the verse is partial/unrecognized — the caller then picks the
    graceful FALLBACK_METER itself and can tell the user it was a guess. Pure text — no GPU. Needs a
    COMPLETE verse (4 pādas, or 32 syllables for anuṣṭubh) for a confident vṛtta match."""
    try:
        from indic_transliteration import sanscript
        from tts_syllabify import syllabify
        from tts_weight import tag_weights
        from tts_meter import detect_meter
    except Exception:
        return ""
    try:
        d = PT.to_deva(text).replace("॥", "|").replace("।", "|").replace("\n", " | ")
        d = "".join(c for c in d if not (c.isdigit() or ("०" <= c <= "९")) and c not in "\"'“”‘’()")
        slp = re.sub(r"\s+", " ", sanscript.transliterate(d, sanscript.DEVANAGARI, sanscript.SLP1)).strip()
        syls = syllabify(slp)
        tag_weights(syls)
        name = detect_meter(syls).get("name", "unknown")
    except Exception:
        return ""
    if name in ("anushtubh_half", "anushtubh"):
        return "anushtubh"
    if name in ("unknown", None, ""):
        return ""
    return name


