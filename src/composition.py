"""Backend-neutral multi-verse rendering: split a text into shlokas, chant each (auto-detecting
its meter), stitch them with a 1.2 s pause, and return per-pāda timestamps for the synced lyrics.

Works with any renderer exposing `_lut` and `render_one(text, meter, seed=, return_timestamps=True)`
— the MLX backend (vagdhenu_mlx.Renderer) and the torch one (render_core.Renderer, which also has
its own render_composition with per-line progress).
"""
import numpy as np

from chant_text import FALLBACK_METER, SR, detect_meter_key, split_shlokas

INTER_SHLOKA_GAP_S = 1.2


def render_composition(renderer, text, meter=None, seed=60, progress_cb=None, log=print):
    """Returns (SR, audio float32, [meter per shloka], [timestamp dicts])."""
    shlokas = split_shlokas(text)
    if not shlokas:
        raise ValueError("No chantable Sanskrit syllables found in input")
    total = len(shlokas)
    waves, used, stamps, offset = [], [], [], 0.0
    log(f"[vagdhenu] Processing composition with {total} shloka(s)...", flush=True)
    for s_idx, shloka in enumerate(shlokas):
        m = meter
        if not m or m == "__auto__":
            det = detect_meter_key(shloka)
            m = det if (det and det.lower() in renderer._lut) else FALLBACK_METER
        used.append(m)
        if progress_cb:
            progress_cb(s_idx / total, f"Verse {s_idx + 1}/{total} · {m}")
        log(f"[vagdhenu] === Shloka {s_idx + 1}/{total} (meter: {m}) ===", flush=True)
        sr, wave, pts = renderer.render_one(shloka, m, seed=seed + s_idx, return_timestamps=True)
        waves.append(np.asarray(wave, np.float32))
        for pt in pts:
            stamps.append({"shloka_idx": s_idx + 1, "pada_idx": pt["pada_idx"] + 1, "text": pt["text"],
                           "start": round(offset + pt["start"], 2), "end": round(offset + pt["end"], 2),
                           "meter": m})
        offset += len(wave) / SR + INTER_SHLOKA_GAP_S
    if progress_cb:
        progress_cb(1.0, "Stitching…")
    if len(waves) == 1:
        audio = waves[0]
    else:
        gap = np.zeros(int(INTER_SHLOKA_GAP_S * SR), np.float32)
        parts = []
        for i, w in enumerate(waves):
            parts.append(w)
            if i < len(waves) - 1:
                parts.append(gap)
        audio = np.concatenate(parts)
    log(f"[vagdhenu] Composition complete: {len(audio) / SR:.2f}s across {total} shloka(s).", flush=True)
    return SR, audio, used, stamps
