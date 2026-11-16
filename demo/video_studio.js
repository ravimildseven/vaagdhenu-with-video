// ==========================================================================
// VĀGDHENU — LYRIC VIDEO STUDIO
// Canvas renderer with five distinct styles, multiple photos (Ken Burns + crossfade, exact
// cover/contain fit), accent palettes and verse fonts. Recording is real-time (MediaRecorder,
// video only); the server muxes the ORIGINAL chant wav and converts to H.264 MP4 with ffmpeg.
// Public API used by the page: window.openVideoStudio(card?), window.closeVideoStudio().
// ==========================================================================
(() => {
  'use strict';

  // ── Catalogue ─────────────────────────────────────────────────────────
  const FONTS = [
    { id: 'tiro',   name: 'Tiro Sanskrit', css: '"Tiro Devanagari Sanskrit"', w: '400', wb: '400' },
    { id: 'noto',   name: 'Noto Serif',    css: '"Noto Serif Devanagari"',    w: '500', wb: '700' },
    { id: 'martel', name: 'Martel',        css: '"Martel"',                    w: '400', wb: '800' },
    { id: 'eczar',  name: 'Eczar',         css: '"Eczar"',                     w: '500', wb: '700' },
    { id: 'rozha',  name: 'Rozha One',     css: '"Rozha One"',                 w: '400', wb: '400' },
    { id: 'yatra',  name: 'Yatra One',     css: '"Yatra One"',                 w: '400', wb: '400' },
    { id: 'kalam',  name: 'Kalam',         css: '"Kalam"',                     w: '400', wb: '700' },
  ];
  const SCRIPT_FALLBACK = '"Noto Serif Kannada", "Noto Serif Telugu", "Noto Serif Devanagari", serif';
  const LATIN = '"Cormorant Garamond", Georgia, serif';
  const UI = '"Source Sans 3", system-ui, sans-serif';

  const ACCENTS = {
    saffron:   { name: 'Saffron gold', a: '#f4b740', b: '#c9671a' },
    vermilion: { name: 'Sindoor',      a: '#ff8159', b: '#b2381c' },
    peacock:   { name: 'Peacock',      a: '#52d6c9', b: '#16707c' },
    lotus:     { name: 'Lotus',        a: '#f59ec4', b: '#b23e74' },
    tulasi:    { name: 'Tulasī',       a: '#a8dc7a', b: '#3f7d2a' },
  };

  const TEMPLATES = [
    { id: 'temple',     name: 'Temple Glow',   desc: 'Full-bleed photos, rising embers, glowing line' },
    { id: 'manuscript', name: 'Palm-leaf',     desc: 'Parchment page, arched photo, whole verse' },
    { id: 'cinematic',  name: 'Cinematic',     desc: 'Film look, light leaks, subtitle line' },
    { id: 'mandala',    name: 'Mandala',       desc: 'Rotating mandala, round photo, progress ring' },
    { id: 'minimal',    name: 'Minimal',       desc: 'Big type, word-by-word reveal' },
  ];

  const PRESETS = [
    { id: 'diya',    label: '🪔 Diya',    src: '/api/assets/diya.jpg' },
    { id: 'ganesha', label: '🐘 Gaṇeśa',  src: '/api/assets/ganesha.jpg' },
    { id: 'shiva',   label: '🔱 Śiva',    src: '/api/assets/shiva.jpg' },
    { id: 'krishna', label: '🪈 Kṛṣṇa',   src: '/api/assets/krishna.jpg' },
  ];

  const DIMS = {
    '9:16': { 1080: [1080, 1920], 720: [720, 1280] },
    '16:9': { 1080: [1920, 1080], 720: [1280, 720] },
    '1:1':  { 1080: [1080, 1080], 720: [720, 720] },
  };

  const DEFAULT_OPTS = {
    template: 'temple', accent: 'saffron', font: 'tiro', ratio: '9:16', quality: 1080,
    fit: 'cover', kenburns: true, particles: true, grain: true, fade: true,
    showTitle: true, showMeter: true, showProgress: true,
  };
  const OPTS_KEY = 'vagdhenu_video_studio_opts';

  // ── Small utilities ───────────────────────────────────────────────────
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const easeOut = (x) => 1 - Math.pow(1 - clamp(x), 3);
  const easeInOut = (x) => { x = clamp(x); return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
  const hash = (n) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
  function hexRgb(h) { h = h.replace('#', ''); return [0, 2, 4].map(i => parseInt(h.substr(i, 2), 16)); }
  function rgba(h, a) { const [r, g, b] = hexRgb(h); return `rgba(${r},${g},${b},${a})`; }
  function shade(h, amt) {  // amt < 0 → towards black, > 0 → towards white
    const [r, g, b] = hexRgb(h); const t = amt < 0 ? 0 : 255; const p = Math.abs(amt);
    const f = (c) => Math.round(c + (t - c) * p);
    return `rgb(${f(r)},${f(g)},${f(b)})`;
  }
  function fmtTime(s) { s = Math.max(0, s); return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`; }
  function esc(s) { return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }
  function loadOpts() {
    try { return Object.assign({}, DEFAULT_OPTS, JSON.parse(localStorage.getItem(OPTS_KEY) || '{}')); }
    catch (e) { return Object.assign({}, DEFAULT_OPTS); }
  }
  function saveOpts(o) { try { localStorage.setItem(OPTS_KEY, JSON.stringify(o)); } catch (e) {} }

  function fontOf(opts) { return FONTS.find(f => f.id === opts.font) || FONTS[0]; }
  function verseFont(opts, size, bold) {
    const f = fontOf(opts);
    return `${bold ? f.wb : f.w} ${Math.round(size)}px ${f.css}, ${SCRIPT_FALLBACK}`;
  }

  function roundRect(c, x, y, w, h, r) {
    r = Math.min(r, w / 2, h / 2);
    c.beginPath(); c.moveTo(x + r, y); c.arcTo(x + w, y, x + w, y + h, r); c.arcTo(x + w, y + h, x, y + h, r);
    c.arcTo(x, y + h, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath();
  }
  function archPath(c, x, y, w, h) {
    const r = w / 2;
    if (h < r * 1.05) { roundRect(c, x, y, w, h, w * 0.06); return; }
    c.beginPath(); c.moveTo(x, y + h); c.lineTo(x, y + r); c.arc(x + r, y + r, r, Math.PI, 0); c.lineTo(x + w, y + h); c.closePath();
  }

  function wrapWords(ctx, text, maxW) {
    const words = String(text).trim().split(/\s+/); const lines = []; let cur = '';
    for (const w of words) {
      const t = cur ? cur + ' ' + w : w;
      if (cur && ctx.measureText(t).width > maxW) { lines.push(cur); cur = w; } else cur = t;
    }
    if (cur) lines.push(cur);
    return lines;
  }
  // Largest size ≤ size whose wrap fits in maxLines lines of maxW.
  function fitText(ctx, text, opts, size, maxW, maxLines, bold, minSize) {
    let s = size; minSize = minSize || size * 0.45;
    for (let i = 0; i < 24; i++) {
      ctx.font = verseFont(opts, s, bold);
      const lines = wrapWords(ctx, text, maxW);
      const widest = Math.max(...lines.map(l => ctx.measureText(l).width));
      if (lines.length <= maxLines && widest <= maxW) return { size: s, lines };
      if (s <= minSize) return { size: s, lines: lines.slice(0, maxLines) };
      s = Math.max(minSize, s * 0.92);
    }
    return { size: s, lines: wrapWords(ctx, text, maxW) };
  }
  // Draw wrapped lines with a left-to-right karaoke wipe from `base` to `hi` across all lines.
  function drawKaraoke(ctx, lines, x, y, lh, align, base, hi, prog, shadow) {
    ctx.textBaseline = 'middle'; ctx.textAlign = 'left';
    const widths = lines.map(l => ctx.measureText(l).width);
    const total = widths.reduce((a, b) => a + b, 0);
    let remain = prog * total;
    lines.forEach((ln, i) => {
      const w = widths[i];
      const lx = align === 'center' ? x - w / 2 : align === 'right' ? x - w : x;
      const ly = y + i * lh;
      ctx.save();
      if (shadow) { ctx.shadowColor = shadow.color; ctx.shadowBlur = shadow.blur; }
      ctx.fillStyle = base; ctx.fillText(ln, lx, ly);
      ctx.restore();
      const cut = clamp(remain, 0, w); remain -= w;
      if (cut > 0 && hi) {
        ctx.save(); ctx.beginPath(); ctx.rect(lx - 4, ly - lh, cut + 4, lh * 2); ctx.clip();
        if (shadow && shadow.hiColor) { ctx.shadowColor = shadow.hiColor; ctx.shadowBlur = shadow.blur * 1.4; }
        ctx.fillStyle = hi; ctx.fillText(ln, lx, ly); ctx.restore();
      }
    });
  }
  function plainLines(ctx, lines, x, y, lh, align, color) {
    ctx.textBaseline = 'middle'; ctx.textAlign = align; ctx.fillStyle = color;
    lines.forEach((l, i) => ctx.fillText(l, x, y + i * lh));
  }

  // ── Timeline helpers ──────────────────────────────────────────────────
  function lineState(st, t) {
    const L = st.lines; let idx = -1;
    for (let i = 0; i < L.length; i++) {
      const next = i + 1 < L.length ? L[i + 1].start : L[i].end + 1.2;
      if (t >= L[i].start - 0.15 && t < next) { idx = i; break; }
      if (i === L.length - 1 && t >= L[i].start) idx = i;
    }
    const cur = L[Math.max(0, idx)];
    const prog = idx < 0 ? 0 : clamp((t - cur.start) / Math.max(0.2, cur.end - cur.start));
    const since = idx < 0 ? 0 : t - cur.start;
    return { idx, show: Math.max(0, idx), prog, since, cur };
  }

  // ── Pre-rendered layers (cached per size) ─────────────────────────────
  function mkCanvas(w, h) { const c = document.createElement('canvas'); c.width = Math.max(1, Math.round(w)); c.height = Math.max(1, Math.round(h)); return c; }
  function cached(st, key, make) { if (!st.cache[key]) st.cache[key] = make(); return st.cache[key]; }

  function vignette(st, strength) {
    return cached(st, `vig${strength}`, () => {
      const c = mkCanvas(st.W, st.H), x = c.getContext('2d');
      const g = x.createRadialGradient(st.W / 2, st.H / 2, Math.min(st.W, st.H) * 0.25, st.W / 2, st.H / 2, Math.hypot(st.W, st.H) * 0.62);
      g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(0,0,0,${strength})`);
      x.fillStyle = g; x.fillRect(0, 0, st.W, st.H); return c;
    });
  }
  function grainTile(st) {
    return cached(st, 'grain', () => {
      const c = mkCanvas(256, 256), x = c.getContext('2d'), im = x.createImageData(256, 256);
      for (let i = 0; i < im.data.length; i += 4) { const v = Math.random() * 255; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 255; }
      x.putImageData(im, 0, 0); return c;
    });
  }
  function drawGrain(ctx, st, t, alpha) {
    if (!st.opts.grain) return;
    const tile = grainTile(st), pat = ctx.createPattern(tile, 'repeat');
    const f = Math.floor(t * 24);
    ctx.save(); ctx.globalAlpha = alpha; ctx.globalCompositeOperation = 'overlay';
    ctx.translate(-hash(f) * 256, -hash(f + 7) * 256); ctx.fillStyle = pat; ctx.fillRect(0, 0, st.W + 256, st.H + 256);
    ctx.restore();
  }
  function glowSprite(st, color) {
    return cached(st, 'glow' + color, () => {
      const c = mkCanvas(64, 64), x = c.getContext('2d'), g = x.createRadialGradient(32, 32, 0, 32, 32, 32);
      g.addColorStop(0, rgba(color, 1)); g.addColorStop(0.25, rgba(color, 0.55)); g.addColorStop(1, rgba(color, 0));
      x.fillStyle = g; x.fillRect(0, 0, 64, 64); return c;
    });
  }
  // kind: 'embers' rise; 'sparkle' drift & twinkle
  function drawParticles(ctx, st, t, color, kind, count) {
    if (!st.opts.particles) return;
    const spr = glowSprite(st, color), u = st.u;
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    for (let i = 0; i < count; i++) {
      const s1 = hash(i + 1), s2 = hash(i + 101), s3 = hash(i + 201), s4 = hash(i + 301);
      let x, y, a, size;
      if (kind === 'embers') {
        const speed = 0.04 + s3 * 0.08;  // screen-heights per second
        const p = (s2 + t * speed) % 1;
        y = st.H * (1.05 - p * 1.15);
        x = st.W * s1 + Math.sin(t * (0.6 + s4) + i) * u * 0.03;
        a = Math.sin(p * Math.PI) * (0.35 + 0.5 * s4);
        size = u * (0.006 + 0.014 * s3);
      } else {
        x = st.W * (((s1 + t * 0.006 * (s4 - 0.5)) % 1 + 1) % 1);
        y = st.H * (((s2 + t * 0.004 * (s3 - 0.5)) % 1 + 1) % 1);
        a = 0.25 + 0.6 * Math.max(0, Math.sin(t * (1 + s3 * 2) + i * 1.7));
        size = u * (0.004 + 0.01 * s4);
      }
      ctx.globalAlpha = clamp(a);
      ctx.drawImage(spr, x - size * 2, y - size * 2, size * 4, size * 4);
    }
    ctx.restore();
  }

  function mandalaSprite(st, R, color) {
    return cached(st, `mandala${Math.round(R)}${color}`, () => {
      const c = mkCanvas(R * 2, R * 2), x = c.getContext('2d');
      x.translate(R, R); x.strokeStyle = rgba(color, 0.55); x.fillStyle = rgba(color, 0.08);
      const rings = [[0.98, 48, 0.07], [0.84, 32, 0.11], [0.7, 24, 0.13], [0.56, 16, 0.15]];
      x.lineWidth = Math.max(1, R * 0.004);
      for (const [rr, n, pl] of rings) {
        const r0 = R * rr;
        x.beginPath(); x.arc(0, 0, r0, 0, Math.PI * 2); x.stroke();
        for (let i = 0; i < n; i++) {
          const a = (i / n) * Math.PI * 2;
          x.save(); x.rotate(a); x.beginPath();
          x.moveTo(r0 - R * pl, 0);
          x.quadraticCurveTo(r0 - R * pl * 0.4, R * pl * 0.42 * (12 / n) * 2, r0, 0);
          x.quadraticCurveTo(r0 - R * pl * 0.4, -R * pl * 0.42 * (12 / n) * 2, r0 - R * pl, 0);
          x.fill(); x.stroke(); x.restore();
        }
      }
      for (let i = 0; i < 64; i++) {  // dotted outer ring
        const a = (i / 64) * Math.PI * 2;
        x.beginPath(); x.arc(Math.cos(a) * R * 0.92, Math.sin(a) * R * 0.92, R * 0.006, 0, Math.PI * 2);
        x.fillStyle = rgba(color, 0.7); x.fill();
      }
      return c;
    });
  }

  function parchment(st) {
    return cached(st, 'parchment', () => {
      const c = mkCanvas(st.W, st.H), x = c.getContext('2d');
      const g = x.createLinearGradient(0, 0, st.W * 0.3, st.H);
      g.addColorStop(0, '#f6ead0'); g.addColorStop(0.55, '#efdfbb'); g.addColorStop(1, '#e4cd9d');
      x.fillStyle = g; x.fillRect(0, 0, st.W, st.H);
      // palm-leaf fibres: faint horizontal streaks
      for (let i = 0; i < 900; i++) {
        const y = Math.random() * st.H, len = st.W * (0.05 + Math.random() * 0.4), x0 = Math.random() * st.W;
        x.strokeStyle = `rgba(120,85,40,${0.02 + Math.random() * 0.05})`;
        x.lineWidth = Math.random() * 1.6 + 0.3;
        x.beginPath(); x.moveTo(x0, y); x.lineTo(x0 + len, y + (Math.random() - 0.5) * 2); x.stroke();
      }
      const v = x.createRadialGradient(st.W / 2, st.H / 2, Math.min(st.W, st.H) * 0.3, st.W / 2, st.H / 2, Math.hypot(st.W, st.H) * 0.6);
      v.addColorStop(0, 'rgba(110,70,20,0)'); v.addColorStop(1, 'rgba(110,70,20,0.28)');
      x.fillStyle = v; x.fillRect(0, 0, st.W, st.H);
      return c;
    });
  }

  // ── Photos ────────────────────────────────────────────────────────────
  async function loadImage(src) {
    const img = new Image(); img.crossOrigin = 'anonymous';
    await new Promise((res, rej) => { img.onload = res; img.onerror = () => rej(new Error('Could not load image')); img.src = src; });
    // downscale big photos once: keeps per-frame drawing cheap at 1080p
    const maxSide = 2400, k = Math.min(1, maxSide / Math.max(img.naturalWidth, img.naturalHeight));
    const c = mkCanvas(img.naturalWidth * k, img.naturalHeight * k);
    const x = c.getContext('2d'); x.imageSmoothingQuality = 'high'; x.drawImage(img, 0, 0, c.width, c.height);
    const b = mkCanvas(Math.max(8, c.width / 16), Math.max(8, c.height / 16));  // tiny copy = soft backdrop when upscaled
    const bx = b.getContext('2d'); bx.filter = 'blur(2px)'; bx.drawImage(c, 0, 0, b.width, b.height);
    return { canvas: c, blur: b, w: c.width, h: c.height };
  }

  const KB_PATHS = [[1, 0.2], [-0.8, -0.4], [0.3, -1], [-0.5, 0.8], [0.9, 0.7], [-1, -0.1]];
  // Draw photo `ph` into rect with exact aspect handling. u: 0..1 through this photo's screen time.
  function drawPhoto(ctx, st, ph, rect, u, zoomAmt, idx) {
    const { x, y, w, h } = rect;
    const kb = st.opts.kenburns;
    const zin = idx % 2 === 0;
    const z = 1 + (kb ? (zin ? u : 1 - u) * zoomAmt : 0);
    const [px, py] = KB_PATHS[idx % KB_PATHS.length];
    if (st.opts.fit === 'contain') {
      // whole photo visible, soft blurred fill behind it (no stretching, no crop)
      const sb = Math.max(w / ph.w, h / ph.h) * 1.15;
      ctx.save(); ctx.globalAlpha *= 0.9;
      ctx.drawImage(ph.blur, x + (w - ph.w * sb) / 2, y + (h - ph.h * sb) / 2, ph.w * sb, ph.h * sb);
      ctx.fillStyle = 'rgba(0,0,0,0.18)'; ctx.fillRect(x, y, w, h);
      ctx.restore();
      const s = Math.min(w / ph.w, h / ph.h) * (1 + (kb ? (zin ? u : 1 - u) * zoomAmt * 0.35 : 0));
      const dw = ph.w * s, dh = ph.h * s;
      ctx.drawImage(ph.canvas, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh);
    } else {
      // fill the frame, centre-cropped; pan never exposes an edge
      const s = Math.max(w / ph.w, h / ph.h) * z;
      const dw = ph.w * s, dh = ph.h * s;
      const mx = (dw - w) / 2, my = (dh - h) / 2;
      const pu = kb ? (u - 0.5) : 0;
      ctx.drawImage(ph.canvas, x - mx + px * mx * pu * 1.6, y - my + py * my * pu * 1.6, dw, dh);
    }
  }
  // Slideshow across the whole duration with crossfades.
  function drawSlideshow(ctx, st, rect, t, zoomAmt, xf) {
    const P = st.photos; if (!P.length) return false;
    const n = P.length, seg = st.dur / n;
    const i = Math.min(n - 1, Math.floor(clamp(t, 0, st.dur - 1e-3) / seg));
    const uOf = (k) => clamp((t - (k * seg - xf)) / (seg + xf));
    if (i > 0 && t - i * seg < xf) {
      drawPhoto(ctx, st, P[i - 1], rect, uOf(i - 1), zoomAmt, i - 1);
      ctx.save(); ctx.globalAlpha *= easeInOut((t - i * seg) / xf);
      drawPhoto(ctx, st, P[i], rect, uOf(i), zoomAmt, i); ctx.restore();
    } else {
      drawPhoto(ctx, st, P[i], rect, uOf(i), zoomAmt, i);
    }
    return true;
  }

  function header(ctx, st, x, y, align, colors, sizeK) {
    const u = st.u, o = st.opts;
    if (o.showTitle && st.title) {
      const r = fitText(ctx, st.title, o, u * 0.046 * sizeK, st.W * 0.84, 1, true);
      ctx.font = verseFont(o, r.size, true);
      plainLines(ctx, r.lines, x, y, 0, align, colors.title);
      y += r.size * 0.95;
    }
    if (o.showMeter && st.meterStr) {
      ctx.font = `600 ${Math.round(u * 0.019 * sizeK)}px ${UI}`;
      try { ctx.letterSpacing = `${(u * 0.004).toFixed(1)}px`; } catch (e) {}
      plainLines(ctx, [st.meterStr.toUpperCase()], x, y, 0, align, colors.meta);
      try { ctx.letterSpacing = '0px'; } catch (e) {}
    }
  }

  // ── Templates ─────────────────────────────────────────────────────────
  const T = {};

  T.temple = function (ctx, st, t) {
    const { W, H, u, opts } = st, ac = ACCENTS[opts.accent];
    ctx.fillStyle = '#0b0705'; ctx.fillRect(0, 0, W, H);
    if (!drawSlideshow(ctx, st, { x: 0, y: 0, w: W, h: H }, t, 0.12, 1.4)) {
      const g = ctx.createRadialGradient(W / 2, H * 0.4, 0, W / 2, H * 0.4, Math.max(W, H) * 0.7);
      g.addColorStop(0, shade(ac.b, -0.35)); g.addColorStop(1, '#060403'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
      ctx.save(); ctx.globalAlpha = 0.35; ctx.translate(W / 2, H * 0.4); ctx.rotate(t * 0.03);
      const R = Math.min(W, H) * 0.42, m = mandalaSprite(st, R, ac.a); ctx.drawImage(m, -R, -R); ctx.restore();
    }
    // warm grade + legibility scrim
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, 'rgba(10,5,0,0.55)'); g.addColorStop(0.35, 'rgba(10,5,0,0.12)');
    g.addColorStop(0.5, 'rgba(10,5,0,0.4)'); g.addColorStop(0.72, 'rgba(10,5,0,0.78)'); g.addColorStop(1, 'rgba(8,4,0,0.94)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    ctx.drawImage(vignette(st, 0.7), 0, 0);
    drawParticles(ctx, st, t, ac.a, 'embers', 46);

    ctx.save(); ctx.shadowColor = 'rgba(0,0,0,0.6)'; ctx.shadowBlur = u * 0.02;
    ctx.font = `${Math.round(u * 0.05)}px ${fontOf(opts).css}, ${SCRIPT_FALLBACK}`;
    plainLines(ctx, ['ॐ'], W / 2, H * 0.06, 0, 'center', ac.a);
    header(ctx, st, W / 2, H * 0.06 + u * 0.065, 'center', { title: '#fff8ec', meta: rgba(ac.a, 0.9) }, 1);
    ctx.restore();

    const ls = lineState(st, t), L = st.lines;
    const cy = H * (W > H ? 0.7 : 0.72), maxW = W * 0.84;
    const k = easeOut(ls.since / 0.45);
    // previous line drifting up
    if (ls.idx > 0) {
      const r = fitText(ctx, L[ls.idx - 1].text, opts, u * 0.034, maxW, 2, false);
      ctx.font = verseFont(opts, r.size, false);
      ctx.globalAlpha = 0.42 * (0.6 + 0.4 * (1 - k));
      plainLines(ctx, r.lines, W / 2, cy - u * 0.13 - u * 0.03 * k - (r.lines.length - 1) * r.size * 1.25, r.size * 1.25, 'center', '#f3e7d3');
      ctx.globalAlpha = 1;
    }
    const r = fitText(ctx, L[ls.show].text, opts, u * 0.062, maxW, 2, true);
    ctx.font = verseFont(opts, r.size, true);
    ctx.globalAlpha = 0.25 + 0.75 * k;
    drawKaraoke(ctx, r.lines, W / 2, cy + u * 0.025 * (1 - k) - (r.lines.length - 1) * r.size * 0.62, r.size * 1.25,
      'center', 'rgba(255,248,236,0.62)', ac.a, ls.prog,
      { color: 'rgba(0,0,0,0.65)', blur: u * 0.018, hiColor: rgba(ac.a, 0.85) });
    ctx.globalAlpha = 1;
    if (ls.show + 1 < L.length) {
      const rn = fitText(ctx, L[ls.show + 1].text, opts, u * 0.032, maxW, 1, false);
      ctx.font = verseFont(opts, rn.size, false); ctx.globalAlpha = 0.38 * k;
      plainLines(ctx, rn.lines, W / 2, cy + u * 0.13 + (r.lines.length - 1) * r.size * 0.62, 0, 'center', '#f3e7d3');
      ctx.globalAlpha = 1;
    }
    if (opts.showProgress) {
      const p = clamp(t / st.dur), y = H - u * 0.045;
      ctx.fillStyle = 'rgba(255,255,255,0.14)'; ctx.fillRect(W * 0.12, y, W * 0.76, Math.max(2, u * 0.003));
      const pg = ctx.createLinearGradient(W * 0.12, 0, W * 0.88, 0); pg.addColorStop(0, ac.b); pg.addColorStop(1, ac.a);
      ctx.fillStyle = pg; ctx.fillRect(W * 0.12, y, W * 0.76 * p, Math.max(2, u * 0.003));
    }
    drawGrain(ctx, st, t, 0.08);
  };

  T.manuscript = function (ctx, st, t) {
    const { W, H, u, opts } = st, ac = ACCENTS[opts.accent];
    const INK = '#2a1c12', INK2 = '#6b5440';
    ctx.drawImage(parchment(st), 0, 0);
    // double-ruled folio frame
    const m = u * 0.035;
    ctx.strokeStyle = rgba('#8a6a3a', 0.65); ctx.lineWidth = Math.max(1.5, u * 0.003); ctx.strokeRect(m, m, W - 2 * m, H - 2 * m);
    ctx.lineWidth = Math.max(1, u * 0.0012); ctx.strokeRect(m + u * 0.012, m + u * 0.012, W - 2 * m - u * 0.024, H - 2 * m - u * 0.024);

    const land = W > H * 1.2, sq = !land && W > H * 0.8;
    const hasPhoto = st.photos.length > 0;
    let photo, text;
    if (land) {
      photo = { x: W * 0.07, y: H * 0.12, w: W * 0.34, h: H * 0.76 };
      text = { x: hasPhoto ? W * 0.47 : W * 0.12, y: H * 0.26, w: hasPhoto ? W * 0.46 : W * 0.76, h: H * 0.56 };
    } else if (sq) {
      photo = { x: W * 0.3, y: H * 0.16, w: W * 0.4, h: H * 0.36 };
      text = { x: W * 0.1, y: hasPhoto ? H * 0.58 : H * 0.3, w: W * 0.8, h: hasPhoto ? H * 0.3 : H * 0.55 };
    } else {
      photo = { x: W * 0.14, y: H * 0.14, w: W * 0.72, h: H * 0.37 };
      text = { x: W * 0.1, y: hasPhoto ? H * 0.57 : H * 0.28, w: W * 0.8, h: hasPhoto ? H * 0.31 : H * 0.55 };
    }
    if (hasPhoto) {
      ctx.save(); ctx.shadowColor = 'rgba(80,50,15,0.45)'; ctx.shadowBlur = u * 0.03; ctx.shadowOffsetY = u * 0.008;
      archPath(ctx, photo.x, photo.y, photo.w, photo.h); ctx.fillStyle = '#d9c39a'; ctx.fill(); ctx.restore();
      ctx.save(); archPath(ctx, photo.x, photo.y, photo.w, photo.h); ctx.clip();
      drawSlideshow(ctx, st, photo, t, 0.08, 1.2); ctx.restore();
      ctx.strokeStyle = '#a77c2b'; ctx.lineWidth = Math.max(2, u * 0.005); archPath(ctx, photo.x, photo.y, photo.w, photo.h); ctx.stroke();
      const g = u * 0.012; ctx.lineWidth = Math.max(1, u * 0.0015);
      archPath(ctx, photo.x - g, photo.y - g, photo.w + 2 * g, photo.h + 2 * g); ctx.stroke();
    }
    const hx = land ? text.x + text.w / 2 : W / 2, hy = land ? H * 0.14 : (hasPhoto ? H * 0.075 : H * 0.12);
    ctx.font = `${Math.round(u * 0.036)}px ${fontOf(opts).css}, ${SCRIPT_FALLBACK}`;
    if (!land || !opts.showTitle) plainLines(ctx, ['॥ श्रीः ॥'], hx, hy - u * 0.035, 0, 'center', ac.b);
    header(ctx, st, hx, hy + (land ? 0 : u * 0.01), 'center', { title: INK, meta: ac.b }, 0.9);

    // whole current verse, active line in accent with a wipe
    const ls = lineState(st, t), L = st.lines, cur = L[ls.show];
    const group = L.map((l, i) => ({ ...l, i })).filter(l => l.shloka_idx === cur.shloka_idx);
    const lastI = group[group.length - 1].i;
    const label = (l) => l.text + (l.i === lastI ? ' ॥' : ' ।');
    let size = u * 0.05, laid;
    for (let it = 0; it < 18; it++) {
      ctx.font = verseFont(opts, size, false);
      laid = group.map(l => wrapWords(ctx, label(l), text.w));
      const rows = laid.reduce((a, b) => a + b.length, 0);
      const widest = Math.max(...laid.flat().map(s => ctx.measureText(s).width));
      if (rows * size * 1.55 + (group.length - 1) * size * 0.35 <= text.h && widest <= text.w) break;
      size *= 0.92;
    }
    const lh = size * 1.55;
    const totalH = laid.reduce((a, b) => a + b.length, 0) * lh + (group.length - 1) * size * 0.35;
    let y = text.y + (text.h - totalH) / 2 + lh / 2;
    const gfade = easeOut((t - group[0].start + 0.15) / 0.5);
    ctx.globalAlpha = 0.3 + 0.7 * gfade;
    group.forEach((l, gi) => {
      const active = l.i === ls.show && ls.idx >= 0, past = l.i < ls.show;
      ctx.font = verseFont(opts, size, active);
      if (active) {
        drawKaraoke(ctx, laid[gi], text.x + text.w / 2, y, lh, 'center', rgba(INK, 0.55), ac.b, ls.prog, null);
      } else {
        plainLines(ctx, laid[gi], text.x + text.w / 2, y, lh, 'center', past ? INK : rgba(INK2, 0.6));
      }
      y += laid[gi].length * lh + size * 0.35;
    });
    ctx.globalAlpha = 1;

    if (opts.showProgress) {
      const nV = st.shlokaCount, vi = cur.shloka_idx || 1;
      ctx.font = `600 ${Math.round(u * 0.018)}px ${UI}`;
      const by = H - m - u * 0.05;
      if (nV > 1) plainLines(ctx, [`श्लोकः ${vi} / ${nV}`], W / 2, by - u * 0.03, 0, 'center', INK2);
      ctx.fillStyle = rgba(INK, 0.12); ctx.fillRect(W * 0.3, by, W * 0.4, Math.max(2, u * 0.003));
      ctx.fillStyle = ac.b; ctx.fillRect(W * 0.3, by, W * 0.4 * clamp(t / st.dur), Math.max(2, u * 0.003));
    }
  };

  T.cinematic = function (ctx, st, t) {
    const { W, H, u, opts } = st, ac = ACCENTS[opts.accent];
    ctx.fillStyle = '#050505'; ctx.fillRect(0, 0, W, H);
    if (!drawSlideshow(ctx, st, { x: 0, y: 0, w: W, h: H }, t, 0.2, 1.8)) {
      const g = ctx.createLinearGradient(0, 0, W, H); g.addColorStop(0, shade(ac.b, -0.6)); g.addColorStop(1, '#050505');
      ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    }
    // light leaks
    ctx.save(); ctx.globalCompositeOperation = 'screen';
    for (let i = 0; i < 2; i++) {
      const lx = W * (0.5 + 0.55 * Math.sin(t * 0.11 + i * 2.4)), ly = H * (0.3 + 0.35 * Math.cos(t * 0.08 + i * 1.3));
      const R = Math.max(W, H) * (0.45 + 0.1 * i), lg = ctx.createRadialGradient(lx, ly, 0, lx, ly, R);
      lg.addColorStop(0, rgba(i ? ac.b : ac.a, 0.22)); lg.addColorStop(1, rgba(ac.a, 0));
      ctx.fillStyle = lg; ctx.fillRect(0, 0, W, H);
    }
    ctx.restore();
    const sg = ctx.createLinearGradient(0, H * 0.45, 0, H);
    sg.addColorStop(0, 'rgba(0,0,0,0)'); sg.addColorStop(1, 'rgba(0,0,0,0.88)'); ctx.fillStyle = sg; ctx.fillRect(0, H * 0.45, W, H * 0.55);
    const tg = ctx.createLinearGradient(0, 0, 0, H * 0.22); tg.addColorStop(0, 'rgba(0,0,0,0.55)'); tg.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = tg; ctx.fillRect(0, 0, W, H * 0.22);
    ctx.drawImage(vignette(st, 0.55), 0, 0);
    drawParticles(ctx, st, t, '#ffffff', 'sparkle', 18);

    // title card for the first seconds, then a small corner title
    const land = W > H * 1.2;
    const intro = 1 - easeInOut((t - 2.6) / 0.8);
    if (opts.showTitle && st.title && intro > 0) {
      ctx.save(); ctx.globalAlpha = intro * easeOut(t / 0.6);
      const r = fitText(ctx, st.title, opts, u * 0.075, W * 0.8, 2, true);
      ctx.font = verseFont(opts, r.size, true); ctx.shadowColor = 'rgba(0,0,0,0.7)'; ctx.shadowBlur = u * 0.03;
      plainLines(ctx, r.lines, W / 2, H * 0.42 - (r.lines.length - 1) * r.size * 0.6, r.size * 1.2, 'center', '#ffffff');
      ctx.fillStyle = ac.a; ctx.fillRect(W / 2 - u * 0.06, H * 0.42 + r.size * (0.75 + (r.lines.length - 1) * 0.6), u * 0.12, Math.max(2, u * 0.004));
      ctx.restore();
    }
    ctx.save(); ctx.globalAlpha = 1 - intro;
    header(ctx, st, land ? W * 0.06 : W / 2, H * 0.06, land ? 'left' : 'center', { title: '#ffffff', meta: rgba(ac.a, 0.95) }, 0.75);
    ctx.restore();

    const ls = lineState(st, t), L = st.lines;
    const align = land ? 'left' : 'center', x = land ? W * 0.07 : W / 2, maxW = land ? W * 0.72 : W * 0.86;
    const k = easeOut(ls.since / 0.4);
    const r = fitText(ctx, L[ls.show].text, opts, u * (land ? 0.058 : 0.056), maxW, 2, true);
    ctx.font = verseFont(opts, r.size, true);
    const cy = H * (land ? 0.8 : 0.79) - (r.lines.length - 1) * r.size * 1.2;
    ctx.globalAlpha = k;
    drawKaraoke(ctx, r.lines, x, cy + u * 0.02 * (1 - k), r.size * 1.22, align, 'rgba(255,255,255,0.9)', ac.a, ls.prog,
      { color: 'rgba(0,0,0,0.85)', blur: u * 0.012 });
    ctx.globalAlpha = 1;
    if (ls.show + 1 < L.length) {
      const rn = fitText(ctx, L[ls.show + 1].text, opts, u * 0.028, maxW, 1, false);
      ctx.font = verseFont(opts, rn.size, false); ctx.globalAlpha = 0.5 * k;
      plainLines(ctx, rn.lines, x, cy + r.lines.length * r.size * 1.22 + u * 0.025, 0, align, '#e9e2d6');
      ctx.globalAlpha = 1;
    }
    if (opts.showProgress) {
      ctx.fillStyle = rgba(ac.a, 0.95); ctx.fillRect(0, H - Math.max(3, u * 0.004), W * clamp(t / st.dur), Math.max(3, u * 0.004));
    }
    drawGrain(ctx, st, t, 0.12);
  };

  T.mandala = function (ctx, st, t) {
    const { W, H, u, opts } = st, ac = ACCENTS[opts.accent];
    const land = W > H * 1.2;
    const sq = !land && W > H * 0.8;
    const cx = land ? W * 0.26 : W / 2, cy = land ? H / 2 : H * (sq ? 0.38 : 0.34);
    const R = land ? H * 0.40 : Math.min(W * 0.40, H * (sq ? 0.27 : 0.25));
    const SR = R * (land ? 1.3 : 1.4);  // mandala radius — kept clear of the text block
    const bg = ctx.createRadialGradient(cx, cy, 0, cx, cy, Math.max(W, H) * 0.85);
    bg.addColorStop(0, shade(ac.b, -0.45)); bg.addColorStop(0.6, shade(ac.b, -0.8)); bg.addColorStop(1, '#050306');
    ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
    // rays
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(-t * 0.05); ctx.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 18; i++) {
      ctx.rotate(Math.PI * 2 / 18); const rg = ctx.createLinearGradient(0, 0, Math.max(W, H), 0);
      rg.addColorStop(0, rgba(ac.a, 0.10)); rg.addColorStop(1, rgba(ac.a, 0));
      ctx.fillStyle = rg; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.max(W, H), -u * 0.05); ctx.lineTo(Math.max(W, H), u * 0.05); ctx.fill();
    }
    ctx.restore();
    const ms = mandalaSprite(st, SR, ac.a);
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(t * 0.06); ctx.globalAlpha = 0.85; ctx.drawImage(ms, -SR, -SR); ctx.restore();
    drawParticles(ctx, st, t, ac.a, 'sparkle', 30);
    const pr = R * 0.78;
    ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, pr, 0, Math.PI * 2); ctx.fillStyle = shade(ac.b, -0.7); ctx.fill(); ctx.clip();
    if (!drawSlideshow(ctx, st, { x: cx - pr, y: cy - pr, w: pr * 2, h: pr * 2 }, t, 0.1, 1.2)) {
      ctx.font = `${Math.round(pr * 1.0)}px ${fontOf(opts).css}, ${SCRIPT_FALLBACK}`;
      plainLines(ctx, ['ॐ'], cx, cy + pr * 0.08, 0, 'center', ac.a);
    }
    ctx.restore();
    ctx.lineWidth = Math.max(2, u * 0.004); ctx.strokeStyle = rgba(ac.a, 0.9);
    ctx.beginPath(); ctx.arc(cx, cy, pr, 0, Math.PI * 2); ctx.stroke();
    if (opts.showProgress) {  // progress ring
      ctx.lineWidth = Math.max(3, u * 0.008); ctx.strokeStyle = rgba('#ffffff', 0.15);
      ctx.beginPath(); ctx.arc(cx, cy, pr + u * 0.022, 0, Math.PI * 2); ctx.stroke();
      ctx.strokeStyle = ac.a; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.arc(cx, cy, pr + u * 0.022, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * clamp(t / st.dur)); ctx.stroke();
      ctx.lineCap = 'butt';
    }
    const tx = land ? W * 0.77 : W / 2, maxW = land ? W * 0.36 : W * 0.86;
    const ty = Math.max(cy + pr + u * 0.1, H * (sq ? 0.66 : 0.68));
    ctx.save(); ctx.shadowColor = 'rgba(0,0,0,0.5)'; ctx.shadowBlur = u * 0.015;
    header(ctx, st, tx, land ? H * 0.12 : u * 0.07, 'center', { title: '#fff6ea', meta: rgba(ac.a, 0.95) }, 0.85);
    ctx.restore();
    const ls = lineState(st, t), L = st.lines, k = easeOut(ls.since / 0.45);
    const r = fitText(ctx, L[ls.show].text, opts, u * 0.058, maxW, land ? 3 : 2, true);
    ctx.font = verseFont(opts, r.size, true);
    const ly = land ? H * 0.5 - (r.lines.length - 1) * r.size * 0.62 : ty + u * 0.04;
    ctx.globalAlpha = k; ctx.save(); ctx.translate(tx, ly); ctx.scale(0.96 + 0.04 * k, 0.96 + 0.04 * k);
    drawKaraoke(ctx, r.lines, 0, 0, r.size * 1.25, 'center', 'rgba(255,246,234,0.6)', '#ffffff', ls.prog,
      { color: rgba(ac.a, 0.0), blur: u * 0.02, hiColor: rgba(ac.a, 0.9) });
    ctx.restore(); ctx.globalAlpha = 1;
    if (ls.show + 1 < L.length) {
      const rn = fitText(ctx, L[ls.show + 1].text, opts, u * 0.03, maxW, 1, false);
      ctx.font = verseFont(opts, rn.size, false); ctx.globalAlpha = 0.45 * k;
      plainLines(ctx, rn.lines, tx, ly + r.lines.length * r.size * 1.25 + u * 0.03, 0, 'center', '#efe2d0');
      ctx.globalAlpha = 1;
    }
    drawGrain(ctx, st, t, 0.05);
  };

  T.minimal = function (ctx, st, t) {
    const { W, H, u, opts } = st, ac = ACCENTS[opts.accent];
    ctx.fillStyle = shade(ac.b, -0.78); ctx.fillRect(0, 0, W, H);
    if (st.photos.length) {  // atmospheric photo wash
      ctx.save(); ctx.globalAlpha = 0.2; drawSlideshow(ctx, st, { x: 0, y: 0, w: W, h: H }, t, 0.06, 2); ctx.restore();
      ctx.fillStyle = rgba('#000000', 0.25); ctx.fillRect(0, 0, W, H);
    }
    const land = W > H * 1.2, pad = land ? W * 0.09 : W * 0.1;
    ctx.fillStyle = ac.a; ctx.fillRect(pad, H * 0.1, u * 0.06, Math.max(3, u * 0.005));
    header(ctx, st, pad, H * 0.1 + u * 0.06, 'left', { title: '#f7f1e6', meta: rgba(ac.a, 0.95) }, 0.85);

    const ls = lineState(st, t), L = st.lines;
    const maxW = W - pad * 2;
    const r = fitText(ctx, L[ls.show].text, opts, u * (land ? 0.075 : 0.08), maxW, 3, true);
    ctx.font = verseFont(opts, r.size, true);
    const lh = r.size * 1.3, cy = H * 0.5 - (r.lines.length - 1) * lh / 2;
    // previous line slides up and away
    const k = easeOut(ls.since / 0.5);
    if (ls.idx > 0 && k < 1) {
      const rp = fitText(ctx, L[ls.idx - 1].text, opts, u * (land ? 0.075 : 0.08), maxW, 3, true);
      ctx.font = verseFont(opts, rp.size, true); ctx.globalAlpha = 1 - k;
      plainLines(ctx, rp.lines, pad, H * 0.5 - (rp.lines.length - 1) * rp.size * 0.65 - u * 0.12 * k, rp.size * 1.3, 'left', '#f7f1e6');
      ctx.globalAlpha = 1; ctx.font = verseFont(opts, r.size, true);
    }
    // word-by-word reveal across the line's duration
    const words = r.lines.map(l => l.split(/\s+/));
    const nW = words.reduce((a, b) => a + b.length, 0);
    let wi = 0;
    ctx.textBaseline = 'middle'; ctx.textAlign = 'left';
    words.forEach((ws, li) => {
      let x = pad; const y = cy + li * lh + u * 0.02 * (1 - k);
      ws.forEach(w => {
        const appear = ls.idx < 0 ? 0 : clamp((ls.prog * nW - wi) * 1.6 + 0.35);
        const done = ls.idx >= 0 && ls.prog * nW > wi + 1;
        ctx.globalAlpha = 0.18 + 0.82 * appear;
        ctx.fillStyle = done ? '#f7f1e6' : (appear > 0.35 ? ac.a : '#f7f1e6');
        ctx.fillText(w, x, y - u * 0.012 * (1 - appear));
        x += ctx.measureText(w + ' ').width; wi++;
      });
    });
    ctx.globalAlpha = 1;
    if (opts.showProgress) {  // one dot per line
      const n = L.length, gap = Math.min(u * 0.03, (W - pad * 2) / Math.max(1, n));
      for (let i = 0; i < n; i++) {
        ctx.beginPath(); ctx.arc(pad + i * gap + gap / 2, H * 0.9, Math.max(2, u * 0.005), 0, Math.PI * 2);
        ctx.fillStyle = i < ls.show ? rgba('#f7f1e6', 0.8) : i === ls.show ? ac.a : rgba('#f7f1e6', 0.2); ctx.fill();
      }
    }
    drawGrain(ctx, st, t, 0.05);
  };

  function drawFrame(ctx, st, t) {
    ctx.save();
    (T[st.opts.template] || T.temple)(ctx, st, t);
    ctx.restore();
    if (st.opts.fade) {
      const a = Math.max(1 - clamp(t / 0.6), clamp((t - (st.dur - 0.9)) / 0.9));
      if (a > 0) { ctx.fillStyle = `rgba(0,0,0,${a})`; ctx.fillRect(0, 0, st.W, st.H); }
    }
  }

  // ── State built from a chant card ─────────────────────────────────────
  function buildState(card, opts, photos, W, H, title) {
    const lines = (card.timestamps || []).map(x => ({ ...x, shloka_idx: x.shloka_idx || 1 }));
    return {
      W, H, u: Math.min(W, H), opts, photos, lines, cache: {},
      dur: Math.max(card.duration || 0, lines.length ? lines[lines.length - 1].end : 0),
      title: title || '',
      meterStr: (card.meters && card.meters.length) ? card.meters.join(' · ') : '',
      shlokaCount: card.shlokaCount || new Set(lines.map(l => l.shloka_idx)).size || 1,
    };
  }
  async function ensureFonts(opts, sample) {
    if (!document.fonts || !document.fonts.load) return;
    const f = fontOf(opts), s = (sample || 'ॐ नमः') + ' ॐ';
    try {
      await Promise.all([
        document.fonts.load(`${f.w} 40px ${f.css}`, s), document.fonts.load(`${f.wb} 40px ${f.css}`, s),
        document.fonts.load(`400 40px "Noto Serif Kannada"`, 'ಕ'), document.fonts.load(`600 20px "Source Sans 3"`, 'A'),
      ]);
    } catch (e) { /* fall back to whatever is available */ }
  }

  // ── Studio UI ─────────────────────────────────────────────────────────
  const S = { card: null, opts: loadOpts(), photos: [], previewT: 0, playing: false, audio: null, raf: 0 };

  function el(html) { const d = document.createElement('div'); d.innerHTML = html.trim(); return d.firstChild; }

  function buildModal() {
    if (document.getElementById('vg-vs-backdrop')) return;
    const m = el(`
<div id="vg-vs-backdrop" class="vagdhenu-modal-backdrop vg-vs-backdrop" style="display:none">
  <div class="vagdhenu-modal-card vg-vs-card" role="dialog" aria-label="Lyric video studio">
    <div class="vagdhenu-modal-top">
      <div>
        <h2 class="vagdhenu-modal-title">Lyric Video Studio</h2>
        <div class="vg-vs-sub">Pick a style, add photos, preview, then render an MP4.</div>
      </div>
      <button class="vagdhenu-modal-close-btn" data-act="close" aria-label="Close">✕</button>
    </div>
    <div class="vg-vs-body">
      <div class="vg-vs-preview">
        <div class="vg-vs-canvas-wrap"><canvas id="vg-vs-canvas"></canvas></div>
        <div class="vg-vs-scrub">
          <button class="vg-vs-play" data-act="play" aria-label="Play preview">▶</button>
          <input type="range" id="vg-vs-time" min="0" max="10" step="0.05" value="0" aria-label="Preview time">
          <span id="vg-vs-timecode" class="vg-vs-timecode">0:00</span>
        </div>
      </div>
      <div class="vg-vs-options">
        <label class="vg-vs-label" for="vg-vs-title">Title shown in the video</label>
        <input id="vg-vs-title" class="vg-studio-input" type="text" placeholder="e.g. श्री गणेश वन्दना">

        <div class="vg-vs-label">Style</div>
        <div class="vg-vs-templates" id="vg-vs-templates"></div>

        <div class="vg-vs-row">
          <div>
            <div class="vg-vs-label">Format</div>
            <div class="vg-vs-seg" data-group="ratio">
              <button data-v="9:16">9:16 Reels</button><button data-v="16:9">16:9 YouTube</button><button data-v="1:1">1:1 Post</button>
            </div>
          </div>
          <div>
            <div class="vg-vs-label">Quality</div>
            <div class="vg-vs-seg" data-group="quality"><button data-v="1080">1080p</button><button data-v="720">720p</button></div>
          </div>
        </div>

        <div class="vg-vs-label">Accent colour</div>
        <div class="vg-vs-swatches" id="vg-vs-accents"></div>

        <div class="vg-vs-label">Verse font</div>
        <div class="vg-vs-fonts" id="vg-vs-fonts"></div>

        <div class="vg-vs-label">Photos <span class="vg-vs-hint">shown in order, evenly across the chant</span></div>
        <div class="vg-vs-photos" id="vg-vs-photos"></div>
        <div class="vg-vs-photo-actions">
          <input type="file" id="vg-vs-file" accept="image/*" multiple hidden>
          <button class="vagdhenu-add-card-btn" data-act="addphotos">📁 Add your photos…</button>
          <span class="vg-vs-presets" id="vg-vs-presets"></span>
        </div>
        <div class="vg-vs-seg vg-vs-fit" data-group="fit">
          <button data-v="cover">Fill frame (crop edges)</button><button data-v="contain">Show whole photo</button>
        </div>

        <div class="vg-vs-label">Effects</div>
        <div class="vg-vs-checks">
          <label><input type="checkbox" data-opt="kenburns"> Slow zoom & pan</label>
          <label><input type="checkbox" data-opt="particles"> Light particles</label>
          <label><input type="checkbox" data-opt="grain"> Film grain</label>
          <label><input type="checkbox" data-opt="fade"> Fade in / out</label>
          <label><input type="checkbox" data-opt="showTitle"> Title</label>
          <label><input type="checkbox" data-opt="showMeter"> Meter</label>
          <label><input type="checkbox" data-opt="showProgress"> Progress</label>
        </div>
      </div>
    </div>
    <div class="vagdhenu-modal-bottom-bar">
      <span class="vg-vs-note">Rendering plays in real time — keep this window open and visible.</span>
      <button class="card-btn" style="width:auto" data-act="close">Cancel</button>
      <button class="vagdhenu-export-btn-primary" data-act="render">🎬 Render MP4</button>
    </div>
  </div>
</div>`);
    document.body.appendChild(m);

    m.addEventListener('click', (e) => {
      if (e.target === m) return closeStudio();
      const b = e.target.closest('[data-act]'); if (!b) return;
      const act = b.dataset.act;
      if (act === 'close') closeStudio();
      else if (act === 'play') togglePlay();
      else if (act === 'addphotos') document.getElementById('vg-vs-file').click();
      else if (act === 'render') renderVideo();
    });
    m.querySelectorAll('.vg-vs-seg').forEach(seg => seg.addEventListener('click', (e) => {
      const b = e.target.closest('button[data-v]'); if (!b) return;
      const g = seg.dataset.group; S.opts[g] = g === 'quality' ? Number(b.dataset.v) : b.dataset.v;
      onOptsChanged();
    }));
    m.querySelectorAll('input[data-opt]').forEach(cb => cb.addEventListener('change', () => { S.opts[cb.dataset.opt] = cb.checked; onOptsChanged(); }));
    document.getElementById('vg-vs-title').addEventListener('input', () => drawPreview());
    document.getElementById('vg-vs-time').addEventListener('input', (e) => { S.previewT = Number(e.target.value); if (S.audio) S.audio.currentTime = S.previewT; drawPreview(); });
    document.getElementById('vg-vs-file').addEventListener('change', async (e) => {
      const files = Array.from(e.target.files || []); e.target.value = '';
      for (const f of files) {
        try {
          const url = await new Promise((res, rej) => { const r = new FileReader(); r.onload = () => res(r.result); r.onerror = rej; r.readAsDataURL(f); });
          const ph = await loadImage(url); ph.name = f.name; S.photos.push(ph);
        } catch (err) { console.warn('[vagdhenu] skipped photo', f.name, err); }
      }
      renderPhotos(); drawPreview();
    });

    const tpl = document.getElementById('vg-vs-templates');
    TEMPLATES.forEach(tp => tpl.appendChild(el(`<button class="vg-vs-tpl" data-tpl="${tp.id}"><canvas width="96" height="170"></canvas><b>${tp.name}</b><span>${tp.desc}</span></button>`)));
    tpl.addEventListener('click', (e) => { const b = e.target.closest('[data-tpl]'); if (b) { S.opts.template = b.dataset.tpl; onOptsChanged(); } });

    const acc = document.getElementById('vg-vs-accents');
    Object.entries(ACCENTS).forEach(([id, a]) => acc.appendChild(el(`<button class="vg-vs-swatch" data-acc="${id}" title="${a.name}" style="--sw-a:${a.a};--sw-b:${a.b}"><i></i>${a.name}</button>`)));
    acc.addEventListener('click', (e) => { const b = e.target.closest('[data-acc]'); if (b) { S.opts.accent = b.dataset.acc; onOptsChanged(); } });

    const fo = document.getElementById('vg-vs-fonts');
    FONTS.forEach(f => fo.appendChild(el(`<button class="vg-vs-font" data-font="${f.id}" style="font-family:${f.css.replace(/"/g, "'")}, serif; font-weight:${f.wb}">वन्दे<small>${f.name}</small></button>`)));
    fo.addEventListener('click', async (e) => { const b = e.target.closest('[data-font]'); if (b) { S.opts.font = b.dataset.font; await ensureFonts(S.opts, sampleText()); onOptsChanged(); } });

    const pr = document.getElementById('vg-vs-presets');
    PRESETS.forEach(p => pr.appendChild(el(`<button class="vg-photo-preset-chip" data-preset="${p.id}">+ ${p.label}</button>`)));
    pr.addEventListener('click', async (e) => {
      const b = e.target.closest('[data-preset]'); if (!b) return;
      const p = PRESETS.find(x => x.id === b.dataset.preset);
      try { const ph = await loadImage(p.src); ph.name = p.label; S.photos.push(ph); renderPhotos(); drawPreview(); }
      catch (err) { alert('Could not load that preset image.'); }
    });

    document.getElementById('vg-vs-photos').addEventListener('click', (e) => {
      const b = e.target.closest('[data-ph]'); if (!b) return;
      const i = Number(b.dataset.i), act = b.dataset.ph, P = S.photos;
      if (act === 'rm') P.splice(i, 1);
      else if (act === 'left' && i > 0) [P[i - 1], P[i]] = [P[i], P[i - 1]];
      else if (act === 'right' && i < P.length - 1) [P[i + 1], P[i]] = [P[i], P[i + 1]];
      renderPhotos(); drawPreview();
    });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && m.style.display !== 'none') closeStudio(); });
  }

  function sampleText() { return S.card && S.card.timestamps ? S.card.timestamps.map(x => x.text).join(' ') : ''; }

  function syncControls() {
    const m = document.getElementById('vg-vs-backdrop'), o = S.opts;
    m.querySelectorAll('.vg-vs-seg').forEach(seg => seg.querySelectorAll('button').forEach(b =>
      b.classList.toggle('active', String(o[seg.dataset.group]) === b.dataset.v)));
    m.querySelectorAll('input[data-opt]').forEach(cb => { cb.checked = !!o[cb.dataset.opt]; });
    m.querySelectorAll('[data-tpl]').forEach(b => b.classList.toggle('active', b.dataset.tpl === o.template));
    m.querySelectorAll('[data-acc]').forEach(b => b.classList.toggle('active', b.dataset.acc === o.accent));
    m.querySelectorAll('[data-font]').forEach(b => b.classList.toggle('active', b.dataset.font === o.font));
    const wrap = m.querySelector('.vg-vs-canvas-wrap'); wrap.dataset.ratio = o.ratio;
  }

  function renderPhotos() {
    const box = document.getElementById('vg-vs-photos');
    if (!S.photos.length) { box.innerHTML = '<div class="vg-vs-empty">No photos — the style\'s own background is used.</div>'; return; }
    box.innerHTML = '';
    S.photos.forEach((ph, i) => {
      const item = el(`<div class="vg-vs-thumb"><span class="vg-vs-n">${i + 1}</span>
        <div class="vg-vs-thumb-btns">
          <button data-ph="left" data-i="${i}" aria-label="Move earlier">◀</button>
          <button data-ph="rm" data-i="${i}" aria-label="Remove">✕</button>
          <button data-ph="right" data-i="${i}" aria-label="Move later">▶</button>
        </div></div>`);
      const c = ph.canvas.cloneNode(false); c.width = 160; c.height = Math.round(160 * ph.h / ph.w);
      c.getContext('2d').drawImage(ph.canvas, 0, 0, c.width, c.height); item.prepend(c);
      box.appendChild(item);
    });
  }

  function previewDims() {
    const [W, H] = DIMS[S.opts.ratio][720];
    const k = S.opts.ratio === '16:9' ? 0.5 : 0.5;
    return [Math.round(W * k), Math.round(H * k)];
  }
  function drawPreview() {
    if (!S.card) return;
    const c = document.getElementById('vg-vs-canvas'); if (!c) return;
    const [W, H] = previewDims();
    if (c.width !== W || c.height !== H) { c.width = W; c.height = H; S.prevState = null; }
    const title = document.getElementById('vg-vs-title').value.trim();
    if (!S.prevState || S.prevState.W !== W || S.prevState.opts !== S.opts || S.prevState.photos !== S.photos || S.prevState._sig !== sig()) {
      S.prevState = buildState(S.card, S.opts, S.photos, W, H, title); S.prevState._sig = sig();
    }
    S.prevState.title = title;
    drawFrame(c.getContext('2d'), S.prevState, S.previewT);
    document.getElementById('vg-vs-timecode').textContent = `${fmtTime(S.previewT)} / ${fmtTime(S.prevState.dur)}`;
  }
  function sig() { return JSON.stringify(S.opts) + S.photos.length + S.photos.map(p => p.w + 'x' + p.h).join(','); }

  function drawThumbs() {  // a tiny still of every style, with the current photos/accent/font
    if (!S.card) return;
    document.querySelectorAll('#vg-vs-templates [data-tpl]').forEach(b => {
      const c = b.querySelector('canvas'); const o = Object.assign({}, S.opts, { template: b.dataset.tpl, grain: false });
      const st = buildState(S.card, o, S.photos, c.width, c.height, '');
      const L = st.lines; const t = L.length ? (L[0].start + L[0].end) / 2 : 1;
      drawFrame(c.getContext('2d'), st, Math.max(1, t));
    });
  }

  function onOptsChanged() { saveOpts(S.opts); syncControls(); S.prevState = null; drawPreview(); drawThumbs(); }

  function togglePlay() {
    const btn = document.querySelector('.vg-vs-play');
    if (S.playing) { S.playing = false; if (S.audio) S.audio.pause(); btn.textContent = '▶'; cancelAnimationFrame(S.raf); return; }
    if (!S.audio) { S.audio = new Audio(S.card.audioSrc); }
    S.audio.currentTime = S.previewT; S.audio.play().catch(() => {});
    S.playing = true; btn.textContent = '❚❚';
    const slider = document.getElementById('vg-vs-time');
    const loop = () => {
      if (!S.playing) return;
      S.previewT = S.audio.currentTime; slider.value = S.previewT; drawPreview();
      if (S.audio.ended) { S.playing = false; btn.textContent = '▶'; return; }
      S.raf = requestAnimationFrame(loop);
    };
    loop();
  }

  function stopPlayback() { S.playing = false; if (S.audio) { S.audio.pause(); } cancelAnimationFrame(S.raf); const b = document.querySelector('.vg-vs-play'); if (b) b.textContent = '▶'; }

  function resolveCard(customCard) {
    let card = customCard;
    if (!card) {
      const idx = window._openModalIdx;
      if (idx != null && window.vagdhenuLibrary && window.vagdhenuLibrary[idx]) card = window.vagdhenuLibrary[idx];
      else card = window.vagdhenuActiveData;
    }
    if (card && !card.audioSrc && window.getVagdhenuMainAudio) {
      const a = window.getVagdhenuMainAudio(); if (a) card.audioSrc = a.currentSrc || a.src;
    }
    return card;
  }

  window.openVideoStudio = async function (customCard) {
    const card = resolveCard(customCard);
    if (!card || !card.audioSrc || !card.timestamps || !card.timestamps.length) {
      alert('Please chant a verse first before opening the video studio 🙏'); return;
    }
    buildModal();
    if (S.card !== card) { S.card = card; S.audio = null; S.prevState = null; }
    const title = document.getElementById('vg-vs-title');
    let t = card.title || card.snippet || ''; if (t.length > 48) t = t.slice(0, 46) + '…';
    title.value = t;
    const slider = document.getElementById('vg-vs-time');
    const dur = Math.max(card.duration || 0, card.timestamps[card.timestamps.length - 1].end);
    slider.max = dur.toFixed(2);
    S.previewT = Math.min(dur, (card.timestamps[0].start + card.timestamps[0].end) / 2 + 0.3);
    slider.value = S.previewT;
    if (!S.photos.length) { try { const ph = await loadImage(PRESETS[0].src); ph.name = PRESETS[0].label; S.photos.push(ph); } catch (e) {} }
    document.getElementById('vg-vs-backdrop').style.display = 'flex';
    await ensureFonts(S.opts, sampleText());
    syncControls(); renderPhotos(); drawPreview(); drawThumbs();
  };
  window.closeVideoStudio = function closeStudio() {
    stopPlayback();
    const m = document.getElementById('vg-vs-backdrop'); if (m) m.style.display = 'none';
  };
  const closeStudio = window.closeVideoStudio;
  window.exportChantVideo = window.openVideoStudio;

  // ── Recording ─────────────────────────────────────────────────────────
  function overlay(html) {
    let ov = document.getElementById('vagdhenu-export-overlay');
    if (!ov) { ov = document.createElement('div'); ov.id = 'vagdhenu-export-overlay'; ov.className = 'vagdhenu-export-overlay'; document.body.appendChild(ov); }
    ov.innerHTML = `<div class="vagdhenu-export-card">${html}</div>`; ov.style.display = 'flex';
    return ov;
  }

  async function renderVideo() {
    const card = S.card; if (!card) return;
    stopPlayback();
    const opts = Object.assign({}, S.opts);
    const [W, H] = DIMS[opts.ratio][opts.quality];
    const title = document.getElementById('vg-vs-title').value.trim();
    document.getElementById('vg-vs-backdrop').style.display = 'none';
    let cancelled = false;
    const ov = overlay(`
      <div class="export-title">Rendering video</div>
      <div class="export-status" id="vg-ex-status">Preparing fonts and photos…</div>
      <div class="vagdhenu-export-progress-track"><div class="vagdhenu-export-progress-fill" id="vg-ex-fill"></div></div>
      <div class="export-time" id="vg-ex-time">0:00 / 0:00</div>
      <div class="export-sub" style="margin-top:10px">Recording runs in real time. Keep this window open and visible.</div>
      <button class="vagdhenu-export-cancel-btn" id="vg-ex-cancel">Cancel</button>`);
    ov.querySelector('#vg-ex-cancel').onclick = () => { cancelled = true; };
    const statusEl = ov.querySelector('#vg-ex-status'), fillEl = ov.querySelector('#vg-ex-fill'), timeEl = ov.querySelector('#vg-ex-time');
    try {
      await ensureFonts(opts, sampleText());
      const st = buildState(card, opts, S.photos, W, H, title);
      const canvas = mkCanvas(W, H), ctx = canvas.getContext('2d', { alpha: false });
      drawFrame(ctx, st, 0);  // warm caches (parchment, mandala, vignette) before the clock starts
      const stream = canvas.captureStream(30);
      let mime = ['video/webm;codecs=vp9', 'video/webm;codecs=vp8', 'video/webm'].find(m => MediaRecorder.isTypeSupported(m)) || '';
      const rec = new MediaRecorder(stream, { mimeType: mime, videoBitsPerSecond: opts.quality === 1080 ? 14e6 : 7e6 });
      const chunks = []; rec.ondataavailable = (e) => { if (e.data.size) chunks.push(e.data); };
      const stopped = new Promise(res => { rec.onstop = res; });
      rec.start(250);
      const t0 = performance.now(), dur = st.dur;
      await new Promise((resolve) => {
        const tick = () => {
          const t = (performance.now() - t0) / 1000;
          if (cancelled) { resolve(); return; }
          drawFrame(ctx, st, Math.min(t, dur));
          const p = clamp(t / dur);
          fillEl.style.width = `${(p * 100).toFixed(1)}%`;
          timeEl.textContent = `${fmtTime(t)} / ${fmtTime(dur)}`;
          statusEl.textContent = `Recording ${opts.ratio} · ${opts.quality}p · ${Math.round(p * 100)}%`;
          if (t >= dur + 0.25) { resolve(); return; }
          next();
        };
        // rAF stops in hidden windows; fall back to a timer so the export always finishes
        const next = () => (document.hidden ? setTimeout(tick, 1000 / 30) : requestAnimationFrame(tick));
        next();
      });
      rec.stop(); await stopped;
      if (cancelled) { ov.style.display = 'none'; return; }

      statusEl.textContent = 'Adding the chant audio and converting to MP4…'; fillEl.style.width = '100%';
      const safe = (title || card.snippet || 'shloka').replace(/[^a-zA-Z0-9ऀ-ॿಀ-೿ఀ-౿]+/g, '_').slice(0, 28) || 'shloka';
      const name = `${safe}_${opts.template}_${opts.ratio.replace(':', 'x')}_${Date.now()}.mp4`;
      const blob = new Blob(chunks, { type: mime || 'video/webm' });
      const q = new URLSearchParams({ filename: name, audio: card.audioSrc || '' });
      const resp = await fetch(`/api/convert_to_mp4?${q}`, { method: 'POST', headers: { 'Content-Type': 'video/webm' }, body: blob });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok || !data.download_url) throw new Error(data.error || `conversion failed (${resp.status})`);

      const portrait = H > W;
      ov.querySelector('.vagdhenu-export-card').style.maxWidth = portrait ? '440px' : '680px';
      ov.querySelector('.vagdhenu-export-card').innerHTML = `
        <div class="export-title">Video ready</div>
        <div class="export-sub">Saved as <strong>${esc(data.filename)}</strong>${data.saved_to ? `<br><span class="vg-vs-path">${esc(data.saved_to)}</span>` : ''}</div>
        <video src="${data.download_url}" controls autoplay loop playsinline class="vg-vs-result ${portrait ? 'portrait' : ''}"></video>
        <div class="vg-vs-result-actions">
          <a href="${data.download_url}" download="${esc(data.filename)}" class="vagdhenu-export-btn-primary" style="text-decoration:none">💾 Download MP4</a>
          <button class="card-btn" style="width:auto" id="vg-ex-again">Make another</button>
          <button class="vagdhenu-export-cancel-btn" style="margin-top:0" id="vg-ex-close">Close</button>
        </div>`;
      ov.querySelector('#vg-ex-close').onclick = () => { ov.style.display = 'none'; };
      ov.querySelector('#vg-ex-again').onclick = () => { ov.style.display = 'none'; document.getElementById('vg-vs-backdrop').style.display = 'flex'; drawPreview(); };
    } catch (err) {
      console.error('[vagdhenu] video export failed', err);
      ov.querySelector('.vagdhenu-export-card').innerHTML = `
        <div class="export-title">Export failed</div><div class="export-sub">${esc(err.message || err)}</div>
        <button class="vagdhenu-export-cancel-btn" onclick="this.closest('.vagdhenu-export-overlay').style.display='none'">Close</button>`;
    }
  }

  // test hook: render one frame of the given style into a canvas (used by the studio thumbnails)
  window.vagdhenuDrawVideoFrame = (canvas, card, opts, t) => {
    const st = buildState(card, Object.assign({}, DEFAULT_OPTS, opts), S.photos, canvas.width, canvas.height, card.title || card.snippet || '');
    drawFrame(canvas.getContext('2d'), st, t);
  };
  console.log('[vagdhenu] Lyric video studio ready.');
})();
