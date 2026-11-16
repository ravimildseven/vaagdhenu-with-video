"""A synthesized bell struck after each shloka, tuned to the chant's Sa so it sits with the tanpura.

Two sounds:
  temple — a large temple ghaṇṭā: deep, long, with the slow "wah-wah" beating of a big bell.
  pooja  — a small brass pūjā ghaṇṭī: bright and short.

add_bells() opens each pause between verses a little (so the bell has room to ring instead of
landing on the next verse), strikes the bell there and once more after the last verse, and returns
the lyric timestamps shifted to match. It works on the cached dry chant, so toggling the bell in the
UI never re-renders the voice.
"""
import numpy as np

SOUNDS = {"temple": "Temple bell", "pooja": "Pooja bell"}
EXTRA_GAP_S = 1.0  # added to each 1.2 s pause between verses
TAIL_S = 3.2       # room after the final verse for the last bell to ring out
STRIKE_DELAY_S = 0.18


def _temple(sr, sa):
    f0 = 2.0 * sa  # main tone an octave above Sa
    # (ratio to f0, amplitude, decay seconds, beat Hz) — inharmonic partials of a cast bronze bell
    partials = [(0.5, 0.45, 4.0, 0.0), (1.0, 1.0, 3.2, 0.9), (1.19, 0.45, 2.2, 0.0),
                (1.5, 0.30, 1.8, 1.3), (2.0, 0.55, 1.5, 0.0), (2.52, 0.28, 0.9, 0.0),
                (3.01, 0.18, 0.6, 0.0), (4.08, 0.12, 0.35, 0.0), (5.4, 0.08, 0.2, 0.0)]
    return _ring(sr, f0, partials, dur=4.5, strike=0.35, seed=3)


def _pooja(sr, sa):
    f0 = 8.0 * sa  # small bell: three octaves above Sa
    partials = [(1.0, 1.0, 1.4, 2.5), (1.47, 0.35, 0.9, 0.0), (2.09, 0.55, 0.8, 3.1),
                (2.76, 0.30, 0.5, 0.0), (3.52, 0.18, 0.3, 0.0), (4.6, 0.10, 0.18, 0.0)]
    return _ring(sr, f0, partials, dur=2.4, strike=0.5, seed=5)


def _ring(sr, f0, partials, dur, strike, seed):
    n = int(dur * sr)
    t = np.arange(n, dtype=np.float32) / sr
    rng = np.random.RandomState(seed)
    out = np.zeros(n, np.float32)
    nyq = sr / 2 - 200
    for ratio, amp, decay, beat in partials:
        f = f0 * ratio
        if f >= nyq:
            continue
        ph = rng.rand() * 2 * np.pi
        tone = np.sin(2 * np.pi * f * t + ph)
        if beat:  # a second, slightly detuned copy -> slow amplitude beating
            tone = 0.6 * tone + 0.4 * np.sin(2 * np.pi * (f + beat) * t + ph * 1.7)
        out += amp * np.exp(-t / decay) * tone
    # the clapper's strike: a few ms of bright noise
    k = int(0.012 * sr)
    click = rng.randn(k).astype(np.float32) * np.exp(-np.linspace(0, 6, k)).astype(np.float32)
    click = np.diff(click, prepend=0.0)  # high-pass
    out[:k] += strike * click / (np.abs(click).max() + 1e-9)
    a = int(0.002 * sr)
    out[:a] *= np.linspace(0, 1, a)
    f = int(0.3 * sr)
    out[-f:] *= np.linspace(1, 0, f)
    return out / (np.abs(out).max() + 1e-9)


def bell_sound(kind, sr, sa):
    return _pooja(sr, sa) if kind == "pooja" else _temple(sr, sa)


def verse_ends(stamps):
    """End time (s) of the last line of each shloka, in order."""
    ends = {}
    for s in stamps or []:
        k = s.get("shloka_idx", 1)
        ends[k] = max(ends.get(k, 0.0), float(s["end"]))
    return [ends[k] for k in sorted(ends)]


def add_bells(y, sr, stamps, kind="temple", sa=170.0, level=0.32):
    """Return (audio, stamps) with a bell after every shloka. `level` is the bell's peak relative
    to the voice's peak."""
    y = np.asarray(y, np.float32)
    if kind not in SOUNDS or not stamps:
        return y, stamps
    ends = verse_ends(stamps)
    extra = int(EXTRA_GAP_S * sr)
    # 1) widen each pause between verses (cut right after the verse's last line)
    pieces, shifts, prev = [], [], 0
    for i, e in enumerate(ends[:-1]):
        cut = min(len(y), int((e + 0.05) * sr))
        pieces.append(y[prev:cut])
        pieces.append(np.zeros(extra, np.float32))
        prev = cut
        shifts.append((e, (i + 1) * EXTRA_GAP_S))
    pieces.append(y[prev:])
    pieces.append(np.zeros(int(TAIL_S * sr), np.float32))
    out = np.concatenate(pieces)

    def shift(t):
        s = 0.0
        for e, sh in shifts:
            if t > e + 0.05:
                s = sh
        return t + s

    new_stamps = [dict(s, start=round(shift(s["start"]), 2), end=round(shift(s["end"]), 2))
                  for s in stamps]
    # 2) strike the bell after each verse
    ring = bell_sound(kind, sr, sa) * float(level) * (np.abs(y).max() or 1.0)
    for e in verse_ends(new_stamps):
        p = int((e + STRIKE_DELAY_S) * sr)
        q = min(len(out), p + len(ring))
        if p < q:
            out[p:q] += ring[: q - p]
    return out, new_stamps
