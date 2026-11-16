"""Synthesized tanpura drone tuned to a chant's Sa, mixed under the voice.

Ported from render_production._tanpura (the drone used for the MBTN videos) so the demo can use
it without importing render_production (which parses argv at import time). Split into
detect_sa() (slow-ish, pYIN, run once per chant) and mix() (fast, run on every level change),
so the UI can toggle the drone or change its level instantly from the cached dry chant.
"""
import numpy as np

DEFAULT_SA = 170.0


def detect_sa(y, sr, max_seconds=45.0):
    """Estimate the chant's tonic (Sa, Hz) as the most common pitch, from up to the first
    `max_seconds` of audio, analysed at 16 kHz for speed."""
    import librosa
    seg = np.asarray(y, np.float32)[: int(max_seconds * sr)]
    if seg.size < sr // 2:
        return DEFAULT_SA
    if sr != 16000:
        seg = librosa.resample(seg, orig_sr=sr, target_sr=16000)
    f0, _, _ = librosa.pyin(seg, fmin=90, fmax=350, sr=16000, frame_length=1024, hop_length=256)
    f0 = f0[np.isfinite(f0)]
    if not len(f0):
        return DEFAULT_SA
    cents = 1200 * np.log2(f0 / 110.0)
    hist, edges = np.histogram(cents, bins=240, range=(0, 2400))
    pk = (edges[np.argmax(hist)] + edges[np.argmax(hist) + 1]) / 2
    return float(110.0 * 2 ** (pk / 1200.0))


def _pluck(f, dur, sr, rng):
    """One tanpura string pluck: ~40 slightly inharmonic partials with a jawari formant bump."""
    n = int(dur * sr)
    t = np.arange(n, dtype=np.float32) / sr
    kmax = int(min(40, (sr / 2) // f))
    k = np.arange(1, kmax + 1, dtype=np.float32)
    amp = (1.0 / k) * (1.0 + 1.8 * np.exp(-((k - 9) ** 2) / (2 * 5.0 ** 2)))
    phase = rng.rand(kmax).astype(np.float32) * 2 * np.pi
    freqs = f * k * (1 + 0.0003 * k)
    out = (amp[None, :] * np.sin(2 * np.pi * t[:, None] * freqs[None, :] + phase[None, :])).sum(axis=1)
    env = np.exp(-t / (dur * 0.55))
    at = int(0.006 * sr)
    env[:at] *= np.linspace(0, 1, at)
    return (out * env).astype(np.float32)


def drone(n_samples, sr, sa):
    """Pa-Sa-Sa-Sa(low) tanpura cycle, re-plucked every 1.15 s, long fade in/out."""
    rng = np.random.RandomState(7)
    notes = [0.75 * sa, sa, sa, 0.5 * sa]
    spacing, ring = 1.15, 2.6
    # two phase variants per string so consecutive cycles don't sound identical
    plucks = [[_pluck(f, ring, sr, rng) for f in notes] for _ in range(2)]
    buf = np.zeros(n_samples + int(ring * sr), np.float32)
    pos, ni = 0, 0
    step = int(spacing * sr)
    while pos < n_samples:
        g = plucks[(ni // 4) % 2][ni % 4]
        buf[pos:pos + len(g)] += g
        pos += step
        ni += 1
    tan = buf[:n_samples]
    tan /= (np.abs(tan).max() + 1e-9)
    fi, fo = min(int(1.2 * sr), n_samples // 3), min(int(1.5 * sr), n_samples // 3)
    if fi:
        tan[:fi] *= np.linspace(0, 1, fi)
    if fo:
        tan[-fo:] *= np.linspace(1, 0, fo)
    return tan


def mix(y, sr, level, sa):
    """Voice + drone at `level` (0.08 is the MBTN production level), peak-normalized to 0.97."""
    y = np.asarray(y, np.float32)
    if level <= 0:
        return y
    m = 0.92 * y + float(level) * drone(len(y), sr, sa)
    pk = np.abs(m).max()
    return (m / pk * 0.97 if pk > 0 else m).astype(np.float32)
