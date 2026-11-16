"""UI Assets, CSS Design System, JavaScript and HTML builders for Vāgdhenu Sanskrit Chant Studio.
Aesthetic: Light manuscript — parchment, iron-gall ink, sindoor vermilion, saffron and gold leaf.
"""
import re
import html
import json

HEAD_HTML = """\
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Source+Sans+3:wght@400;500;600;700&family=Tiro+Devanagari+Sanskrit&family=Noto+Serif+Telugu:wght@400;600&family=Martel:wght@400;800&family=Eczar:wght@500;700&family=Rozha+One&family=Yatra+One&family=Kalam:wght@400;700&family=Cinzel:wght@600;700;800;900&family=Fira+Code:wght@400;500;600&family=Noto+Serif+Devanagari:wght@400;500;600;700&family=Noto+Serif+Kannada:wght@400;500;600;700&family=Noto+Sans+Kannada:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
"""

CUSTOM_CSS = """\
/* ==========================================================================
   VĀGDHENU — LIGHT MANUSCRIPT DESIGN SYSTEM
   Parchment ground · iron-gall ink · sindoor vermilion · saffron · gold leaf
   Component colours come from the Gradio theme (demo/app.py: MANUSCRIPT_THEME);
   this sheet styles the custom HTML (header, chips, lyrics, library, modals).
   ========================================================================== */

:root, .dark {
  color-scheme: light;

  /* paper */
  --vg-paper:        #f3e9d2;
  --vg-paper-deep:   #eadcbd;
  --vg-leaf:         #fbf6ea;   /* raised surfaces (cards) */
  --vg-leaf-2:       #f7efdc;   /* recessed panels */
  --vg-field:        #fffcf4;   /* writing surfaces (inputs) */

  /* ink */
  --vg-ink:          #2a1c12;
  --vg-ink-2:        #57432f;
  --vg-ink-3:        #7a6450;

  /* rules */
  --vg-rule:         #e2d1ad;
  --vg-rule-strong:  #cbb183;

  /* accents */
  --vg-vermilion:    #b2381c;
  --vg-vermilion-dk: #8e2a13;
  --vg-vermilion-sf: #f6dccd;
  --vg-saffron:      #c9671a;
  --vg-saffron-sf:   #fbe7cf;
  --vg-gold:         #a97c2c;
  --vg-leafgreen:    #3f7d4a;

  --vg-shadow-sm: 0 1px 2px rgba(74, 46, 20, 0.06), 0 1px 1px rgba(74, 46, 20, 0.04);
  --vg-shadow-md: 0 6px 18px -6px rgba(74, 46, 20, 0.18), 0 2px 4px rgba(74, 46, 20, 0.05);
  --vg-shadow-lg: 0 24px 60px -18px rgba(60, 36, 14, 0.35);

  --vg-font-display: 'Cormorant Garamond', 'EB Garamond', Georgia, serif;
  --vg-font-ui: 'Source Sans 3', system-ui, -apple-system, 'Segoe UI', sans-serif;
  --vg-font-verse: 'Tiro Devanagari Sanskrit', 'Noto Serif Devanagari', 'Noto Serif Kannada', 'Noto Serif Telugu', Georgia, serif;
  --vg-font-mono: 'Fira Code', ui-monospace, monospace;

  /* legacy names still referenced by inline styles in the HTML/JS */
  --vg-text: var(--vg-ink);
  --vg-text-muted: var(--vg-ink-2);
  --vg-text-dim: var(--vg-ink-3);
  --vg-border: var(--vg-rule);
  --vg-border-strong: var(--vg-rule-strong);
  --vg-gold-light: var(--vg-saffron);
  --vg-bg: var(--vg-paper);
  --vg-bg-surface: var(--vg-leaf);
  --vg-bg-card: var(--vg-leaf);
}

/* ── Page ground ───────────────────────────────────────────────────── */
html, body {
  background: var(--vg-paper) !important;
}
body {
  background:
    radial-gradient(ellipse 80% 50% at 50% -10%, rgba(255, 250, 236, 0.9) 0%, transparent 70%),
    radial-gradient(ellipse 60% 60% at 100% 100%, rgba(201, 103, 26, 0.06) 0%, transparent 60%),
    linear-gradient(180deg, #f6eedb 0%, var(--vg-paper) 40%, var(--vg-paper-deep) 100%) !important;
  background-attachment: fixed !important;
  color: var(--vg-ink);
}
.gradio-container {
  background: transparent !important;
  max-width: 1200px !important;
  margin: 0 auto !important;
  padding: 20px 20px 48px !important;
  font-family: var(--vg-font-ui) !important;
  color: var(--vg-ink);
}
.gradio-container .main, .gradio-container .contain { background: transparent; }

/* ── Progress panel (shown only on the lyrics area while chanting) ─── */
.gradio-container [data-testid="status-tracker"].wrap:not(.hide) {
  background: var(--vg-leaf-2) !important;
  border-radius: 12px;
  z-index: 5;
}
#vagdhenu-lyrics-wrapper { min-height: 240px; position: relative; }
.gradio-container [data-testid="status-tracker"] .progress-text,
.gradio-container [data-testid="status-tracker"] .progress-level-inner,
.gradio-container [data-testid="status-tracker"] .meta-text,
.gradio-container [data-testid="status-tracker"] .meta-text-center {
  color: var(--vg-ink-2) !important;
  font-family: var(--vg-font-ui) !important;
  font-size: 14px !important;
}
.gradio-container [data-testid="status-tracker"] .progress-level { width: min(80%, 420px); }
.gradio-container [data-testid="status-tracker"] .progress-bar-wrap {
  background: var(--vg-paper-deep) !important;
  border: 1px solid var(--vg-rule) !important;
  border-radius: 999px !important;
  height: 8px !important;
  overflow: hidden;
}
.gradio-container [data-testid="status-tracker"] .progress-bar {
  background: linear-gradient(90deg, var(--vg-saffron), var(--vg-vermilion)) !important;
  border-radius: 999px !important;
}
.vagdhenu-rendering-card { min-height: 240px; display: flex; flex-direction: column; justify-content: center; }

/* tanpura row */
.vagdhenu-tanpura-row { gap: 12px !important; align-items: stretch !important; }
.vagdhenu-action-row { gap: 10px !important; }
#vagdhenu-queue-btn { min-height: 52px; font-weight: 700 !important; border-radius: 10px !important; }
.vg-hidden { display: none !important; }

/* ── Render queue panel ─────────────────────────────────────────── */
#vagdhenu-queue { margin-top: 18px !important; padding: 0 !important; background: transparent !important; border: 0 !important; }
.vg-q {
  background: var(--vg-leaf); border: 1px solid var(--vg-rule); border-radius: 14px;
  padding: 16px 18px; box-shadow: var(--vg-shadow-sm);
}
.vg-q-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 10px; }
.vg-q-title { font-family: var(--vg-font-display); font-size: 24px; font-weight: 600; color: var(--vg-ink); line-height: 1.1; }
.vg-q-sub { font-size: 13px; color: var(--vg-ink-3); }
.vg-q-empty { font-size: 14px; color: var(--vg-ink-3); padding: 10px 2px; line-height: 1.5; }
.vg-q-list { display: flex; flex-direction: column; gap: 8px; max-height: 360px; overflow-y: auto; }
.vg-q-item {
  display: flex; align-items: center; gap: 12px; padding: 10px 12px; border-radius: 10px;
  background: var(--vg-field); border: 1px solid var(--vg-rule);
}
.vg-q-item.following { border-color: var(--vg-saffron); box-shadow: 0 0 0 2px var(--vg-saffron-sf); }
.vg-q-item.cancelled, .vg-q-item.failed { opacity: .75; }
.vg-q-main { flex: 1; min-width: 0; }
.vg-q-top { display: flex; align-items: center; gap: 8px; min-width: 0; }
.vg-q-snip { font-family: var(--vg-font-verse); font-size: 16px; color: var(--vg-ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.vg-q-meta { font-size: 12.5px; color: var(--vg-ink-3); margin-top: 2px; }
.vg-q-chip { font-size: 11px; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; border-radius: 999px; padding: 2px 8px; flex-shrink: 0; }
.vg-q-chip.rendering { background: var(--vg-saffron-sf); color: #8a4510; }
.vg-q-chip.queued { background: var(--vg-paper); color: var(--vg-ink-2); }
.vg-q-chip.done { background: #e6f1df; color: #2f6239; }
.vg-q-chip.failed { background: var(--vg-vermilion-sf); color: var(--vg-vermilion-dk); }
.vg-q-actions { display: flex; gap: 6px; flex-shrink: 0; }
.vg-q-actions button {
  font: 600 13px var(--vg-font-ui); color: var(--vg-ink-2); background: var(--vg-leaf);
  border: 1px solid var(--vg-rule-strong); border-radius: 8px; padding: 6px 12px; min-height: 32px; cursor: pointer;
}
.vg-q-actions button:hover { border-color: var(--vg-saffron); color: var(--vg-ink); }
.vg-q-actions button.primary { background: var(--vg-vermilion); border-color: var(--vg-vermilion-dk); color: #fffaf2; }
.vg-q-actions button.primary:hover { background: var(--vg-vermilion-dk); }
.vg-progress { height: 8px; background: var(--vg-paper-deep); border-radius: 999px; overflow: hidden; margin: 12px auto 10px; max-width: 360px; }
.vg-progress.sm { height: 5px; margin: 6px 0 0; max-width: none; }
.vg-progress-fill { height: 100%; background: linear-gradient(90deg, var(--vg-saffron), var(--vg-vermilion)); border-radius: 999px; transition: width .6s ease; }
/* the model reports progress per verse, so show motion while a verse is in the works */
.vg-progress.busy { position: relative; }
.vg-progress.busy::after {
  content: ''; position: absolute; inset: 0; border-radius: 999px;
  background: linear-gradient(90deg, transparent 0%, rgba(201,103,26,.45) 50%, transparent 100%);
  background-size: 40% 100%; background-repeat: no-repeat;
  animation: vg-busy 1.6s ease-in-out infinite;
}
@keyframes vg-busy { from { background-position: -40% 0; } to { background-position: 140% 0; } }
.vg-q-snip-lg { font-family: var(--vg-font-verse); font-size: 17px; color: var(--vg-ink-2); }
.vg-q-hint { font-size: 13px; color: var(--vg-ink-3); margin: 6px 0 0 !important; }
@media (max-width: 768px) {
  .vg-q-item { flex-wrap: wrap; }
  .vg-q-actions { width: 100%; justify-content: flex-end; }
}

::selection { background: var(--vg-saffron-sf); color: var(--vg-ink); }
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--vg-rule-strong); border-radius: 999px; border: 2px solid var(--vg-leaf); }
::-webkit-scrollbar-thumb:hover { background: var(--vg-gold); }

/* ── Header: a manuscript folio title ──────────────────────────────── */
.vagdhenu-header {
  text-align: center;
  padding: 30px 24px 24px;
  margin-bottom: 18px;
  background: var(--vg-leaf);
  border: 1px solid var(--vg-rule-strong);
  border-radius: 14px;
  /* double-ruled border, like a folio frame */
  box-shadow: inset 0 0 0 5px var(--vg-leaf), inset 0 0 0 6px var(--vg-rule), var(--vg-shadow-md);
  position: relative;
}
.vagdhenu-header-topline {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
}
.vagdhenu-om-symbol {
  font-family: var(--vg-font-verse);
  font-size: 40px;
  line-height: 1;
  color: var(--vg-vermilion);
}
.vagdhenu-title {
  font-family: var(--vg-font-display) !important;
  font-size: 42px !important;
  font-weight: 600 !important;
  letter-spacing: 0.16em !important;
  color: var(--vg-ink) !important;
  -webkit-text-fill-color: currentColor !important;
  background: none !important;
  margin: 0 !important;
  line-height: 1.1 !important;
  border: 0 !important;
  padding: 0 !important;
}
.vagdhenu-subtitle {
  font-family: var(--vg-font-verse);
  font-size: 17px;
  color: var(--vg-vermilion-dk);
  margin: 8px 0 6px;
  letter-spacing: 0.01em;
}
.vagdhenu-subtitle::before, .vagdhenu-subtitle::after {
  content: '';
  display: inline-block;
  width: 36px;
  height: 1px;
  background: var(--vg-gold);
  vertical-align: middle;
  margin: 0 12px;
  opacity: 0.7;
}
.vagdhenu-tagline {
  font-size: 15px;
  line-height: 1.55;
  color: var(--vg-ink-2);
  max-width: 620px;
  margin: 0 auto 16px;
}
.vagdhenu-badges-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}
.vagdhenu-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--vg-ink-2);
  background: var(--vg-field);
  border: 1px solid var(--vg-rule);
  border-radius: 999px;
  padding: 4px 12px;
}
.vagdhenu-pill.live-status { color: var(--vg-leafgreen); border-color: rgba(63, 125, 74, 0.35); background: #eef5e9; }
.vagdhenu-pill.live-status::before {
  content: '';
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--vg-leafgreen);
  box-shadow: 0 0 0 3px rgba(63, 125, 74, 0.18);
}

/* ── Studio layout ─────────────────────────────────────────────────── */
.vagdhenu-studio-row { gap: 18px !important; align-items: flex-start !important; }
.vagdhenu-deck-left, .vagdhenu-deck-right {
  background: var(--vg-leaf);
  border: 1px solid var(--vg-rule);
  border-radius: 14px;
  padding: 18px !important;
  box-shadow: var(--vg-shadow-sm);
  gap: 14px !important;
}

/* section labels (small caps, gold-leaf rule) */
.vagdhenu-quick-chips-title,
.vagdhenu-modal-section-tag {
  font-family: var(--vg-font-ui);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--vg-ink-3);
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.vagdhenu-quick-chips-title::after,
.vagdhenu-modal-section-tag::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--vg-rule);
}

/* ── Quick verse chips ─────────────────────────────────────────────── */
.vagdhenu-chips-row { display: flex; flex-wrap: wrap; gap: 8px; }
.vagdhenu-chip-btn {
  font-family: var(--vg-font-ui);
  font-size: 14px;
  font-weight: 600;
  color: var(--vg-ink-2);
  background: var(--vg-field);
  border: 1px solid var(--vg-rule);
  border-radius: 999px;
  padding: 6px 14px;
  min-height: 34px;
  cursor: pointer;
  transition: border-color .15s, background .15s, color .15s;
}
.vagdhenu-chip-btn:hover { border-color: var(--vg-saffron); color: var(--vg-ink); background: #fff8ea; }
.vagdhenu-chip-btn:focus-visible { outline: 2px solid var(--vg-saffron); outline-offset: 2px; }
.vagdhenu-chip-btn.active-chip {
  background: var(--vg-vermilion-sf);
  border-color: var(--vg-vermilion);
  color: var(--vg-vermilion-dk);
}

/* ── Gradio components inside the studio ───────────────────────────── */
.vagdhenu-input-tabs .tab-container button {
  font-family: var(--vg-font-ui) !important;
  font-weight: 600 !important;
  font-size: 14px !important;
}
#vagdhenu-text-input textarea {
  font-family: var(--vg-font-verse) !important;
  font-size: 20px !important;
  line-height: 1.85 !important;
  color: var(--vg-ink) !important;
  padding: 12px 14px !important;
}
#vagdhenu-text-input textarea::placeholder { color: var(--vg-ink-3); font-family: var(--vg-font-ui); font-size: 15px; }

.vagdhenu-controls-bar { gap: 12px !important; align-items: stretch !important; }

#vagdhenu-chant-btn {
  font-family: var(--vg-font-ui) !important;
  font-size: 17px !important;
  font-weight: 700 !important;
  letter-spacing: 0.02em;
  min-height: 52px;
  border-radius: 10px !important;
  box-shadow: 0 6px 16px -6px rgba(142, 42, 19, 0.55) !important;
}
#vagdhenu-chant-btn:hover { transform: translateY(-1px); }
#vagdhenu-chant-btn:active { transform: translateY(0); }

.vagdhenu-deck-subtext, .vagdhenu-deck-subtext p, .vagdhenu-deck-subtext sub {
  color: var(--vg-ink-3) !important;
  font-size: 13px !important;
  line-height: 1.5 !important;
  margin: 0 !important;
  vertical-align: baseline !important;
}
.vagdhenu-deck-subtext { overflow: visible !important; }

/* status line */
#vagdhenu-status-box {
  background: var(--vg-leaf-2) !important;
  border: 1px solid var(--vg-rule) !important;
  border-left: 3px solid var(--vg-saffron) !important;
  border-radius: 10px !important;
  padding: 10px 14px !important;
}
#vagdhenu-status-box, #vagdhenu-status-box p, #vagdhenu-status-box em { color: var(--vg-ink-2) !important; font-size: 14.5px; line-height: 1.5; margin: 0; }
#vagdhenu-status-box strong, #vagdhenu-status-box b { color: var(--vg-vermilion-dk) !important; font-weight: 700; }

#vagdhenu-audio audio { width: 100%; }
#vagdhenu-lyrics-wrapper { padding: 0 !important; background: transparent !important; border: 0 !important; }

/* ── Idle placeholder ──────────────────────────────────────────────── */
.vagdhenu-idle-card {
  text-align: center;
  padding: 34px 24px 28px;
  border: 1px dashed var(--vg-rule-strong);
  border-radius: 12px;
  background: var(--vg-leaf-2);
}
.vagdhenu-idle-mandala { font-size: 34px; line-height: 1; margin-bottom: 10px; }
.vagdhenu-idle-title {
  font-family: var(--vg-font-display);
  font-size: 26px;
  font-weight: 600;
  color: var(--vg-ink);
  margin-bottom: 8px;
}
.vagdhenu-idle-desc {
  font-size: 15px;
  line-height: 1.6;
  color: var(--vg-ink-2) !important;
  max-width: 440px;
  margin: 0 auto 16px !important;
}
.vagdhenu-idle-desc strong { color: var(--vg-vermilion-dk); }
.vagdhenu-idle-features {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 6px 10px;
  font-size: 13px;
  color: var(--vg-ink-3);
}

/* ── Synchronized lyrics ───────────────────────────────────────────── */
.vagdhenu-lyrics-box {
  background: var(--vg-leaf-2);
  border: 1px solid var(--vg-rule);
  border-radius: 12px;
  padding: 14px;
}
.vagdhenu-lyrics-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--vg-rule);
}
.vagdhenu-lyrics-header-title {
  font-family: var(--vg-font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--vg-ink);
  display: flex;
  align-items: center;
  gap: 8px;
}
.vagdhenu-action-btn-group { display: flex; flex-wrap: wrap; gap: 8px; }

/* secondary (outline) and primary (vermilion) action buttons */
.vagdhenu-add-card-btn, .card-btn, .vagdhenu-export-cancel-btn, .vg-custom-upload-btn {
  font-family: var(--vg-font-ui);
  font-size: 13.5px;
  font-weight: 600;
  color: var(--vg-ink-2);
  background: var(--vg-field);
  border: 1px solid var(--vg-rule-strong);
  border-radius: 8px;
  padding: 7px 14px;
  min-height: 34px;
  cursor: pointer;
  transition: border-color .15s, color .15s, background .15s;
}
.vagdhenu-add-card-btn:hover, .card-btn:hover, .vagdhenu-export-cancel-btn:hover, .vg-custom-upload-btn:hover {
  border-color: var(--vg-saffron);
  color: var(--vg-ink);
  background: #fff8ea;
}
.vagdhenu-export-btn-primary {
  font-family: var(--vg-font-ui);
  font-size: 13.5px;
  font-weight: 700;
  color: #fffaf2;
  background: var(--vg-vermilion);
  border: 1px solid var(--vg-vermilion-dk);
  border-radius: 8px;
  padding: 7px 14px;
  min-height: 34px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: background .15s;
}
.vagdhenu-export-btn-primary:hover { background: var(--vg-vermilion-dk); }
.vagdhenu-export-btn-primary:disabled { opacity: .6; cursor: progress; }

.vagdhenu-lyrics-scroller {
  max-height: 290px;
  overflow-y: auto;
  padding-right: 4px;
  scroll-behavior: smooth;
}
.vagdhenu-lyric-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  margin-bottom: 4px;
  border-radius: 8px;
  border-left: 3px solid transparent;
  cursor: pointer;
  transition: background .15s, border-color .15s;
}
.vagdhenu-lyric-item:hover { background: var(--vg-leaf); }
/* phones: the tanpura checkbox + level slider share one Gradio form whose summed min-widths
   (180 + 200 px) would push the page wider than the screen — stack them instead */
@media (max-width: 700px) {
  .vagdhenu-tanpura-row .form { flex-wrap: wrap !important; min-width: 0 !important; }
  .vagdhenu-tanpura-row .form > * { min-width: 100% !important; flex-basis: 100% !important; }
  .tab-container button { padding: 0 9px !important; }
}
/* stotra title (not chanted), verse dividers, closing colophon */
.vg-stotra-title {
  display: flex; align-items: center; justify-content: center; gap: 12px;
  margin: 2px 0 10px; padding: 14px 12px 12px;
  border-top: 1px solid var(--vg-rule-strong); border-bottom: 1px solid var(--vg-rule-strong);
  background: linear-gradient(180deg, var(--vg-saffron-sf), transparent);
  text-align: center;
}
.vg-stotra-name {
  font-family: var(--vg-font-verse); font-size: 1.45rem; line-height: 1.35;
  color: var(--vg-vermilion-dk); letter-spacing: 0.01em;
}
.vg-stotra-orn { font-family: var(--vg-font-verse); color: var(--vg-gold); font-size: 1.1rem; }
.vg-verse-divider {
  display: flex; align-items: center; gap: 10px; margin: 10px 4px 4px;
  color: var(--vg-gold); font-family: var(--vg-font-verse); font-size: 0.85rem;
}
.vg-verse-divider::before, .vg-verse-divider::after {
  content: ""; flex: 1; height: 1px; background: var(--vg-rule);
}
.vg-verse-divider span::before { content: "॥ "; }
.vg-verse-divider span::after { content: " ॥"; }
.vg-stotra-colophon {
  margin: 12px 0 4px; text-align: center; font-family: var(--vg-font-verse);
  font-size: 0.95rem; color: var(--vg-ink-3); font-style: italic;
}
.lyric-time-badge {
  font-family: var(--vg-font-mono);
  font-size: 12px;
  color: var(--vg-ink-3);
  background: var(--vg-paper);
  border-radius: 6px;
  padding: 2px 7px;
  flex-shrink: 0;
}
.lyric-verse-text {
  flex: 1;
  font-family: var(--vg-font-verse);
  font-size: 18px;
  line-height: 1.6;
  color: var(--vg-ink-2);
}
.lyric-play-icon { font-size: 11px; color: var(--vg-ink-3); opacity: 0; transition: opacity .15s; }
.vagdhenu-lyric-item:hover .lyric-play-icon { opacity: 1; }
.vagdhenu-lyric-item.active-lyric {
  background: var(--vg-saffron-sf);
  border-left-color: var(--vg-vermilion);
}
.vagdhenu-lyric-item.active-lyric .lyric-verse-text { color: var(--vg-ink); font-weight: 600; }
.vagdhenu-lyric-item.active-lyric .lyric-time-badge { background: var(--vg-vermilion); color: #fffaf2; }
.vagdhenu-lyric-item.active-lyric .lyric-play-icon { opacity: 1; color: var(--vg-vermilion); }
.vagdhenu-lyrics-hint { margin-top: 8px; font-size: 13px; color: var(--vg-ink-3); }

/* ── Chant library ─────────────────────────────────────────────────── */
.vagdhenu-library-section {
  margin-top: 18px;
  background: var(--vg-leaf);
  border: 1px solid var(--vg-rule);
  border-radius: 14px;
  padding: 20px;
  box-shadow: var(--vg-shadow-sm);
}
.vagdhenu-library-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 4px;
}
.vagdhenu-library-title {
  font-family: var(--vg-font-display);
  font-size: 26px;
  font-weight: 600;
  color: var(--vg-ink);
  display: flex;
  align-items: center;
  gap: 10px;
}
.vagdhenu-library-section > p { color: var(--vg-ink-2) !important; font-size: 14px !important; line-height: 1.55; }
.vagdhenu-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 14px;
}
.vagdhenu-chant-card {
  background: var(--vg-field);
  border: 1px solid var(--vg-rule);
  border-top: 3px solid var(--vg-saffron);
  border-radius: 10px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 12px;
  box-shadow: var(--vg-shadow-sm);
  transition: box-shadow .2s, transform .2s;
}
.vagdhenu-chant-card:hover { box-shadow: var(--vg-shadow-md); transform: translateY(-1px); }
.card-title-row { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 8px; }
.card-om { font-family: var(--vg-font-verse); color: var(--vg-vermilion); font-size: 20px; line-height: 1.2; }
.card-title-text {
  flex: 1;
  font-family: var(--vg-font-verse);
  font-size: 16px;
  line-height: 1.5;
  color: var(--vg-ink);
}
.card-meta-row { display: flex; flex-wrap: wrap; gap: 6px; }
.card-badge {
  font-size: 12px;
  font-weight: 600;
  color: var(--vg-ink-2);
  background: var(--vg-paper);
  border-radius: 999px;
  padding: 2px 9px;
}
.card-badge.meter { color: var(--vg-vermilion-dk); background: var(--vg-vermilion-sf); }
.card-btn { width: 100%; }
.card-delete-btn {
  background: none;
  border: 0;
  color: var(--vg-ink-3);
  font-size: 14px;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  cursor: pointer;
}
.card-delete-btn:hover { color: var(--vg-vermilion); background: var(--vg-vermilion-sf); }

/* ── Modals (chant view + video studio) ────────────────────────────── */
.vagdhenu-modal-backdrop {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(42, 28, 18, 0.45);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  z-index: 999999;
  justify-content: center;
  align-items: center;
  padding: 16px;
}
.vagdhenu-modal-card {
  background: var(--vg-leaf);
  border: 1px solid var(--vg-rule-strong);
  border-radius: 14px;
  max-width: 760px;
  width: 100%;
  max-height: 88vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--vg-shadow-lg);
  overflow: hidden;
  animation: vg-modal-in .22s cubic-bezier(.16, 1, .3, 1);
}
@keyframes vg-modal-in { from { opacity: 0; transform: translateY(8px) scale(.98); } to { opacity: 1; transform: none; } }
.vagdhenu-modal-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--vg-rule);
  background: var(--vg-leaf-2);
}
.vagdhenu-modal-title {
  font-family: var(--vg-font-verse) !important;
  font-size: 19px !important;
  font-weight: 600 !important;
  color: var(--vg-ink) !important;
  margin: 0 !important;
  line-height: 1.35 !important;
}
.vagdhenu-modal-close-btn {
  background: none;
  border: 1px solid transparent;
  color: var(--vg-ink-3);
  font-size: 16px;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  cursor: pointer;
  flex-shrink: 0;
}
.vagdhenu-modal-close-btn:hover { background: var(--vg-paper); color: var(--vg-ink); }
.vagdhenu-modal-content-area { padding: 18px 20px; overflow-y: auto; flex: 1; }
.vagdhenu-modal-audio-wrap {
  margin-bottom: 14px;
  background: var(--vg-leaf-2);
  padding: 10px;
  border-radius: 10px;
  border: 1px solid var(--vg-rule);
}
#vagdhenu-modal-audio-player { width: 100%; }
.vagdhenu-modal-devanagari-text {
  font-family: var(--vg-font-verse);
  font-size: 20px;
  line-height: 2.1;
  color: var(--vg-ink);
  text-align: center;
  background: var(--vg-field);
  padding: 22px 18px;
  border: 1px solid var(--vg-rule);
  border-radius: 10px;
  box-shadow: inset 0 0 0 4px var(--vg-field), inset 0 0 0 5px var(--vg-rule);
  white-space: pre-wrap;
  margin-bottom: 8px;
}
.ornamental-danda, .ornamental-danda-double { color: var(--vg-vermilion); font-weight: 600; }
.vagdhenu-modal-bottom-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  padding: 12px 20px;
  border-top: 1px solid var(--vg-rule);
  background: var(--vg-leaf-2);
}
.vagdhenu-modal-bottom-bar span { color: var(--vg-ink-3) !important; font-size: 13px !important; }

/* video studio */
.vg-studio-label {
  display: block;
  color: var(--vg-ink);
  font-weight: 700;
  font-size: 14px;
  margin-bottom: 6px;
}
.vg-studio-help { display: block; color: var(--vg-ink-3); font-size: 12.5px; margin-top: 5px; }
.vg-studio-note {
  background: var(--vg-saffron-sf);
  border: 1px solid rgba(201, 103, 26, 0.3);
  border-radius: 8px;
  padding: 10px 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--vg-ink-2);
  font-size: 13px;
  line-height: 1.45;
}
.vg-studio-input {
  width: 100%;
  box-sizing: border-box;
  font-family: var(--vg-font-verse);
  font-size: 16px;
  color: var(--vg-ink);
  background: var(--vg-field);
  border: 1px solid var(--vg-rule-strong);
  border-radius: 8px;
  padding: 9px 12px;
}
.vg-studio-input:focus { outline: none; border-color: var(--vg-saffron); box-shadow: 0 0 0 3px rgba(201, 103, 26, 0.18); }
.vg-studio-choice-btn {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  color: var(--vg-ink-2);
  background: var(--vg-field);
  border: 1px solid var(--vg-rule-strong);
  border-radius: 10px;
  cursor: pointer;
  font-family: var(--vg-font-ui);
}
.vg-studio-choice-btn:hover { border-color: var(--vg-saffron); }
.vg-studio-choice-btn.active { background: var(--vg-vermilion-sf); border-color: var(--vg-vermilion); color: var(--vg-vermilion-dk); }
.vg-photo-preset-chip {
  font-family: var(--vg-font-ui);
  font-size: 13px;
  font-weight: 600;
  color: var(--vg-ink-2);
  background: var(--vg-field);
  border: 1px solid var(--vg-rule);
  border-radius: 999px;
  padding: 5px 12px;
  cursor: pointer;
}
.vg-photo-preset-chip:hover { border-color: var(--vg-saffron); }
.vg-photo-preset-chip.active { background: var(--vg-vermilion-sf); border-color: var(--vg-vermilion); color: var(--vg-vermilion-dk); }
#vg-custom-photo-status { color: var(--vg-leafgreen) !important; }

/* export progress overlay */
.vagdhenu-export-overlay {
  position: fixed;
  inset: 0;
  background: rgba(42, 28, 18, 0.5);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  z-index: 9999999;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 16px;
}
.vagdhenu-export-card {
  background: var(--vg-leaf);
  border: 1px solid var(--vg-rule-strong);
  border-radius: 14px;
  padding: 26px 28px;
  width: 100%;
  max-width: 420px;
  text-align: center;
  box-shadow: var(--vg-shadow-lg);
}
.vagdhenu-export-card .export-title {
  font-family: var(--vg-font-display);
  font-size: 24px;
  font-weight: 600;
  color: var(--vg-ink) !important;
  margin-bottom: 6px;
}
.vagdhenu-export-card .export-status { color: var(--vg-ink-2); font-size: 14px; margin-bottom: 14px; }
.vagdhenu-export-card .export-sub { color: var(--vg-ink-2); font-size: 13.5px; margin-bottom: 12px; }
.vagdhenu-export-card video { border: 1px solid var(--vg-rule-strong) !important; box-shadow: var(--vg-shadow-md) !important; }
.vagdhenu-export-progress-track { height: 8px; background: var(--vg-paper-deep); border-radius: 999px; overflow: hidden; }
.vagdhenu-export-progress-fill {
  height: 100%;
  width: 0;
  background: linear-gradient(90deg, var(--vg-saffron), var(--vg-vermilion));
  border-radius: 999px;
  transition: width .2s;
}
.vagdhenu-export-card .export-time { font-family: var(--vg-font-mono); font-size: 12.5px; color: var(--vg-ink-3); margin-top: 8px; }
.vagdhenu-export-cancel-btn { margin-top: 14px; }

/* ── Accordion / examples / footer ─────────────────────────────────── */
.vagdhenu-treasury { margin-top: 18px !important; }
.vagdhenu-treasury button.label-wrap span {
  font-family: var(--vg-font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--vg-ink);
}
.vagdhenu-footer, .vagdhenu-footer p { color: var(--vg-ink-3) !important; font-size: 13px !important; text-align: center; }
.vagdhenu-footer a { color: var(--vg-vermilion-dk) !important; }
.vagdhenu-footer hr { border-color: var(--vg-rule) !important; }
.gradio-container footer, .gradio-container footer * { color: var(--vg-ink-3) !important; }

/* ── Small screens ─────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .gradio-container { padding: 12px 12px 36px !important; }
  .vagdhenu-header { padding: 22px 14px 18px; }
  .vagdhenu-om-symbol { font-size: 30px; }
  .vagdhenu-title { font-size: 30px !important; letter-spacing: 0.1em !important; }
  .vagdhenu-subtitle { font-size: 15px; }
  .vagdhenu-subtitle::before, .vagdhenu-subtitle::after { width: 16px; margin: 0 8px; }
  .vagdhenu-tagline { font-size: 14px; }
  .vagdhenu-pill { font-size: 11.5px; padding: 3px 10px; }
  .vagdhenu-deck-left, .vagdhenu-deck-right { padding: 14px !important; }
  .vagdhenu-lyrics-header { flex-direction: column; align-items: flex-start; }
  .lyric-verse-text { font-size: 16px; }
  .vagdhenu-library-section { padding: 16px; }
  .vagdhenu-modal-devanagari-text { font-size: 17px; }
  .vg-studio-choice-btn { padding: 8px; }
}
@media (prefers-reduced-motion: reduce) {
  * { transition: none !important; animation: none !important; }
}
"""

CUSTOM_JS_CODE = """\
// ==========================================================================
// VĀGDHENU — SYNCHRONIZED KARAOKE LYRICS & CARD LIBRARY CLIENT ENGINE
// ==========================================================================

window.vagdhenuActiveData = null;
try {
  window.vagdhenuLibrary = JSON.parse(localStorage.getItem('vagdhenu_library') || '[]');
} catch (e) {
  window.vagdhenuLibrary = [];
}

// Global audio capture listener for instant karaoke synchronization
const onAudioSyncEvent = (e) => {
  if (e.target && e.target.tagName === 'AUDIO') {
    if (e.target.closest && e.target.closest('#vagdhenu-audio')) {
      syncLyricsHighlight(e.target.currentTime, '.vagdhenu-studio-lyrics');
    } else if (e.target.id === 'vagdhenu-modal-audio-player') {
      syncLyricsHighlight(e.target.currentTime, '#vagdhenu-modal-lyrics-list');
    }
  }
};
document.addEventListener('timeupdate', onAudioSyncEvent, true);
document.addEventListener('seeked', onAudioSyncEvent, true);

document.addEventListener('ended', (e) => {
  if (e.target && e.target.tagName === 'AUDIO') {
    const selector = (e.target.id === 'vagdhenu-modal-audio-player') 
      ? '#vagdhenu-modal-lyrics-list .vagdhenu-lyric-item' 
      : '.vagdhenu-studio-lyrics .vagdhenu-lyric-item';
    document.querySelectorAll(selector).forEach(el => el.classList.remove('active-lyric'));
  }
}, true);

// Precise & smooth lyric line highlight
function syncLyricsHighlight(currentTime, containerSelector) {
  const container = document.querySelector(containerSelector);
  if (!container) return;
  const items = Array.from(container.querySelectorAll('.vagdhenu-lyric-item'));
  if (items.length === 0) return;
  
  let activeIdx = -1;
  for (let i = 0; i < items.length; i++) {
    const start = parseFloat(items[i].getAttribute('data-start'));
    const end = parseFloat(items[i].getAttribute('data-end'));
    const nextStart = (i + 1 < items.length) ? parseFloat(items[i+1].getAttribute('data-start')) : (end + 1.2);
    
    // Active from start (with slight 150ms lead-in) until next item starts
    if (currentTime >= (start - 0.15) && currentTime < nextStart) {
      activeIdx = i;
      break;
    }
  }
  
  items.forEach((item, idx) => {
    if (idx === activeIdx) {
      if (!item.classList.contains('active-lyric')) {
        item.classList.add('active-lyric');
        item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    } else {
      item.classList.remove('active-lyric');
    }
  });
}

// Gradio 6 renders the playable <audio> inside the waveform player's shadow root; the light-DOM
// <audio> under #vagdhenu-audio is an empty placeholder. Media events don't cross the shadow
// boundary, so the document-level listeners above never see playback — bind to the real element.
window.getVagdhenuMainAudio = function() {
  const block = document.querySelector('#vagdhenu-audio');
  if (!block) return null;
  for (const el of block.querySelectorAll('*')) {
    if (el.shadowRoot) {
      const m = el.shadowRoot.querySelector('audio, video');
      if (m && (m.currentSrc || m.src)) return m;
    }
  }
  const a = block.querySelector('audio');
  return (a && (a.currentSrc || a.src)) ? a : null;
};

function bindMainAudioSync() {
  const m = window.getVagdhenuMainAudio();
  if (!m || m._vgSyncBound) return;
  m._vgSyncBound = true;
  const sync = () => syncLyricsHighlight(m.currentTime, '.vagdhenu-studio-lyrics');
  m.addEventListener('timeupdate', sync);
  m.addEventListener('seeked', sync);
  m.addEventListener('ended', () => {
    document.querySelectorAll('.vagdhenu-studio-lyrics .vagdhenu-lyric-item')
      .forEach(el => el.classList.remove('active-lyric'));
  });
}
// the player (and its media element) is re-created on each new chant, so keep re-binding
setInterval(bindMainAudioSync, 1000);

// Interactive line seek in main audio
window.seekVagdhenuAudio = function(timeSec) {
  const audio = window.getVagdhenuMainAudio();
  if (audio) {
    audio.currentTime = parseFloat(timeSec);
    audio.play().catch(() => {});
  }
};

// Interactive line seek in modal audio
window.seekModalAudio = function(timeSec) {
  const audio = document.getElementById('vagdhenu-modal-audio-player');
  if (audio) {
    audio.currentTime = parseFloat(timeSec);
    audio.play().catch(() => {});
  }
};

// Quick verse loader
window.loadQuickVerse = function(key) {
  const verses = {
    'suklam': 'शुक्लाम्बरधरं विष्णुं शशिवर्णं चतुर्भुजम् ।\\nप्रसन्नवदनं ध्यायेत् सर्वविघ्नोपशान्तये ॥',
    'vasudeva': 'वसुदेवसुतं देवं कंसचाणूरमर्दनम् ।\\nदेवकीपरमानन्दं कृष्णं वन्दे जगद्गुरुम् ॥',
    'vakratunda': 'वक्रतुण्ड महाकाय सूर्यकोटिसमप्रभ ।\\nनिर्विघ्नं कुरु मे देव सर्वकार्येषु सर्वदा ॥',
    'yakundendu': 'या कुन्देन्दुतुषारहारधवला या शुभ्रवस्त्रावृता\\nया वीणावरदण्डमण्डितकरा या श्वेतपद्मासना ।\\nया ब्रह्माच्युतशङ्करप्रभृतिभिर्देवैः सदा वन्दिता\\nसा मां पातु सरस्वती भगवती निःशेषजाड्यापहा ॥',
    'gayatrimantra': 'ॐ भूर्भुवः स्वः तत्सवितुर्वरेण्यं\\nभर्गो देवस्य धीमहि धियो यो नः प्रचोदयात् ॥',
    'gururbrahma': 'गुरुर्ब्रह्मा गुरुर्विष्णुः गुरुर्देवो महेश्वरः ।\\nगुरुः साक्षात् परं ब्रह्म तस्मै श्रीगुरवे नमः ॥',
    'gita247': 'कर्मण्येवाधिकारस्ते मा फलेषु कदाचन ।\\nमा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि ॥',
    'karagre': 'कराग्रे वसते लक्ष्मीः करमध्ये सरस्वती ।\\nकरमूले तु गोविन्दः प्रभाते करदर्शनम् ॥'
  };
  const text = verses[key];
  if (!text) return;

  const textarea = document.querySelector('#vagdhenu-text-input textarea, textarea');
  if (textarea) {
    textarea.value = text;
    textarea.dispatchEvent(new Event('input', { bubbles: true }));
    textarea.dispatchEvent(new Event('change', { bubbles: true }));
  }

  document.querySelectorAll('.vagdhenu-chip-btn').forEach(b => b.classList.remove('active-chip'));
  const activeBtn = document.getElementById('chip-' + key);
  if (activeBtn) activeBtn.classList.add('active-chip');
};

// Called whenever new lyrics HTML is rendered into the DOM
window.vagdhenuOnLyricsRendered = function() {
  const payloadEl = document.getElementById('vagdhenu-active-payload');
  if (payloadEl) {
    const raw = payloadEl.getAttribute('data-payload');
    if (raw) {
      try {
        window.vagdhenuActiveData = JSON.parse(raw);
        console.log('[vagdhenu] Active chant data loaded:', window.vagdhenuActiveData.snippet, 'Audio URL:', window.vagdhenuActiveData.audioSrc);
      } catch (err) {
        console.error('[vagdhenu] JSON parse error on payload:', err);
      }
    }
  }
};

// Save current chant into browser local chant library
window.saveCurrentToLibrary = function(btnEl) {
  const btn = btnEl || document.getElementById('vagdhenu-save-card-btn');
  
  if (!window.vagdhenuActiveData) {
    const payloadEl = document.getElementById('vagdhenu-active-payload');
    if (payloadEl) {
      const raw = payloadEl.getAttribute('data-payload');
      if (raw) {
        try {
          window.vagdhenuActiveData = JSON.parse(raw);
        } catch (e) {
          console.error('[vagdhenu] Parse error reading payload element:', e);
        }
      }
    }
  }

  if (!window.vagdhenuActiveData) {
    alert('Please chant a verse first before adding to the library 🙏');
    return;
  }

  if (!window.vagdhenuActiveData.audioSrc) {
    const mainAudio = window.getVagdhenuMainAudio();
    if (mainAudio) {
      window.vagdhenuActiveData.audioSrc = mainAudio.currentSrc || mainAudio.src;
    }
  }

  const current = window.vagdhenuActiveData;
  const existingIdx = window.vagdhenuLibrary.findIndex(item => item.id === current.id);
  if (existingIdx >= 0) {
    window.vagdhenuLibrary[existingIdx] = current;
  } else {
    window.vagdhenuLibrary.unshift(current);
  }

  if (window.vagdhenuLibrary.length > 50) {
    window.vagdhenuLibrary.pop();
  }

  try {
    localStorage.setItem('vagdhenu_library', JSON.stringify(window.vagdhenuLibrary));
  } catch (err) {
    console.warn('[vagdhenu] localStorage quota issue, trimming library:', err);
    window.vagdhenuLibrary = window.vagdhenuLibrary.slice(0, 10);
    try {
      localStorage.setItem('vagdhenu_library', JSON.stringify(window.vagdhenuLibrary));
    } catch(e) {}
  }

  window.renderLibraryCards();

  if (btn) {
    btn.innerHTML = '✓ Saved in Library!';
    btn.style.background = '#3f7d4a';
    btn.style.borderColor = '#2f6239';
    btn.style.color = '#fffaf2';
  }

  const libSec = document.querySelector('.vagdhenu-library-section');
  if (libSec) {
    libSec.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
};

// Delete single card
window.deleteCard = function(idx) {
  if (confirm('Remove this chant card from your library?')) {
    window.vagdhenuLibrary.splice(idx, 1);
    try {
      localStorage.setItem('vagdhenu_library', JSON.stringify(window.vagdhenuLibrary));
    } catch(e) {}
    window.renderLibraryCards();
  }
};

// Clear entire library
window.clearChantLibrary = function() {
  if (confirm('Clear all saved chant cards from this browser?')) {
    window.vagdhenuLibrary = [];
    localStorage.removeItem('vagdhenu_library');
    window.renderLibraryCards();
  }
};

// Render card gallery
window.renderLibraryCards = function() {
  const grid = document.getElementById('vagdhenu-library-grid');
  if (!grid) return;
  
  if (!window.vagdhenuLibrary || window.vagdhenuLibrary.length === 0) {
    grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: var(--vg-text-dim); padding: 36px; border: 1px dashed var(--vg-border); border-radius: 14px;">🪔 No saved chants yet. Chanted shlokas can be preserved here as cards!</div>';
    return;
  }
  
  grid.innerHTML = window.vagdhenuLibrary.map((card, idx) => `
    <div class="vagdhenu-chant-card">
      <div>
        <div class="card-title-row">
          <span class="card-om">ॐ</span>
          <div class="card-title-text">${card.snippet || 'Sanskrit Chant'}</div>
          <button class="card-delete-btn" title="Remove card" onclick="deleteCard(${idx})">✕</button>
        </div>
        <div class="card-meta-row">
          <span class="card-badge meter">✨ ${(card.meters && card.meters.length > 0) ? card.meters.join(', ') : 'Auto'}</span>
          <span class="card-badge">⏱️ ${card.duration ? card.duration.toFixed(1) + 's' : ''}</span>
          <span class="card-badge">📜 ${card.shlokaCount || 1} Verse${(card.shlokaCount || 1) > 1 ? 's' : ''}</span>
        </div>
      </div>
      <button class="card-btn" onclick="openChantModal(${idx})">🔍 View Verse & Synced Lyrics</button>
    </div>
  `).join('');
};

// Modal dialog
window.openChantModal = function(index) {
  const card = window.vagdhenuLibrary[index];
  if (!card) return;
  window._openModalIdx = index;
  
  const backdrop = document.getElementById('vagdhenu-modal-backdrop');
  const title = document.getElementById('vagdhenu-modal-title');
  const meta = document.getElementById('vagdhenu-modal-meta');
  const verseText = document.getElementById('vagdhenu-modal-verse-text');
  const lyricsList = document.getElementById('vagdhenu-modal-lyrics-list');
  const modalAudio = document.getElementById('vagdhenu-modal-audio-player');
  const downloadLink = document.getElementById('vagdhenu-modal-download-link');
  
  title.innerText = card.snippet || 'Sanskrit Chant Composition';
  meta.innerHTML = `
    <span class="card-badge meter">✨ ${(card.meters && card.meters.length > 0) ? card.meters.join(', ') : 'Auto'}</span>
    <span class="card-badge">⏱️ ${card.duration ? card.duration.toFixed(1) + 's total' : ''}</span>
    <span class="card-badge">📜 ${card.shlokaCount || 1} Shloka${(card.shlokaCount || 1) > 1 ? 's' : ''}</span>
  `;
  
  verseText.innerHTML = card.beautifiedHtml || (card.raw_text ? card.raw_text.replace(/\\n/g, '<br>') : '');
  
  if (card.timestamps && card.timestamps.length > 0) {
    lyricsList.innerHTML = card.timestamps.map(t => `
      <div class="vagdhenu-lyric-item" data-start="${t.start}" data-end="${t.end}" onclick="seekModalAudio(${t.start})">
        <span class="lyric-time-badge">${formatSeconds(t.start)}</span>
        <span class="lyric-verse-text">${t.text}</span>
        <span class="lyric-play-icon">▶</span>
      </div>
    `).join('');
  } else {
    lyricsList.innerHTML = '<div style="color: var(--vg-text-dim); padding: 12px;">No timestamp breakdown available.</div>';
  }
  
  let audioSrc = card.audioSrc;
  if (!audioSrc) {
    if (window.vagdhenuActiveData && window.vagdhenuActiveData.audioSrc) {
      audioSrc = window.vagdhenuActiveData.audioSrc;
    } else {
      const mainAudio = window.getVagdhenuMainAudio();
      if (mainAudio) {
        audioSrc = mainAudio.currentSrc || mainAudio.src;
      }
    }
    if (audioSrc) {
      card.audioSrc = audioSrc;
      try { localStorage.setItem('vagdhenu_library', JSON.stringify(window.vagdhenuLibrary)); } catch(e){}
    }
  }

  const exportBtn = document.getElementById('vagdhenu-modal-export-video-btn');
  if (modalAudio) {
    if (audioSrc) {
      modalAudio.src = audioSrc;
      modalAudio.style.display = 'block';
      modalAudio.load();
      if (downloadLink) {
        const audioMeter = (card.meters && card.meters[0]) ? card.meters[0].replace(/[^a-zA-Z0-9]/g, '').toLowerCase() : 'chant';
        const audioName = `vagdhenu_${audioMeter}_${Date.now()}.wav`;
        downloadLink.href = audioSrc;
        downloadLink.download = audioName;
        downloadLink.onclick = async (e) => {
          e.preventDefault();
          try {
            const resp = await fetch(audioSrc);
            const blob = await resp.blob();
            const blobUrl = URL.createObjectURL(new Blob([blob], { type: 'audio/wav' }));
            const a = document.createElement('a');
            a.href = blobUrl;
            a.download = audioName;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            setTimeout(() => URL.revokeObjectURL(blobUrl), 15000);
          } catch(err) {
            window.open(audioSrc, '_blank');
          }
        };
        downloadLink.style.display = 'inline-flex';
      }
      if (exportBtn) exportBtn.style.display = 'inline-flex';
    } else {
      modalAudio.style.display = 'none';
      if (downloadLink) downloadLink.style.display = 'none';
      if (exportBtn) exportBtn.style.display = 'none';
    }
  }
  
  backdrop.style.display = 'flex';
};

window.closeVagdhenuModal = function(e) {
  if (e && e.target && e.target !== document.getElementById('vagdhenu-modal-backdrop') && !e.target.classList.contains('vagdhenu-modal-close-btn')) return;
  const backdrop = document.getElementById('vagdhenu-modal-backdrop');
  if (backdrop) backdrop.style.display = 'none';
  const modalAudio = document.getElementById('vagdhenu-modal-audio-player');
  if (modalAudio) {
    modalAudio.pause();
    modalAudio.currentTime = 0;
  }
};

function formatSeconds(sec) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s < 10 ? '0' : ''}${s}`;
}

// ESC closes modal
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeVagdhenuModal();
  }
});

// Periodic check on load to ensure cards render as soon as DOM grid exists
const initInterval = setInterval(() => {
  const grid = document.getElementById('vagdhenu-library-grid');
  if (grid) {
    window.renderLibraryCards();
    clearInterval(initInterval);
  }
}, 300);
setTimeout(() => clearInterval(initInterval), 10000);

// Observer for payload
const observer = new MutationObserver(() => {
  if (window.vagdhenuOnLyricsRendered) window.vagdhenuOnLyricsRendered();
});
observer.observe(document.body, { childList: true, subtree: true });

// ==========================================================================
// VIDEO EXPORT — Canvas + Web Audio + MediaRecorder lyric video renderer (9:16)
// ==========================================================================

// Lyric video export lives in demo/video_studio.js (window.openVideoStudio).

// Render-queue buttons → hidden Gradio textbox (#vg-queue-cmd) → queue_command() on the server.
window.vgQueueCmd = function(cmd) {
  const el = document.querySelector('#vg-queue-cmd textarea, #vg-queue-cmd input');
  if (!el) return;
  const setter = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el), 'value').set;
  setter.call(el, cmd + '|' + Date.now());   // unique value so repeating a command still fires
  el.dispatchEvent(new Event('input', { bubbles: true }));
};

console.log('[vagdhenu] Sacred Chant Studio engine initialized.');
"""

CUSTOM_JS = f"<script>\n{CUSTOM_JS_CODE}\n</script>"

def beautify_sanskrit_text(text):
    """Format raw Sanskrit text with golden dandas, verse breaks, and traditional rhythm."""
    lines = [l.strip() for l in (text or "").splitlines() if l.strip()]
    formatted_lines = []
    for l in lines:
        h = html.escape(l)
        h = re.sub(r"(॥|\|\|)", r'<span class="ornamental-danda-double">\1</span>', h)
        h = re.sub(r"(।|\|)", r'<span class="ornamental-danda">\1</span>', h)
        formatted_lines.append(h)
    return "<br>".join(formatted_lines)


def format_lyrics_component(all_timestamps, full_text, meters, duration, audio_url="", heading="",
                            colophon=""):
    """Build the interactive synchronized lyrics HTML and embed active chant payload. `heading` (the
    stotra's title) and `colophon` (its closing "इति …" line) are shown apart and not chanted."""
    if not all_timestamps:
        return ""

    snippet = heading or (all_timestamps[0]["text"] if all_timestamps else "Sanskrit Verse")
    if len(snippet) > 60:
        snippet = snippet[:57] + "..."

    beautified_html = beautify_sanskrit_text(full_text)
    shloka_count = len(set(t.get("shloka_idx", 1) for t in all_timestamps))

    items_html = []
    if heading:
        items_html.append(f"""
            <div class="vg-stotra-title">
                <span class="vg-stotra-orn">॥</span>
                <span class="vg-stotra-name">{html.escape(heading)}</span>
                <span class="vg-stotra-orn">॥</span>
            </div>""")
    prev_shloka = None
    for t in all_timestamps:
        sk = t.get("shloka_idx", 1)
        if shloka_count > 1 and sk != prev_shloka:
            items_html.append(f'<div class="vg-verse-divider"><span>{_to_deva_digits(sk)}</span></div>')
        prev_shloka = sk
        s = t["start"]
        e = t["end"]
        txt = html.escape(t["text"])
        m = int(s // 60)
        sec = int(s % 60)
        time_str = f"{m}:{sec:02d}"
        items_html.append(f"""
            <div class="vagdhenu-lyric-item" data-start="{s}" data-end="{e}" onclick="seekVagdhenuAudio({s})">
                <span class="lyric-time-badge">{time_str}</span>
                <span class="lyric-verse-text">{txt}</span>
                <span class="lyric-play-icon">▶</span>
            </div>
        """)
    if colophon:
        items_html.append(f'<div class="vg-stotra-colophon">॥ {html.escape(colophon)} ॥</div>')
    items_joined = "\n".join(items_html)

    payload = json.dumps({
        "id": f"chant_{int(duration * 1000)}",
        "snippet": snippet,
        "title": heading,
        "colophon": colophon,
        "raw_text": full_text,
        "beautifiedHtml": beautified_html,
        "duration": duration,
        "meters": list(set(meters)),
        "shlokaCount": shloka_count,
        "timestamps": all_timestamps,
        "audioSrc": audio_url
    })
    payload_escaped = html.escape(payload, quote=True)

    return f"""
    <div class="vagdhenu-lyrics-box vagdhenu-studio-lyrics">
        <div class="vagdhenu-lyrics-header">
            <div class="vagdhenu-lyrics-header-title">
                <span>🪔</span> Synchronized Verse Lyrics
            </div>
            <div class="vagdhenu-action-btn-group">
                <button id="vagdhenu-save-card-btn" class="vagdhenu-add-card-btn" onclick="window.saveCurrentToLibrary ? window.saveCurrentToLibrary(this) : alert('Initializing...')">
                    ➕ Add to Library
                </button>
                <button class="vagdhenu-export-btn-primary" onclick="window.openVideoStudio && window.openVideoStudio()">
                    🎬 Export Video (9:16 / 16:9)
                </button>
            </div>
        </div>
        <div class="vagdhenu-lyrics-scroller" id="vagdhenu-lyrics-scroller">
            {items_joined}
        </div>
        <div class="vagdhenu-lyrics-hint">
            💡 <em>Click any verse line to seek audio directly. Highlighting tracks playback automatically!</em>
        </div>
        <div id="vagdhenu-active-payload" style="display:none;" data-payload="{payload_escaped}"></div>
        <img src="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg'/>" style="display:none;" onload="window.vagdhenuOnLyricsRendered &amp;&amp; window.vagdhenuOnLyricsRendered()">
    </div>
    """


def _to_deva_digits(n):
    return str(n).translate(str.maketrans("0123456789", "०१२३४५६७८९"))


IDLE_LYRICS_PLACEHOLDER_HTML = """\
<div class="vagdhenu-idle-card">
    <div class="vagdhenu-idle-mandala">🪔</div>
    <div class="vagdhenu-idle-title">Sanctuary of Sacred Sound</div>
    <p class="vagdhenu-idle-desc">
        Select a classic shloka from the quick chips or inscribe your own verse, then click <strong>Chant it</strong> to experience authentic Vedic recitation with real-time synchronized karaoke tracking.
    </p>
    <div class="vagdhenu-idle-features">
        <span>✨ Auto Meter Detection</span>
        <span>•</span>
        <span>⚡ Synchronized Lyrics</span>
        <span>•</span>
        <span>🎬 9:16 HD Video Export</span>
    </div>
</div>
"""


def _fmt_secs(s):
    s = max(0, int(s))
    return f"{s // 60}:{s % 60:02d}"


def render_progress_card(job, ahead=0):
    """Lyrics-area card for the job the user is waiting on ("Chant it")."""
    import time
    pct = int(round(100 * float(job.get("progress") or 0)))
    if job["status"] == "rendering":
        el = _fmt_secs(time.time() - job.get("started", time.time()))
        title = "Chanting your verse…"
        line = f"{html.escape(job.get('desc') or '')} · {el} elapsed"
    else:
        title = "Waiting in the queue…"
        line = "Starts as soon as the chant ahead of it finishes." if ahead else "Starting…"
        if ahead:
            line = f"{ahead} chant{'s' if ahead > 1 else ''} ahead · " + line
    return f"""
<div class="vagdhenu-idle-card vagdhenu-rendering-card">
    <div class="vagdhenu-idle-mandala">🪔</div>
    <div class="vagdhenu-idle-title">{title}</div>
    <div class="vg-q-snip-lg">{html.escape(job.get('snippet') or '')}</div>
    <div class="vg-progress{' busy' if job['status'] == 'rendering' else ''}"><div class="vg-progress-fill" style="width:{max(pct, 3 if job['status'] == 'rendering' else 0)}%"></div></div>
    <p class="vagdhenu-idle-desc">{line}</p>
    <p class="vg-q-hint">You can keep working — queue the next verse or export a video meanwhile.</p>
</div>"""


def render_queue_html(jobs, follow_id=None):
    """The render-queue panel. Buttons talk to the server through window.vgQueueCmd()."""
    import time
    active = [j for j in jobs if j["status"] in ("queued", "rendering")]
    done = [j for j in jobs if j["status"] not in ("queued", "rendering")]
    done.sort(key=lambda j: j.get("finished") or j.get("created") or 0, reverse=True)
    if not jobs:
        body = ('<div class="vg-q-empty">Chants you queue appear here. Add several verses with '
                '<strong>➕ Add to queue</strong> — they render one after another in the background, '
                'and stay here after a restart.</div>')
    else:
        rows = []
        pos = 0
        for j in active + done:
            st, jid = j["status"], j["id"]
            snip = html.escape(j.get("snippet") or "")
            if st == "rendering":
                el = _fmt_secs(time.time() - j.get("started", time.time()))
                meta = f"{html.escape(j.get('desc') or '')} · {el}"
                pct = int(round(100 * float(j.get("progress") or 0)))
                bar = f'<div class="vg-progress sm busy"><div class="vg-progress-fill" style="width:{max(pct, 3)}%"></div></div>'
                acts = f'<button onclick="vgQueueCmd(\'open:{jid}\')">Follow</button>'
                chip = '<span class="vg-q-chip rendering">Rendering</span>'
            elif st == "queued":
                pos += 1
                meta, bar = f"Waiting · #{pos} in line", ""
                acts = f'<button onclick="vgQueueCmd(\'cancel:{jid}\')">Cancel</button>'
                chip = '<span class="vg-q-chip queued">Queued</span>'
            elif st == "done":
                r = j.get("result") or {}
                ms = ", ".join(sorted(set(r.get("meters") or [])))
                tan = " · tanpura" if j.get("tanpura_on") else ""
                tan += {"temple": " · temple bell", "pooja": " · pooja bell"}.get(j.get("bell"), "")
                meta, bar = f"{html.escape(ms)} · {r.get('dur', 0):.1f}s{tan}", ""
                acts = (f'<button class="primary" onclick="vgQueueCmd(\'open:{jid}\')">Open</button>'
                        f'<button onclick="vgQueueCmd(\'remove:{jid}\')" title="Remove from list">✕</button>')
                chip = '<span class="vg-q-chip done">Ready</span>'
            else:
                meta = html.escape(j.get("error") or j.get("desc") or st)
                bar = ""
                acts = f'<button onclick="vgQueueCmd(\'remove:{jid}\')" title="Remove from list">✕</button>'
                chip = f'<span class="vg-q-chip failed">{html.escape(st.title())}</span>'
            cur = " following" if jid == follow_id else ""
            rows.append(f'<div class="vg-q-item {st}{cur}"><div class="vg-q-main"><div class="vg-q-top">{chip}'
                        f'<span class="vg-q-snip">{snip}</span></div><div class="vg-q-meta">{meta}</div>{bar}</div>'
                        f'<div class="vg-q-actions">{acts}</div></div>')
        body = '<div class="vg-q-list">' + "".join(rows) + "</div>"
    clear = ('<button class="vagdhenu-add-card-btn" onclick="vgQueueCmd(\'clear\')">Clear finished</button>'
             if done else "")
    sub = f"{len(active)} in progress · {sum(1 for j in done if j['status'] == 'done')} ready"
    return f"""
<div class="vg-q">
  <div class="vg-q-head"><div><div class="vg-q-title">Render queue</div><div class="vg-q-sub">{sub}</div></div>{clear}</div>
  {body}
</div>"""


RENDERING_LYRICS_HTML = """\
<div class="vagdhenu-idle-card vagdhenu-rendering-card">
    <div class="vagdhenu-idle-mandala">🪔</div>
    <div class="vagdhenu-idle-title">Chanting your verse…</div>
    <p class="vagdhenu-idle-desc">
        The synced lyrics will appear here as soon as the chant is ready.
    </p>
</div>
"""


QUICK_CHIPS_HTML = """\
<div class="vagdhenu-quick-chips-wrapper">
    <div class="vagdhenu-quick-chips-title">
        <span>🪔 Quick Verse Treasury (Click to Load)</span>
    </div>
    <div class="vagdhenu-chips-row">
        <button id="chip-vasudeva" class="vagdhenu-chip-btn active-chip" onclick="window.loadQuickVerse('vasudeva')">
            🌸 Vasudevasutaṃ
        </button>
        <button id="chip-suklam" class="vagdhenu-chip-btn" onclick="window.loadQuickVerse('suklam')">
            ⚡ Śuklāmbaradharaṃ
        </button>
        <button id="chip-vakratunda" class="vagdhenu-chip-btn" onclick="window.loadQuickVerse('vakratunda')">
            🐘 Vakratuṇḍa Mahākāya
        </button>
        <button id="chip-gita247" class="vagdhenu-chip-btn" onclick="window.loadQuickVerse('gita247')">
            🏹 Gītā 2.47
        </button>
        <button id="chip-gayatrimantra" class="vagdhenu-chip-btn" onclick="window.loadQuickVerse('gayatrimantra')">
            ☀️ Gāyatrī Mantra
        </button>
        <button id="chip-gururbrahma" class="vagdhenu-chip-btn" onclick="window.loadQuickVerse('gururbrahma')">
            🕉️ Gururbrahmā
        </button>
        <button id="chip-yakundendu" class="vagdhenu-chip-btn" onclick="window.loadQuickVerse('yakundendu')">
            🌺 Yā Kundendu
        </button>
        <button id="chip-karagre" class="vagdhenu-chip-btn" onclick="window.loadQuickVerse('karagre')">
            🪷 Karāgre Vasate
        </button>
    </div>
</div>
"""


HEADER_HTML = """\
<div class="vagdhenu-header">
    <div class="vagdhenu-header-topline">
        <span class="vagdhenu-om-symbol">ॐ</span>
        <h1 class="vagdhenu-title">VĀGDHENU</h1>
    </div>
    <div class="vagdhenu-subtitle">वाग्धेनुः · Sacred Vedic & Classical Sanskrit Chant Studio</div>
    <div class="vagdhenu-tagline">
        Synthesize metered Vedic chanting with neural pitch modulation, automated chanda detection,
        and real-time synchronized karaoke verse lyrics.
    </div>
    <div class="vagdhenu-badges-row">
        <span class="vagdhenu-pill live-status">Neural Engine Ready</span>
        <span class="vagdhenu-pill">🪔 F5-TTS Diffusion</span>
        <span class="vagdhenu-pill">🪕 BigVGAN 24kHz</span>
        <span class="vagdhenu-pill">📜 Chandas Engine</span>
        <span class="vagdhenu-pill">⚡ Interactive Synced Lyrics</span>
        <span class="vagdhenu-pill">🎬 9:16 &amp; 16:9 Video Export</span>
    </div>
</div>
"""

LIBRARY_AND_MODAL_HTML = """\
<div class="vagdhenu-library-section">
    <div class="vagdhenu-library-header">
        <div class="vagdhenu-library-title">
            <span>📜</span> Sacred Chant Library
        </div>
        <button class="vagdhenu-add-card-btn" onclick="window.clearChantLibrary && window.clearChantLibrary()">Clear Library</button>
    </div>
    <p style="color: var(--vg-text-muted); font-size: 13px; margin-bottom: 16px;">
        Chants you compose during this session are preserved as cards. Click any card to expand into the cinematic view with beautified Sanskrit calligraphy, line seeking, and 9:16 video export!
    </p>
    <div id="vagdhenu-library-grid" class="vagdhenu-card-grid">
        <!-- Cards dynamically populated -->
    </div>
    <img src="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg'/>" style="display:none;" onload="window.renderLibraryCards &amp;&amp; window.renderLibraryCards()">
</div>

<!-- Expanded Modal Dialog -->
<div id="vagdhenu-modal-backdrop" class="vagdhenu-modal-backdrop" onclick="closeVagdhenuModal(event)">
    <div class="vagdhenu-modal-card" onclick="event.stopPropagation()">
        <div class="vagdhenu-modal-top">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span class="card-om" style="font-size: 24px;">ॐ</span>
                <div>
                    <h2 id="vagdhenu-modal-title" class="vagdhenu-modal-title"></h2>
                    <div id="vagdhenu-modal-meta" class="card-meta-row" style="margin: 4px 0 0 0;"></div>
                </div>
            </div>
            <button class="vagdhenu-modal-close-btn" onclick="closeVagdhenuModal()">✕</button>
        </div>
        
        <div class="vagdhenu-modal-content-area">
            <div class="vagdhenu-modal-section-tag">🎧 Synchronized Line-by-Line Audio Recitation</div>
            <div class="vagdhenu-modal-audio-wrap">
                <audio id="vagdhenu-modal-audio-player" controls></audio>
            </div>
            <div id="vagdhenu-modal-lyrics-list" class="vagdhenu-lyrics-scroller" style="max-height: 230px; margin-bottom: 20px;"></div>

            <div class="vagdhenu-modal-section-tag">📜 Complete Beautified Sanskrit Shloka Inscription</div>
            <div id="vagdhenu-modal-verse-text" class="vagdhenu-modal-devanagari-text"></div>
        </div>
        
        <div class="vagdhenu-modal-bottom-bar">
            <span style="color: var(--vg-text-dim); font-size: 12px; margin-right: auto;">
                💡 <em>Click any line to jump audio directly to that verse</em>
            </span>
            <a id="vagdhenu-modal-download-link" class="vagdhenu-add-card-btn" style="text-decoration: none; display: none; align-items: center; gap: 6px;" href="#" download="chant.wav">
                💾 Download Audio (.wav)
            </a>
            <button id="vagdhenu-modal-export-video-btn" class="vagdhenu-export-btn-primary" style="display: none; align-items: center; gap: 6px;" onclick="window.openVideoStudio && window.openVideoStudio()">
                🎬 Export Video (9:16 / 16:9)
            </button>
            <button class="card-btn" style="width: auto; padding: 6px 16px;" onclick="closeVagdhenuModal()">Close</button>
        </div>
    </div>
</div>
"""
