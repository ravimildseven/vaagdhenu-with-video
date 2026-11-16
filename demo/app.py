"""Vāgdhenu — Sanskrit/chant TTS demo (Hugging Face ZeroGPU Space).

Loads the released DiT voice + BigVGAN vocoder (from prathoshap/vagdhenu) and the reference bank
shipped in this repo, then synthesizes metered chant from a verse in any Indic script. The model
load + synthesis run inside an @spaces.GPU function so ZeroGPU allocates a GPU only on demand.

Designed to be usable by a non-technical user: paste a verse, press one button. The meter is
auto-detected; the only knob (a random seed) is hidden under "Advanced".

Local run (with a real GPU + the weights downloaded):
    VAGDHENU_HF=prathoshap/vagdhenu python demo/app.py
"""
import os, sys, json

import gradio as gr
try:
    import spaces
except ImportError:
    class _DummySpaces:
        def GPU(self, *args, **kwargs):
            def decorator(fn): return fn
            return decorator
    spaces = _DummySpaces()

HERE = os.path.dirname(os.path.abspath(__file__))
# works both in-repo (demo/app.py -> ../src) and in a flattened Space (app.py + ./src)
SRC = next((p for p in (os.path.join(os.path.dirname(HERE), "src"), os.path.join(HERE, "src"))
            if os.path.exists(os.path.join(p, "render_core.py"))), os.path.join(HERE, "src"))
sys.path.insert(0, SRC)

import limits
import tanpura
import bell
from chant_text import split_heading
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from ui_assets import (
    HEAD_HTML, CUSTOM_CSS, CUSTOM_JS_CODE, HEADER_HTML,
    LIBRARY_AND_MODAL_HTML, format_lyrics_component,
    QUICK_CHIPS_HTML, IDLE_LYRICS_PLACEHOLDER_HTML, render_queue_html, render_progress_card,
)


def _ensure_bigvgan():
    """NVIDIA BigVGAN ships as a repo, not a pip package — clone it once and put it on sys.path so
    `import bigvgan` works (render_core uses the torch path, use_cuda_kernel=False, so no build)."""
    try:
        import bigvgan  # noqa: F401
        return
    except ImportError:
        pass
    for c in [os.path.join(os.path.dirname(HERE), "BigVGAN"), os.path.join(HERE, "BigVGAN")]:
        if os.path.isdir(c):
            if c not in sys.path:
                sys.path.append(c)
            return
    import subprocess
    dst = os.path.join(HERE, "BigVGAN")
    if not os.path.isdir(os.path.join(dst, ".git")):
        subprocess.run(["git", "clone", "--depth", "1",
                        "https://github.com/NVIDIA/BigVGAN.git", dst], check=True)
    if dst not in sys.path:
        sys.path.insert(0, dst)


# (_ensure_bigvgan() runs only for the torch backend, from _get_renderer)

# ── config ───────────────────────────────────────────────────────────────────────────────
WEIGHTS_REPO = os.environ.get("VAGDHENU_HF", "prathoshap/vagdhenu")
VOICE_FILE   = os.environ.get("VAGDHENU_VOICE", "voice_steer_ema_2026-06-17.pt")
VOC_FILE     = os.environ.get("VAGDHENU_VOC", "voc_bigvgan_EMA_2026-06-11.pth")
VOCAB_FILE   = os.environ.get("VAGDHENU_VOCAB", "vocab.txt")  # tokenizer vocab, shipped in the weights repo
BANK_PATH    = os.path.join(SRC, "reference_bank", "bank.json")
# vocab.txt is bundled with the repo (IndicF5's MIT tokenizer vocab) so there's NO runtime dependency
# on the gated ai4bharat/IndicF5 repo. Falls back to the weights repo, then None (render_core globs).
BUNDLED_VOCAB = os.path.join(SRC, "reference_bank", VOCAB_FILE)

AUTO = "__auto__"

# Inference backend: "mlx" (Apple GPU, no torch at runtime) when it is installed and the converted
# weights exist (scripts/setup_mlx.sh → models/mlx), else "torch". Force with VAGDHENU_BACKEND.
MLX_DIR = os.path.join(os.path.dirname(HERE), "models", "mlx")


def _mlx_available():
    import importlib.util
    return (importlib.util.find_spec("mlx") is not None
            and os.path.exists(os.path.join(MLX_DIR, "dit.safetensors")))


BACKEND = os.environ.get("VAGDHENU_BACKEND", "").lower()
if BACKEND not in ("mlx", "torch"):
    BACKEND = "mlx" if _mlx_available() else "torch"

# meter list + display aliases — read the bank at startup (no GPU needed)
_bank = json.load(open(BANK_PATH, encoding="utf-8"))
METERS = [k for k, v in _bank.items() if not k.startswith("_") and isinstance(v, dict) and "wav" in v]
_PREFERRED = [m for m in ("anuṣṭubh", "upajāti", "śārdūlavikrīḍita", "vasantatilakā") if m in METERS]
METERS = _PREFERRED + [m for m in METERS if m not in _PREFERRED]
_FALLBACK_DISPLAY = "vasantatilakā" if "vasantatilakā" in METERS else METERS[0]
# detected ascii/diacritic name -> pretty bank key
_ALIAS = {}
for _k, _v in _bank.items():
    if _k.startswith("_") or not isinstance(_v, dict) or "wav" not in _v:
        continue
    _ALIAS[_k.lower()] = _k
    _ALIAS[_v["wav"].replace(".wav", "").lower()] = _k

# meter dropdown: Auto first (most users never touch it), then the named meters
METER_CHOICES = [("✨ Auto-detect", AUTO)] + [(m, m) for m in METERS]

# ── sample shlokas (a ready menu for users who don't have a verse handy) ────────────────────
# Authored in Devanagari and transliterated at load to showcase multiple scripts. All are COMPLETE
# verses so meter auto-detect works. (source-label, devanagari, display script)
from indic_transliteration import sanscript as _S  # noqa: E402


def _tx(deva, scheme):
    return deva if scheme == _S.DEVANAGARI else _S.transliterate(deva, _S.DEVANAGARI, scheme)


_MAL = ("हठलुठ दल घिष्टोत्कण्ठदष्टोष्ठ विद्युत्\nसटशठ कठिनोरः पीठभित्सुष्ठुनिष्ठाम् ।\n"
        "पठतिनुतव कण्ठाधिष्ठ घोरान्त्रमाला\nदह दह नरसिंहासह्यवीर्याहितं मे ॥")
# (label, devanagari, display script, meter)  — meter=AUTO unless detection needs help
_SAMPLES = [
    ("Kṛṣṇa — Vasudevasutaṃ (Devanagari)",
     "वसुदेवसुतं देवं कंसचाणूरमर्दनम् ।\nदेवकीपरमानन्दं कृष्णं वन्दे जगद्गुरुम् ॥", _S.DEVANAGARI, AUTO),
    ("Viṣṇu — Śuklāmbaradharaṃ (Devanagari)",
     "शुक्लाम्बरधरं विष्णुं शशिवर्णं चतुर्भुजम् ।\nप्रसन्नवदनं ध्यायेत् सर्वविघ्नोपशान्तये ॥", _S.DEVANAGARI, AUTO),
    ("Narasiṃha — retroflex tongue-twister (mālinī)", _MAL, _S.DEVANAGARI, "mālinī"),
    ("Karāgre vasate — jihvāmūlīya + upadhmānīya (Devanagari)",
     "कराग्रे वसते लक्ष्मीः करमध्ये सरस्वती ।\nकरमूले तु गोविन्दः प्रभाते करदर्शनम् ॥", _S.DEVANAGARI, AUTO),
    ("Sarasvatī — Yā kundendu · śārdūlavikrīḍita (Devanagari)",
     "या कुन्देन्दुतुषारहारधवला या शुभ्रवस्त्रावृता\nया वीणावरदण्डमण्डितकरा या श्वेतपद्मासना ।\n"
     "या ब्रह्माच्युतशङ्करप्रभृतिभिर्देवैः सदा वन्दिता\nसा मां पातु सरस्वती भगवती निःशेषजाड्यापहा ॥", _S.DEVANAGARI, AUTO),
    ("Gaṇeśa — Vakratuṇḍa (Devanagari)",
     "वक्रतुण्ड महाकाय सूर्यकोटिसमप्रभ ।\nनिर्विघ्नं कुरु मे देव सर्वकार्येषु सर्वदा ॥", _S.DEVANAGARI, AUTO),
    ("Guru — Gururbrahmā (Kannada script)",
     "गुरुर्ब्रह्मा गुरुर्विष्णुः गुरुर्देवो महेश्वरः ।\nगुरुः साक्षात् परं ब्रह्म तस्मै श्रीगुरवे नमः ॥", _S.KANNADA, AUTO),
    ("Sarasvatī — Namastubhyaṃ (Telugu script)",
     "सरस्वति नमस्तुभ्यं वरदे कामरूपिणि ।\nविद्यारम्भं करिष्यामि सिद्धिर्भवतु मे सदा ॥", _S.TELUGU, AUTO),
]
EXAMPLES = [[_tx(d, sc), m, 60] for _, d, sc, m in _SAMPLES]
EXAMPLE_LABELS = [name for name, _, _, _ in _SAMPLES]
EX_DEFAULT = EXAMPLES[0][0]

_RENDERER = None


def _ensure_assets():
    """Fetch the 2 release weights (CPU-only) + resolve the tokenizer vocab. vocab.txt is bundled
    locally (no gated-IndicF5 dependency); if missing, try the weights repo."""
    local_models = os.path.join(os.path.dirname(HERE), "models")
    local_voice = os.path.join(local_models, VOICE_FILE)
    local_voc = os.path.join(local_models, VOC_FILE)
    if os.path.exists(local_voice) and os.path.exists(local_voc):
        voice = local_voice
        voc = local_voc
    else:
        voice = hf_hub_download(WEIGHTS_REPO, VOICE_FILE)
        voc   = hf_hub_download(WEIGHTS_REPO, VOC_FILE)
    vocab = BUNDLED_VOCAB if os.path.exists(BUNDLED_VOCAB) else None
    if vocab is None:
        try:
            vocab = hf_hub_download(WEIGHTS_REPO, VOCAB_FILE)
        except Exception:
            vocab = None  # last resort: render_core globs the IndicF5 cache (local dev only)
    return voice, voc, vocab


class _MLXComposer:
    """Gives the MLX renderer the render_composition() interface the app uses."""
    device = "mlx (Apple GPU)"

    def __init__(self, r):
        self.r = r
        self._lut = r._lut

    def render_composition(self, text, meter=None, seed=60, progress_cb=None):
        import composition
        return composition.render_composition(self.r, text, meter, seed=seed, progress_cb=progress_cb)


def _get_renderer():
    global _RENDERER
    if _RENDERER is None:
        nfe = int(os.environ.get("VAGDHENU_NFE", "32"))
        if BACKEND == "mlx":
            from vagdhenu_mlx import Renderer as MLXRenderer
            print(f"[boot] Loading Vāgdhenu on MLX (nfe={nfe})...", flush=True)
            r = MLXRenderer(MLX_DIR, BANK_PATH, nfe=nfe)
            print("[boot] Warming up MLX (one-time compile)...", flush=True)
            r.warmup()
            _RENDERER = _MLXComposer(r)
        else:
            _ensure_bigvgan()
            from render_core import Renderer
            print(f"[boot] Loading Vāgdhenu on torch (nfe={nfe})...", flush=True)
            voice, voc, vocab = _ensure_assets()
            _RENDERER = Renderer(voice, voc, BANK_PATH, vocab_file=vocab, nfe=nfe)
        print(f"[boot] Models loaded on {_RENDERER.device}! Ready for chants.", flush=True)
    return _RENDERER


def _resolve_display(name):
    """detected meter name -> (pretty bank key, recognized?)."""
    k = _ALIAS.get((name or "").lower())
    return (k, True) if k else (_FALLBACK_DISPLAY, False)


@spaces.GPU(duration=300)
def _render_comp(text, used, seed, progress_cb=None):
    return _get_renderer().render_composition(text, used, seed=int(seed), progress_cb=progress_cb)


def _file_url(path):
    import urllib.parse
    return f"/gradio_api/file={urllib.parse.quote(path)}"


def _write_chant_wav(audio, sr):
    """Persist a chant under out/chants and return its Gradio file URL (used by the lyrics payload,
    the library cards and the video exporter)."""
    import soundfile as sf
    import time
    chants_dir = os.path.abspath(os.path.join(HERE, "..", "out", "chants"))
    os.makedirs(chants_dir, exist_ok=True)
    path = os.path.join(chants_dir, f"chant_{int(time.time() * 1000)}.wav")
    sf.write(path, audio, sr)
    return _file_url(path)


BELL_CHOICES = [("Off", "off"), ("🔔 Temple bell", "temple"), ("🛎️ Pooja bell", "pooja")]


def _finish_audio(dry, sr, stamps, on, level, bell_kind, sa=None):
    """Dry chant -> what is played: bells after each verse, then the tanpura under everything.
    Returns (audio, timestamps, sa); the timestamps move when the bells widen the verse pauses."""
    bell_kind = bell_kind if bell_kind in bell.SOUNDS else "off"
    tan = bool(on) and float(level) > 0
    if (tan or bell_kind != "off") and sa is None:
        sa = tanpura.detect_sa(dry, sr)
    audio = dry
    if bell_kind != "off":
        audio, stamps = bell.add_bells(audio, sr, stamps, bell_kind, sa)
    if tan:
        audio = tanpura.mix(audio, sr, float(level), sa)
    elif bell_kind != "off":
        pk = float(abs(audio).max())
        audio = audio / pk * 0.97 if pk > 0 else audio
    return audio.astype("float32"), stamps, sa


def _lyrics_for(chant, audio, stamps, url):
    return format_lyrics_component(stamps, chant["text"], chant["meters"], len(audio) / chant["sr"],
                                   audio_url=url, heading=chant.get("heading", ""),
                                   colophon=chant.get("colophon", ""))


def _status_line(chant, on, level, bell_kind="off"):
    meters, dur = chant["meters"], chant["dur"]
    if len(meters) == 1:
        s = f"🪔 Chanted 1 shloka · meter **{meters[0]}** · **{dur:.1f}s**"
    else:
        s = (f"🪔 Chanted **{len(meters)} shlokas** · meters **{', '.join(sorted(set(meters)))}** · "
             f"**{dur:.1f}s**, stitched into one track")
    if chant.get("heading"):
        s = s.replace("🪔 Chanted", f"🪔 **{chant['heading']}** — chanted", 1)
    if on and float(level) > 0 and chant.get("sa"):
        s += f" · tanpura on (Sa ≈ {chant['sa']:.0f} Hz)"
    if bell_kind in bell.SOUNDS:
        s += f" · {bell.SOUNDS[bell_kind].lower()} after each verse"
    return s + ". Listen below, add it to the library, or export a video."


def remix_tanpura(chant, on, level, bell_kind):
    """Tanpura / bell change: re-mix from the cached dry chant (no re-render)."""
    if not chant:
        return gr.update(), gr.update(), gr.update(), chant
    audio, stamps, chant["sa"] = _finish_audio(chant["dry"], chant["sr"], chant["timestamps"], on, level,
                                               bell_kind, chant.get("sa"))
    url = _write_chant_wav(audio, chant["sr"])
    return ((chant["sr"], audio), _status_line(chant, on, level, bell_kind),
            _lyrics_for(chant, audio, stamps, url), chant)


# ── background render queue ──────────────────────────────────────────────────────────────
QUEUE = None  # RenderQueue, created in __main__ once the model is loaded


def _queue_render(text, meter, seed, progress_cb):
    return _render_comp(text, meter, seed, progress_cb=progress_cb)


def _queue_finish(dry, sr, job, stamps):
    """Worker-side post-processing: the job's bell and tanpura settings."""
    return _finish_audio(dry, sr, stamps, job.get("tanpura_on"), job.get("tanpura_level", 0),
                         job.get("bell", "off"))


def _job_outputs(job):
    """Everything needed to show a finished job in the player/lyrics area."""
    import soundfile as sf
    res = job["result"]
    final, sr = sf.read(res["wav"], dtype="float32")
    try:
        dry, _ = sf.read(res["dry"], dtype="float32")
    except Exception:
        dry = final
    heading, _, colophon = split_heading(job["text"])
    chant = {"sr": sr, "dry": dry, "sa": res.get("sa"), "text": job["text"], "meters": res["meters"],
             "timestamps": res.get("dry_timestamps", res["timestamps"]), "dur": len(dry) / sr,
             "heading": heading, "colophon": colophon}
    bell_kind = job.get("bell", "off")
    return {out: (sr, final), status: _status_line(chant, job["tanpura_on"], job["tanpura_level"], bell_kind),
            lyrics_view: _lyrics_for(chant, final, res["timestamps"], _file_url(res["wav"])),
            chant_state: chant, tan_on: job["tanpura_on"], tan_level: job["tanpura_level"],
            bell_choice: bell_kind}


def _submit(text, meter_choice, seed, tan_on_v, tan_level_v, bell_v, request, follow):
    text = (text or "").strip()
    if not text:
        raise gr.Error("Please paste or upload a Sanskrit verse first 🙏")
    msg = limits.validate_composition(text)
    if msg:
        raise gr.Error(msg)
    if not limits.check_and_count(limits.client_ip(request)):
        raise gr.Error(f"You've reached today's limit of {limits.DAILY_LIMIT} chants from this network. "
                       f"Please come back tomorrow 🙏")
    meter_param = None if (meter_choice == AUTO or not meter_choice) else meter_choice
    job = QUEUE.submit(text, meter_param, seed, tan_on_v, tan_level_v, bell=bell_v,
                       title=split_heading(text)[0] or None)
    ahead = max(0, QUEUE.position(job["id"]))
    upd = {queue_view: render_queue_html(QUEUE.list(), job["id"] if follow else None)}
    if follow:
        upd.update({follow_state: job["id"], out: None, lyrics_view: render_progress_card(job, ahead),
                    status: "🪔 *Queued — it will load here when ready. You can keep working meanwhile.*"})
    else:
        gr.Info(f"Added to the render queue ({ahead} ahead of it).")
    return upd


def chant_now(text, meter_choice, seed, tan_on_v, tan_level_v, bell_v, request: gr.Request):
    return _submit(text, meter_choice, seed, tan_on_v, tan_level_v, bell_v, request, follow=True)


def add_to_queue(text, meter_choice, seed, tan_on_v, tan_level_v, bell_v, request: gr.Request):
    return _submit(text, meter_choice, seed, tan_on_v, tan_level_v, bell_v, request, follow=False)


def queue_tick(follow_id, last_html):
    """Runs every second: refresh the queue panel; drive the followed job's progress card and load
    it into the player when it finishes."""
    # always return at least one component: Gradio reads an empty dict as a single plain value
    if QUEUE is None:
        return {qhtml_state: last_html}
    upd = {qhtml_state: last_html}
    html = render_queue_html(QUEUE.list(), follow_id)
    if html != last_html:
        upd.update({queue_view: html, qhtml_state: html})
    if follow_id:
        job = QUEUE.get(follow_id)
        if job is None or job["status"] == "cancelled":
            upd.update({follow_state: None, lyrics_view: IDLE_LYRICS_PLACEHOLDER_HTML})
        elif job["status"] == "done":
            upd.update(_job_outputs(job))
            upd[follow_state] = None
        elif job["status"] == "failed":
            upd.update({follow_state: None, lyrics_view: IDLE_LYRICS_PLACEHOLDER_HTML,
                        status: f"⚠️ Rendering failed: {job.get('error')}"})
        else:
            upd[lyrics_view] = render_progress_card(job, max(0, QUEUE.position(follow_id)))
    return upd


def queue_command(cmd, follow_id):
    """Buttons in the queue panel send 'open:<id>', 'cancel:<id>', 'remove:<id>' or 'clear'."""
    action, _, rest = (cmd or "").partition(":")
    job_id = rest.split("|")[0]
    upd = {}
    if action == "open":
        job = QUEUE.get(job_id)
        if job and job["status"] == "done":
            upd.update(_job_outputs(job))
            upd[follow_state] = None
        elif job and job["status"] in ("queued", "rendering"):
            upd.update({follow_state: job_id, out: None,
                        lyrics_view: render_progress_card(job, max(0, QUEUE.position(job_id)))})
    elif action == "cancel":
        QUEUE.cancel(job_id)
    elif action == "remove":
        QUEUE.remove(job_id)
    elif action.startswith("clear"):
        QUEUE.clear_finished()
    html = render_queue_html(QUEUE.list(), upd.get(follow_state, follow_id))
    upd.update({queue_view: html, qhtml_state: html})
    return upd


FOOTER = """\
---
The first chant takes ~30–60s (the model loads onto the GPU); after that it's quick.
Voice & method: [`prathoshap/vagdhenu`](https://huggingface.co/prathoshap/vagdhenu) ·
code [github.com/prathoshap/vagdhenu](https://github.com/prathoshap/vagdhenu) · Apache-2.0.
"""

def _manuscript_theme():
    """Light manuscript palette for every built-in Gradio component (inputs, tabs, audio,
    accordion, examples). Each value is applied to the dark variant too, so the page stays on
    parchment even when the visitor's OS is in dark mode. Custom HTML is styled in ui_assets.CUSTOM_CSS."""
    paper, leaf, leaf2, field = "#f3e9d2", "#fbf6ea", "#f7efdc", "#fffcf4"
    ink, ink2, ink3 = "#2a1c12", "#57432f", "#7a6450"
    rule, rule_strong = "#e2d1ad", "#cbb183"
    vermilion, vermilion_dk, saffron, saffron_sf = "#b2381c", "#8e2a13", "#c9671a", "#fbe7cf"
    v = dict(
        body_background_fill=paper, body_text_color=ink, body_text_color_subdued=ink3,
        background_fill_primary=leaf, background_fill_secondary=leaf2,
        border_color_primary=rule, border_color_accent=saffron,
        color_accent=saffron, color_accent_soft=saffron_sf,
        link_text_color=vermilion_dk, link_text_color_hover=vermilion,
        link_text_color_visited=vermilion_dk, link_text_color_active=vermilion,
        block_background_fill=leaf, block_border_color=rule, block_border_width="1px",
        block_label_background_fill=leaf2, block_label_text_color=ink2,
        block_label_border_color=rule, block_title_text_color=ink, block_info_text_color=ink3,
        block_shadow="none", panel_background_fill=leaf2, panel_border_color=rule,
        input_background_fill=field, input_background_fill_focus=field,
        input_background_fill_hover=field, input_border_color=rule_strong,
        input_border_color_hover=saffron, input_border_color_focus=saffron,
        input_placeholder_color=ink3, input_shadow="none",
        input_shadow_focus="0 0 0 3px rgba(201,103,26,0.18)",
        button_primary_background_fill=vermilion, button_primary_background_fill_hover=vermilion_dk,
        button_primary_text_color="#fffaf2", button_primary_text_color_hover="#fffaf2",
        button_primary_border_color=vermilion_dk, button_primary_border_color_hover=vermilion_dk,
        button_secondary_background_fill=field, button_secondary_background_fill_hover="#fff8ea",
        button_secondary_text_color=ink2, button_secondary_text_color_hover=ink,
        button_secondary_border_color=rule_strong, button_secondary_border_color_hover=saffron,
        checkbox_background_color=field, checkbox_border_color=rule_strong,
        checkbox_background_color_selected=vermilion, checkbox_border_color_selected=vermilion,
        slider_color=vermilion, loader_color=saffron,
        table_even_background_fill=field, table_odd_background_fill=leaf2,
        table_border_color=rule, table_row_focus=saffron_sf,
        code_background_fill=leaf2, shadow_drop="none", shadow_drop_lg="0 6px 18px -6px rgba(74,46,20,0.18)",
    )
    parchment = gr.themes.Color(
        name="parchment", c50=leaf, c100=leaf2, c200=rule, c300=rule_strong, c400="#a48c70",
        c500=ink3, c600=ink2, c700="#3f2e20", c800=ink, c900="#1f140c", c950="#160e08",
    )
    theme = gr.themes.Base(
        primary_hue=gr.themes.colors.orange,
        secondary_hue=gr.themes.colors.amber,
        neutral_hue=parchment,
        radius_size=gr.themes.sizes.radius_md,
        font=["Source Sans 3", "system-ui", "sans-serif"],
        font_mono=["Fira Code", "ui-monospace", "monospace"],
    )
    v.update({f"{k}_dark": val for k, val in list(v.items()) if hasattr(theme, f"{k}_dark")})
    return theme.set(**v)


MANUSCRIPT_THEME = _manuscript_theme()


def _on_file_upload(f):
    if f is None:
        return gr.update()
    try:
        path = f.name if hasattr(f, "name") else str(f)
        with open(path, "r", encoding="utf-8", errors="ignore") as fp:
            return fp.read().strip()
    except Exception as e:
        return f"Error reading file: {e}"

with gr.Blocks(title="Vāgdhenu — Sacred Sanskrit Chant Studio") as demo:
    gr.HTML(HEADER_HTML)

    with gr.Row(elem_classes=["vagdhenu-studio-row"]):
        # Left Deck: Sacred Verse Composition
        with gr.Column(scale=5, elem_classes=["vagdhenu-deck-left"]):
            gr.HTML(QUICK_CHIPS_HTML)

            with gr.Tabs(elem_classes=["vagdhenu-input-tabs"]):
                with gr.Tab("✍️ Inscribe Shloka", id="tab_inscribe"):
                    txt = gr.Textbox(
                        label="Sanskrit Verse Text (Devanagari, Kannada, Telugu, IAST)",
                        placeholder="Paste or compose Sanskrit verse (Devanagari, Kannada, Telugu, IAST, etc.)...",
                        value=EX_DEFAULT,
                        lines=5,
                        max_lines=16,
                        elem_id="vagdhenu-text-input",
                    )
                with gr.Tab("📄 Upload .txt Manuscript", id="tab_upload"):
                    file_in = gr.File(
                        label="Upload UTF-8 text manuscript (single or multi-verse)",
                        file_types=[".txt"],
                        file_count="single"
                    )

            with gr.Row(elem_classes=["vagdhenu-controls-bar"]):
                meter = gr.Dropdown(
                    METER_CHOICES,
                    value=AUTO,
                    label="Chanda (Meter)",
                    info="Auto-detected from the verse",
                    scale=3,
                    min_width=200,
                )
                seed = gr.Number(
                    value=60,
                    label="Voice Seed",
                    info="Try another take",
                    precision=0,
                    scale=1,
                    min_width=120,
                )
            with gr.Row(elem_classes=["vagdhenu-tanpura-row"]):
                tan_on = gr.Checkbox(
                    value=False,
                    label="🪕 Tanpura drone",
                    info="Tuned automatically to the chant's Sa",
                    scale=1,
                    min_width=180,
                )
                tan_level = gr.Slider(
                    0.02, 0.20, value=0.08, step=0.01,
                    label="Drone level",
                    info="0.08 is the MBTN video level",
                    scale=2,
                    min_width=200,
                )
            with gr.Row(elem_classes=["vagdhenu-tanpura-row"]):
                bell_choice = gr.Dropdown(
                    BELL_CHOICES,
                    value="off",
                    label="🔔 Bell after each verse",
                    info="Rings in the pause between verses, tuned to the chant's Sa. "
                         "Changing it re-mixes instantly — no re-render.",
                    min_width=200,
                )
            with gr.Row(elem_classes=["vagdhenu-action-row"]):
                btn = gr.Button("🎧 Chant it", variant="primary", elem_id="vagdhenu-chant-btn", size="lg",
                                scale=3)
                qbtn = gr.Button("➕ Add to queue", variant="secondary", elem_id="vagdhenu-queue-btn",
                                 size="lg", scale=2)

            gr.Markdown(
                "<sub>✨ Enter a single shloka or multi-verse composition. Each verse is chanted with authentic Vedic meter cadence and stitched into continuous audio.</sub>",
                elem_classes=["vagdhenu-deck-subtext"]
            )

        # Right Deck: Audio Master & Synchronized Karaoke
        with gr.Column(scale=5, elem_classes=["vagdhenu-deck-right"]):
            status = gr.Markdown(
                "🪔 *Ready to chant. Select a quick verse or inscribe your own, then press **Chant it**.*",
                elem_id="vagdhenu-status-box"
            )
            out = gr.Audio(
                label="Master Audio (Stitched 24kHz WAV)",
                elem_id="vagdhenu-audio",
                type="numpy",
                autoplay=False
            )
            lyrics_view = gr.HTML(
                IDLE_LYRICS_PLACEHOLDER_HTML,
                elem_id="vagdhenu-lyrics-wrapper"
            )

    file_in.change(_on_file_upload, inputs=[file_in], outputs=[txt])

    # Background render queue: both buttons return immediately; a 1 s timer refreshes the queue
    # panel and loads the followed job ("Chant it") into the player when it is ready.
    queue_view = gr.HTML(render_queue_html([], None), elem_id="vagdhenu-queue")
    queue_cmd = gr.Textbox(elem_id="vg-queue-cmd", elem_classes=["vg-hidden"], show_label=False,
                           container=False)
    chant_state = gr.State(None)
    follow_state = gr.State(None)
    qhtml_state = gr.State("")
    ticker = gr.Timer(1.0)

    _qouts = [queue_view, out, status, lyrics_view, chant_state, follow_state, tan_on, tan_level, bell_choice,
              qhtml_state]
    _qins = [txt, meter, seed, tan_on, tan_level, bell_choice]
    btn.click(chant_now, inputs=_qins, outputs=_qouts, show_progress="hidden")
    qbtn.click(add_to_queue, inputs=_qins, outputs=_qouts, show_progress="hidden")
    ticker.tick(queue_tick, inputs=[follow_state, qhtml_state], outputs=_qouts, show_progress="hidden")
    queue_cmd.change(queue_command, inputs=[queue_cmd, follow_state], outputs=_qouts, show_progress="hidden")

    _mix_ins = [chant_state, tan_on, tan_level, bell_choice]
    _mix_outs = [out, status, lyrics_view, chant_state]
    tan_on.input(remix_tanpura, inputs=_mix_ins, outputs=_mix_outs, show_progress="hidden")
    tan_level.release(remix_tanpura, inputs=_mix_ins, outputs=_mix_outs, show_progress="hidden")
    bell_choice.input(remix_tanpura, inputs=_mix_ins, outputs=_mix_outs, show_progress="hidden")

    # Sacred Chant Library & Modal Dialog
    gr.HTML(LIBRARY_AND_MODAL_HTML)

    with gr.Accordion("📜 Complete Verse Treasury & Classical Examples", open=False, elem_classes=["vagdhenu-treasury"]):
        gr.Markdown("Pick a classic shloka to test auto-detection and chanting, or pick any verse from the **[Bhagavad Gītā](https://sanskritdocuments.org/doc_giitaa/bhagvadnew.html)**.")
        gr.Examples(
            examples=EXAMPLES,
            example_labels=EXAMPLE_LABELS,
            inputs=[txt, meter, seed],
            label="",
        )
    gr.Markdown(FOOTER, elem_classes=["vagdhenu-footer"])

if __name__ == "__main__":
    _get_renderer()
    from render_queue import RenderQueue
    QUEUE = RenderQueue(_queue_render, _queue_finish,
                        os.path.abspath(os.path.join(HERE, "..", "out", "queue")))
    try:  # warm librosa's pYIN (first call ~1.5 s) so the first tanpura toggle is instant
        import numpy as _np
        tanpura.detect_sa(_np.sin(2 * _np.pi * 170 * _np.arange(24000) / 24000).astype(_np.float32), 24000)
    except Exception as _e:
        print(f"[boot] tanpura warm-up skipped: {_e}", flush=True)
    chants_dir = os.path.abspath(os.path.join(HERE, "..", "out", "chants"))
    videos_dir = os.path.abspath(os.path.join(HERE, "..", "out", "videos"))
    assets_dir = os.path.abspath(os.path.join(HERE, "assets"))
    os.makedirs(chants_dir, exist_ok=True)
    os.makedirs(videos_dir, exist_ok=True)
    os.makedirs(assets_dir, exist_ok=True)

    from fastapi import Request
    from fastapi.responses import JSONResponse, FileResponse
    import subprocess
    import urllib.parse
    import time

    with open(os.path.join(HERE, "video_studio.js"), encoding="utf-8") as _f:
        _studio_js = _f.read()
    with open(os.path.join(HERE, "video_studio.css"), encoding="utf-8") as _f:
        _studio_css = _f.read()

    app, local_url, share_url = demo.launch(
        theme=MANUSCRIPT_THEME,
        head=HEAD_HTML,
        css=CUSTOM_CSS + "\n" + _studio_css,
        js=CUSTOM_JS_CODE + "\n" + _studio_js,
        allowed_paths=[chants_dir, videos_dir, assets_dir, os.path.abspath(os.path.join(HERE, "..", "out"))],
        prevent_thread_lock=True,
    )

    # Asset serving route for deity presets
    @app.get("/api/assets/{filename}")
    async def api_get_asset(filename: str):
        safe_name = os.path.basename(filename)
        file_path = os.path.join(assets_dir, safe_name)
        if not os.path.isfile(file_path):
            return JSONResponse({"error": "Asset not found"}, status_code=404)
        return FileResponse(file_path)

    # Dedicated download route guaranteeing attachment disposition with .mp4 filename
    @app.get("/api/download_video/{filename}")
    async def api_download_video(filename: str):
        safe_name = os.path.basename(filename)
        file_path = os.path.join(videos_dir, safe_name)
        if not os.path.isfile(file_path):
            return JSONResponse({"error": "File not found"}, status_code=404)
        return FileResponse(
            file_path,
            media_type="video/mp4",
            filename=safe_name,
            content_disposition_type="attachment"
        )

    # Register custom FastAPI route on the active server app for MP4 conversion
    @app.post("/api/convert_to_mp4")
    async def api_convert_to_mp4(request: Request):
        try:
            body = await request.body()
            if not body:
                return JSONResponse({"error": "Empty body"}, status_code=400)

            ts = int(time.time() * 1000)
            webm_path = os.path.join(videos_dir, f"temp_{ts}.webm")
            
            custom_filename = request.query_params.get("filename")
            if custom_filename:
                import unicodedata
                # keep Indic vowel signs / viramas (combining marks), which isalnum() rejects
                safe_custom = "".join(c for c in os.path.basename(custom_filename)
                                      if c.isalnum() or c in ("-", "_", ".")
                                      or unicodedata.category(c).startswith("M"))
                if not safe_custom.endswith(".mp4"):
                    safe_custom += ".mp4"
                mp4_filename = safe_custom
            else:
                mp4_filename = f"shloka_{ts}.mp4"
                
            mp4_path = os.path.join(videos_dir, mp4_filename)

            with open(webm_path, "wb") as f:
                f.write(body)

            # The studio records video only; mux the ORIGINAL chant wav (exact audio, no browser
            # re-encode). Only files under out/ are accepted as the audio source.
            audio_path = None
            audio_src = request.query_params.get("audio") or ""
            if audio_src.startswith("/gradio_api/file="):
                cand = os.path.realpath(urllib.parse.unquote(audio_src[len("/gradio_api/file="):]))
                out_root = os.path.realpath(os.path.join(HERE, "..", "out"))
                if cand.startswith(out_root + os.sep) and os.path.isfile(cand):
                    audio_path = cand

            # Convert with FFmpeg to standard H.264/AAC MP4 (constant 30 fps)
            cmd = ["ffmpeg", "-y", "-i", webm_path]
            if audio_path:
                cmd += ["-i", audio_path, "-map", "0:v:0", "-map", "1:a:0", "-shortest"]
            cmd += [
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "18",
                "-r", "30",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-movflags", "+faststart",
                mp4_path,
            ]
            proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            if proc.returncode != 0:
                err = proc.stderr.decode("utf-8", errors="replace")[-400:]
                return JSONResponse({"error": f"FFmpeg conversion error: {err}"}, status_code=500)

            try:
                os.remove(webm_path)
            except Exception:
                pass

            download_url = f"/api/download_video/{mp4_filename}"
            return JSONResponse({
                "success": True,
                "download_url": download_url,
                "filename": mp4_filename,
                "saved_to": mp4_path,
                "with_audio": bool(audio_path),
            })
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    demo.block_thread()

