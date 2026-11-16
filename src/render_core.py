"""Reusable render core for Vāgdhenu — the gold per-hemistich pipeline as a callable.

This is a faithful extraction of render.py's render_clip(): the helper functions are copied
verbatim and the model-load + per-piece synthesis live in a `Renderer` class whose `render_one()`
RETURNS audio (sr, np.float32) instead of writing a wav. render.py remains the frozen batch path;
this module exists so the Gradio demo (and any interactive caller) can load the models once and
render single inputs without argparse / file I/O.

Usage:
    r = Renderer(voice_path, voc_path, bank_path, device="cuda")
    sr, audio = r.render_one("तस्मै नमः ...", meter="anuṣṭubh")
"""
import os, sys, glob, json, re, numpy as np, torch, torchaudio
import soundfile as sf

def _sf_load(uri, **kwargs):
    data, sr = sf.read(uri, dtype="float32")
    t = torch.from_numpy(data)
    if t.ndim == 1: t = t.unsqueeze(0)
    else: t = t.t()
    return t, sr
torchaudio.load = _sf_load

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import prep_text as PT  # noqa: E402

SR = 24000
# Unknown/unmatched vṛtta -> render against this meter's reference rather than erroring. An
# unrecognized verse is almost always a real metered vṛtta we failed to classify, so a flowing
# 14-syllable triṣṭubh-class reference generalizes better than crashing (or the flat gadya prose
# template). Resolves via the wav-stem alias in the bank LUT.
FALLBACK_METER = "vasantatilaka"

# Text helpers live in chant_text.py (shared with the MLX backend); re-exported here.
from chant_text import (  # noqa: E402,F401
    n_aksharas, _aksharas, _rep_depths, _danda_fix, _anusvara_m, _satva, _visarga_ksha,
    _hna_metathesis, _vocalic_l, gate, _ends_halant, split_padas, split_shlokas, detect_meter_key,
    _VMATRA, _VECHO_SHORT, _VLONG, _AN_KA, _AN_CA, _AN_TTA, _AN_TA, _SATVA, _KSHA, _VIRAMA, _DANDAS,
)


class Renderer:
    """Loads DiT + vocos + BigVGAN + the reference bank ONCE; render_one() synthesizes a single input."""

    def __init__(self, voice_path, voc_path, bank_path, device=None, vocab_file=None,
                 speed=0.90, nfe=32, cfg=3.0, gap=0.55, gap_halant=0.20):
        import bigvgan
        from f5_tts.infer.utils_infer import load_model, load_vocoder, preprocess_ref_audio_text
        from f5_tts.model import DiT
        if device is None or (device == "cuda" and not torch.cuda.is_available()):
            device = "mps" if torch.backends.mps.is_available() else "cpu"
        self.device = device
        self.speed = speed; self.nfe = nfe; self.cfg = cfg
        self.gap = gap; self.gap_halant = gap_halant
        self._preprocess = preprocess_ref_audio_text
        import torchaudio as ta
        self._ta = ta

        CFG = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4)
        # vocab.txt (IndicF5's MIT tokenizer vocab) ships beside the bank; fall back to the IndicF5
        # cache for legacy local setups. Never index an empty glob.
        _cands = [vocab_file, os.path.join(os.path.dirname(bank_path), "vocab.txt")] \
            + glob.glob(os.path.expanduser(
                "~/.cache/huggingface/hub/models--ai4bharat--IndicF5/snapshots/*/checkpoints/vocab.txt"))
        vocab = next((v for v in _cands if v and os.path.exists(v)), None)
        if vocab is None:
            raise FileNotFoundError("vocab.txt not found (pass vocab_file= or ship it beside bank.json)")
        self.cfm = load_model(DiT, CFG, mel_spec_type="vocos", vocab_file=vocab, device=device)
        ck = torch.load(voice_path, map_location="cpu", weights_only=True)
        ema = {k.replace("ema_model.", ""): v for k, v in ck["ema_model_state_dict"].items()
               if k not in ("initted", "step")}
        self.cfm.load_state_dict(ema, strict=False); self.cfm.eval()

        real_voc = load_vocoder("vocos")
        class Cap:
            def __init__(s, r): s.r = r; s.last = None
            def decode(s, m): s.last = m.detach().cpu().numpy(); return s.r.decode(m)
        self.cap = Cap(real_voc)

        g = bigvgan.BigVGAN.from_pretrained("nvidia/bigvgan_v2_24khz_100band_256x", use_cuda_kernel=False)
        bsd = torch.load(voc_path, map_location="cpu"); bsd = bsd.get("model", bsd)
        g.load_state_dict(bsd); g.remove_weight_norm(); g = g.to(device).eval()
        for p in g.parameters(): p.requires_grad = False
        self.g = g

        self._bank = json.load(open(bank_path, encoding="utf-8"))
        self._bdir = os.path.dirname(bank_path)
        self._lut = {}
        for _k, _v in self._bank.items():
            if _k.startswith("_") or not isinstance(_v, dict) or "wav" not in _v: continue
            self._lut[_k.lower()] = _v
            self._lut[_v["wav"].replace(".wav", "").lower()] = _v
        self._primes = self._bank.get("repeat_primes", {})
        self._refcache = {}

    def meters(self):
        return [k for k, v in self._bank.items()
                if not k.startswith("_") and isinstance(v, dict) and "wav" in v]

    def _bvgan(self, mel):
        m = torch.from_numpy(mel).to(self.device)
        with torch.no_grad():
            if m.dim() == 3 and m.shape[1] != 100 and m.shape[2] == 100: m = m.transpose(1, 2)
            return self.g(m).squeeze().cpu().numpy().astype(np.float32)

    def _get_ref(self, meter):
        key = meter.lower().replace(".wav", "")
        if key in self._refcache: return self._refcache[key]
        if key not in self._lut:
            if FALLBACK_METER not in self._lut:
                raise ValueError(f"meter '{meter}' not in bank (and fallback '{FALLBACK_METER}' missing)")
            print(f"[meter] unknown vṛtta '{meter}' -> fallback '{FALLBACK_METER}'", flush=True)
            key = FALLBACK_METER
            if key in self._refcache:
                self._refcache[meter.lower().replace('.wav', '')] = self._refcache[key]
                return self._refcache[key]
        e = self._lut[key]
        ref_wav = os.path.join(self._bdir, e["wav"]); ref_text = e["ref_text"]
        sps = float(e.get("sec_per_syll", 0.26))
        ref_audio, ref_t = self._preprocess(ref_wav, ref_text, clip_short=True)
        ra, sr = self._ta.load(ref_audio); ref_len = ra.shape[-1] / sr
        val = (ref_audio, ref_t, sps, ref_len)
        self._refcache[key] = val
        return val

    def _stitch(self, segs, GAPS, fric=False, halant=False):
        if len(segs) == 1: return gate(segs[0], fric=fric, halant=halant)
        b = []; last = len(segs) - 1
        for i, s in enumerate(segs):
            b += [gate(s, fric=(fric and i == 0), halant=(halant and i == last)),
                  GAPS[i] if i < len(GAPS) else GAPS[-1]]
        return np.concatenate(b[:-1])

    def render_one(self, text, meter, seed=60, no_sandhi=True, speed=None, sps=None, return_timestamps=False,
                   line_cb=None):
        """Synthesize one shloka. text = free Devanagari (split into padas on newline/danda).
        Returns (sr, audio float32). Pipeline is identical to render.py's render_clip()."""
        padas = text if isinstance(text, list) else split_padas(text)
        if not padas: raise ValueError("empty text")
        ref_audio, ref_t, ref_sps, ref_len = self._get_ref(meter)
        if sps is not None: ref_sps = float(sps)
        spd = float(speed) if speed is not None else self.speed

        def _basetext(p):
            return PT.model_text_sandhi(p, echo_final=False) if not no_sandhi else PT.model_text(p)
        PIECES = [_basetext(p) for p in padas]
        if not no_sandhi:
            PIECES = [_satva(x) for x in PIECES]
        PIECES = [_danda_fix(_visarga_ksha(_anusvara_m(x))) for x in PIECES]
        PIECES = [_hna_metathesis(x) for x in PIECES]
        PIECES = [_vocalic_l(x) for x in PIECES]

        valid = [(p_orig, p_proc) for p_orig, p_proc in zip(padas, PIECES)
                 if n_aksharas(p_proc) > 0 and p_proc.strip()]
        if not valid:
            raise ValueError("No chantable Sanskrit syllables found in input text")
        padas = [v[0] for v in valid]
        PIECES = [v[1] for v in valid]

        _ra, _rt = ref_audio, ref_t
        _mono = max((_rep_depths(_aksharas(x))[0] for x in PIECES), default=1)
        _di   = max((_rep_depths(_aksharas(x))[1] for x in PIECES), default=1)
        _pick = None
        if _di >= 3:
            _pick = next((k for k in ["prime_jaya", "prime_chata"]
                          if k in self._primes and self._primes[k].get("di_max", 0) >= _di), None) \
                    or next((k for k, v in self._primes.items()
                             if isinstance(v, dict) and v.get("di_max", 0) >= _di), None)
        if _pick is None and _mono >= 2 and "prime_mono" in self._primes \
                and self._primes["prime_mono"].get("mono_max", 0) >= _mono:
            _pick = "prime_mono"
        if _pick:
            _pv = self._primes[_pick]
            _ra, _rt = self._preprocess(os.path.join(self._bdir, _pv["wav"]), _pv["ref_text"], clip_short=True)
            _prb, _psr = self._ta.load(_ra); ref_len = _prb.shape[-1] / _psr

        NSYLL = [n_aksharas(x) for x in PIECES]
        GAPS = [np.zeros(int(self.gap*SR) + (int(self.gap_halant*SR) if _ends_halant(_p) else 0),
                         dtype=np.float32) for _p in PIECES]
        from f5_tts.infer.utils_infer import infer_process
        bseg = []
        print(f"[vagdhenu] Starting synthesis of {len(PIECES)} line(s) (meter: {meter})...", flush=True)
        for i, p in enumerate(PIECES):
            if line_cb:
                line_cb(i, len(PIECES))
            print(f"[vagdhenu] Chanting line {i+1}/{len(PIECES)} ({NSYLL[i]} aksharas, nfe={self.nfe})...", flush=True)
            au = None
            for att in range(4):
                torch.manual_seed(seed + att)
                _fixd = (ref_len + NSYLL[i]*ref_sps) if (ref_sps > 0 and NSYLL) else None
                w, sr, _ = infer_process(_ra, _rt, p, self.cfm, self.cap, mel_spec_type="vocos",
                                         speed=spd, nfe_step=self.nfe, cfg_strength=self.cfg,
                                         device=self.device, fix_duration=_fixd)
                w = np.array(w, dtype=np.float32)
                if np.abs(w).max() > 1.5: w = w/32768.0
                if float(np.sqrt((w**2).mean())) > 0.04: au = w; break
            if au is None: au = w
            print(f"[vagdhenu] Running BigVGAN vocoder on line {i+1}...", flush=True)
            y = self._bvgan(self.cap.last); mx = np.abs(y).max(); y = y/mx*0.97 if mx > 1 else y
            bseg.append(y)

        _slp = PT.align_slp1(padas[0])
        fric = bool(_slp) and _slp[0] in ("S", "z", "s", "h")
        halant = _ends_halant(PIECES[-1])
        final = self._stitch(bseg, GAPS, fric=fric, halant=halant)
        print(f"[vagdhenu] Synthesis complete! Total duration: {len(final)/SR:.2f}s", flush=True)

        pada_timestamps = []
        t_cur = 0.0
        for i, s in enumerate(bseg):
            p_audio = gate(s, fric=(fric and i == 0), halant=(halant and i == len(bseg) - 1))
            dur = len(p_audio) / SR
            t_start = t_cur
            t_end = t_cur + dur
            pada_text = padas[i] if i < len(padas) else PIECES[i]
            pada_timestamps.append({
                "pada_idx": i,
                "text": pada_text,
                "start": round(t_start, 2),
                "end": round(t_end, 2)
            })
            t_cur = t_end
            if i < len(bseg) - 1 and i < len(GAPS):
                t_cur += len(GAPS[i]) / SR

        if return_timestamps:
            return SR, final, pada_timestamps
        return SR, final

    def render_composition(self, text, meter=None, seed=60, progress_cb=None):
        """Synthesize a complete file or composition containing 1 or more shlokas.
        Splits text into shlokas, chants each shloka (parsing each into padas),
        and stitches them together with an inter-shloka pause (1.2s).
        Returns (SR, final_audio_float32, list_of_meter_names, all_timestamps).
        """
        shlokas = split_shlokas(text)
        if not shlokas:
            raise ValueError("No chantable Sanskrit syllables found in input")

        shloka_waves = []
        used_meters = []
        all_timestamps = []
        shloka_offset = 0.0
        total = len(shlokas)
        print(f"[vagdhenu] Processing composition with {total} shloka(s)...", flush=True)

        for s_idx, shloka in enumerate(shlokas):
            m = meter
            if not m or m == "__auto__":
                det = detect_meter_key(shloka)
                m = det if (det and det.lower() in self._lut) else FALLBACK_METER
            used_meters.append(m)

            if progress_cb:
                progress_cb(s_idx / total, f"Chanting shloka {s_idx+1}/{total} (meter: {m})...")
            print(f"\n[vagdhenu] === Shloka {s_idx+1}/{total} (meter: {m}) ===", flush=True)

            def _line_cb(i, n, s_idx=s_idx, m=m):
                if progress_cb:
                    progress_cb((s_idx + i / max(n, 1)) / total,
                                f"Verse {s_idx+1}/{total} · line {i+1}/{n} · {m}")

            sr, wave, p_timestamps = self.render_one(shloka, m, seed=seed + s_idx, return_timestamps=True,
                                                     line_cb=_line_cb)
            shloka_waves.append(wave)

            for pt in p_timestamps:
                all_timestamps.append({
                    "shloka_idx": s_idx + 1,
                    "pada_idx": pt["pada_idx"] + 1,
                    "text": pt["text"],
                    "start": round(shloka_offset + pt["start"], 2),
                    "end": round(shloka_offset + pt["end"], 2),
                    "meter": m
                })

            shloka_offset += (len(wave) / SR) + 1.2

        if progress_cb:
            progress_cb(1.0, "Stitching final audio composition...")

        if len(shloka_waves) == 1:
            final_audio = shloka_waves[0]
        else:
            inter_gap = np.zeros(int(1.2 * SR), dtype=np.float32)
            stitched = []
            for i, w in enumerate(shloka_waves):
                stitched.append(w)
                if i < len(shloka_waves) - 1:
                    stitched.append(inter_gap)
            final_audio = np.concatenate(stitched)

        print(f"[vagdhenu] Composition complete! Total stitched duration: {len(final_audio)/SR:.2f}s across {total} shloka(s).", flush=True)
        return SR, final_audio, used_meters, all_timestamps
