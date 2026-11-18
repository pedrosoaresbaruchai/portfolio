"""Gravador de demos animadas para o portfólio.

Uso típico (ver exemplos em tools/rec_*.py):

    from rec import Rec
    with Rec("gestores", "http://127.0.0.1:9103", blur_words=["Horizonte Viagens", "Horizonte"]) as r:
        r.goto("/")                       # carrega antes de começar a gravar "de verdade"
        r.start()                         # marca o início do trecho que vai para o vídeo
        r.caption("Ranking de consultores em tempo real")
        r.click("#aba-unidades")          # cursor anda suavemente e clica
        r.pause(2.5)
        r.scroll(600)
    # -> docs/vid/gestores.mp4 + docs/vid/gestores.jpg (poster)

Regras do portfólio: tema escuro, marca borrada (blur_words / blur_css), dados fictícios.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

FF = imageio_ffmpeg.get_ffmpeg_exe()
OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "vid"

INIT_JS = r"""
(() => {
  const CFG = __CFG__;
  const css = `
  #pf-cursor{position:fixed;left:0;top:0;width:26px;height:26px;z-index:2147483647;pointer-events:none;
    transform:translate(-3px,-2px);transition:opacity .2s;filter:drop-shadow(0 2px 4px rgba(0,0,0,.6))}
  .pf-ring{position:fixed;z-index:2147483646;pointer-events:none;width:14px;height:14px;margin:-7px 0 0 -7px;
    border-radius:50%;border:3px solid #60a5fa;background:rgba(96,165,250,.25);animation:pfr .55s ease-out forwards}
  @keyframes pfr{to{transform:scale(3.4);opacity:0}}
  #pf-cap{position:fixed;left:50%;bottom:34px;transform:translateX(-50%) translateY(16px);z-index:2147483645;
    pointer-events:none;opacity:0;transition:all .45s ease;font:600 19px/1.3 Inter,Segoe UI,system-ui,sans-serif;
    color:#fff;background:rgba(10,14,28,.88);border:1px solid rgba(148,163,184,.35);padding:12px 22px;border-radius:999px;
    box-shadow:0 10px 30px rgba(0,0,0,.45);white-space:nowrap;backdrop-filter:blur(6px)}
  #pf-cap.on{opacity:1;transform:translateX(-50%) translateY(0)}
  #pf-cap b{color:#60a5fa}
  .pf-blur{filter:blur(7px)!important;user-select:none}
  .dash-debug-menu__outer,.dash-debug-menu,.dash-debug-alert,.dash-fe-error-top{display:none!important}
  ${CFG.blur_css ? CFG.blur_css + '{filter:blur(7px)!important}' : ''}
  ${CFG.extra_css || ''}`;
  const words = (CFG.blur_words || []).filter(Boolean);
  const rx = words.length ? new RegExp('(' + words.map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|') + ')', 'i') : null;
  function blurText(root) {
    if (!rx || !root) return;
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const hits = []; let n;
    while ((n = w.nextNode())) {
      const p = n.parentElement;
      if (p && !p.closest('.pf-blur,script,style,#pf-cap') && rx.test(n.nodeValue)) hits.push(n);
    }
    for (const t of hits) {
      const parts = t.nodeValue.split(rx); const f = document.createDocumentFragment();
      for (const s of parts) {
        if (!s) continue;
        if (rx.test(s) && words.some(x => x.toLowerCase() === s.toLowerCase())) {
          const sp = document.createElement('span'); sp.className = 'pf-blur'; sp.textContent = s; f.appendChild(sp);
        } else f.appendChild(document.createTextNode(s));
      }
      t.parentNode && t.parentNode.replaceChild(f, t);
    }
    document.querySelectorAll('input,textarea').forEach(el => { if (rx.test(el.value||'')) el.classList.add('pf-blur'); });
  }
  function boot() {
    if (document.getElementById('pf-style')) return;
    const st = document.createElement('style'); st.id = 'pf-style'; st.textContent = css; document.head.appendChild(st);
    const c = document.createElement('div'); c.id = 'pf-cursor';
    c.innerHTML = '<svg viewBox="0 0 24 24" width="26" height="26"><path d="M4 2l15 11.2-6.6 1.1 3.9 7.4-3 1.5-3.8-7.5L4 20z" fill="#fff" stroke="#111" stroke-width="1.4" stroke-linejoin="round"/></svg>';
    const pos = window.__pfPos || {x: -50, y: -50};
    c.style.left = pos.x + 'px'; c.style.top = pos.y + 'px';
    document.body.appendChild(c);
    const cap = document.createElement('div'); cap.id = 'pf-cap'; document.body.appendChild(cap);
    blurText(document.body);
    new MutationObserver(ms => { for (const m of ms) { if (m.type === 'characterData') blurText(m.target.parentElement); else m.addedNodes.forEach(x => blurText(x.nodeType === 1 ? x : x.parentElement)); } })
      .observe(document.body, {childList: true, subtree: true, characterData: true});
    if (CFG.title) document.title = CFG.title;
  }
  document.addEventListener('mousemove', e => {
    window.__pfPos = {x: e.clientX, y: e.clientY};
    const c = document.getElementById('pf-cursor'); if (c) { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px'; }
  }, true);
  document.addEventListener('mousedown', e => {
    const r = document.createElement('div'); r.className = 'pf-ring'; r.style.left = e.clientX + 'px'; r.style.top = e.clientY + 'px';
    document.body.appendChild(r); setTimeout(() => r.remove(), 700);
  }, true);
  window.__pfCaption = (html) => { const c = document.getElementById('pf-cap'); if (!c) return;
    if (!html) { c.classList.remove('on'); return; } c.innerHTML = html; c.classList.add('on'); };
  window.__pfBlur = () => blurText(document.body);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
"""


class Rec:
    def __init__(self, slug: str, base: str, *, blur_words=(), blur_css: str = "", extra_css: str = "",
                 title: str = "", width: int = 1440, height: int = 900, out_width: int = 1280,
                 crf: int = 27, headless: bool = True):
        self.slug, self.base = slug, base.rstrip("/")
        self.w, self.h, self.out_width, self.crf = width, height, out_width, crf
        cfg = {"blur_words": list(blur_words), "blur_css": blur_css, "extra_css": extra_css, "title": title}
        self.init_js = INIT_JS.replace("__CFG__", json.dumps(cfg))
        self.headless = headless
        self.t0 = None
        self.cx, self.cy = width * 0.55, height * 0.45
        self.errors: list[str] = []

    # ---------- ciclo de vida ----------
    def __enter__(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="pfrec_"))
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch(headless=self.headless)
        self.ctx = self.browser.new_context(
            viewport={"width": self.w, "height": self.h}, device_scale_factor=1, color_scheme="dark",
            record_video_dir=str(self.tmp), record_video_size={"width": self.w, "height": self.h})
        self.ctx.add_init_script(self.init_js)
        self.page = self.ctx.new_page()
        self.t_page = time.monotonic()
        self.page.on("console", lambda m: self.errors.append(m.text) if m.type == "error" else None)
        self.page.on("pageerror", lambda e: self.errors.append(str(e)))
        return self

    def __exit__(self, et, ev, tb):
        t_end = time.monotonic()
        vpath = self.page.video.path()
        self.ctx.close()
        self.browser.close()
        self.pw.stop()
        if et is None:
            src = Path(vpath)
            start = (self.t0 or self.t_page) - self.t_page
            dur = t_end - (self.t0 or self.t_page)
            self._encode(src, start, dur)
        shutil.rmtree(self.tmp, ignore_errors=True)
        if self.errors:
            print("[console errors]", self.errors[:8])
        return False

    def _encode(self, src: Path, start: float, dur: float):
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        mp4 = OUT_DIR / f"{self.slug}.mp4"
        jpg = OUT_DIR / f"{self.slug}.jpg"
        vf = f"scale={self.out_width}:-2:flags=lanczos,fps=25"
        subprocess.run([FF, "-y", "-loglevel", "error", "-ss", f"{start:.2f}", "-i", str(src), "-t", f"{dur:.2f}",
                        "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", str(self.crf),
                        "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", str(mp4)], check=True)
        subprocess.run([FF, "-y", "-loglevel", "error", "-ss", "0.3", "-i", str(mp4), "-frames:v", "1",
                        "-q:v", "3", str(jpg)], check=True)
        print(f"OK {mp4.name}: {dur:.1f}s, {mp4.stat().st_size/1e6:.2f} MB")

    # ---------- ações ----------
    def goto(self, path: str = "/", wait: float = 3.0):
        self.page.goto(self.base + path, wait_until="networkidle")
        self.pause(wait)

    def start(self):
        """Marca o início do vídeo (tudo antes é cortado)."""
        self.page.evaluate("window.__pfBlur && window.__pfBlur()")
        self.page.mouse.move(self.cx, self.cy)
        self.pause(0.3)
        self.t0 = time.monotonic()

    def pause(self, s: float):
        self.page.wait_for_timeout(int(s * 1000))

    def caption(self, text: str | None, hold: float = 0):
        self.page.evaluate("t => window.__pfCaption && window.__pfCaption(t)", text or "")
        if hold:
            self.pause(hold)

    def move_to(self, x: float, y: float, dur: float = 0.7):
        steps = max(8, int(dur * 40))
        self.page.mouse.move(x, y, steps=steps)
        self.cx, self.cy = x, y

    def _center(self, target):
        loc = self.page.locator(target).first if isinstance(target, str) else target
        loc.scroll_into_view_if_needed(timeout=10000)
        b = loc.bounding_box()
        if not b:
            raise RuntimeError(f"elemento sem caixa: {target}")
        return b["x"] + b["width"] / 2, b["y"] + b["height"] / 2

    def hover(self, target, dur: float = 0.7, after: float = 0.6):
        x, y = self._center(target)
        self.move_to(x, y, dur)
        self.pause(after)

    def click(self, target, dur: float = 0.7, after: float = 1.2, wait_idle: bool = True):
        x, y = self._center(target)
        self.move_to(x, y, dur)
        self.pause(0.15)
        self.page.mouse.down(); self.pause(0.08); self.page.mouse.up()
        if wait_idle:
            try:
                self.page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass
        self.pause(after)

    def click_xy(self, x: float, y: float, dur: float = 0.7, after: float = 1.2):
        self.move_to(x, y, dur)
        self.pause(0.15)
        self.page.mouse.down(); self.pause(0.08); self.page.mouse.up()
        self.pause(after)

    def type(self, text: str, delay: float = 0.06, after: float = 0.6):
        self.page.keyboard.type(text, delay=int(delay * 1000))
        self.pause(after)

    def key(self, k: str, after: float = 0.8):
        self.page.keyboard.press(k)
        self.pause(after)

    def scroll(self, dy: int, dur: float = 1.2, after: float = 0.8):
        """Rolagem suave com a roda do mouse (funciona em páginas e em contêineres sob o cursor)."""
        n = max(6, int(dur * 30))
        for _ in range(n):
            self.page.mouse.wheel(0, dy / n)
            self.page.wait_for_timeout(int(dur * 1000 / n))
        self.pause(after)

    def scroll_el(self, selector: str, top: int, dur: float = 1.2, after: float = 0.8):
        """Rolagem suave de um contêiner específico (ex.: .main com overflow)."""
        self.page.evaluate("""([sel, top, ms]) => { const el = document.querySelector(sel) || document.scrollingElement;
            const s = el.scrollTop, d = top - s, t0 = performance.now();
            (function f(t){ const k = Math.min(1,(t-t0)/ms); const e = k<.5?2*k*k:1-Math.pow(-2*k+2,2)/2;
              el.scrollTop = s + d*e; if (k<1) requestAnimationFrame(f); })(t0); }""", [selector, top, int(dur * 1000)])
        self.pause(dur + after)
