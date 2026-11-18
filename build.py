"""Gera docs/index.html a partir de config.json e docs/img/<slug>/meta.json.

Uso:  python build.py
"""
import html
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
SITE = ROOT / "docs"
cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

projetos = []
for slug in cfg["ordem"]:
    meta_path = SITE / "img" / slug / "meta.json"
    if not meta_path.exists():
        print(f"[aviso] sem meta.json: {slug}")
        continue
    m = json.loads(meta_path.read_text(encoding="utf-8"))
    m["slug"] = slug
    m["telas"] = [t for t in m.get("telas", []) if (SITE / "img" / slug / t["arquivo"]).exists()]
    if m["telas"]:
        projetos.append(m)

e = html.escape


def img_src(slug, arq):
    return f"img/{slug}/{quote(arq)}"


def card(p, i):
    slug = p["slug"]
    telas = p["telas"]
    principal = telas[0]
    thumbs = "".join(
        f'<button class="thumb" data-full="{img_src(slug, t["arquivo"])}" data-cap="{e(t.get("legenda", ""))}" '
        f'aria-label="Ampliar: {e(t.get("legenda", ""))}"><img loading="lazy" src="{img_src(slug, t["arquivo"])}" alt="{e(t.get("legenda", ""))}"></button>'
        for t in telas
    )
    feats = "".join(f"<li>{e(f)}</li>" for f in p.get("funcionalidades", []))
    stack = "".join(f'<span class="chip">{e(s)}</span>' for s in p.get("stack", []))
    lado = "rev" if i % 2 else ""
    return f"""
<section class="proj {lado}" id="{slug}" data-cat="{e(p.get('categoria', ''))}">
  <div class="shot">
    <button class="main-shot" data-full="{img_src(slug, principal['arquivo'])}" data-cap="{e(principal.get('legenda', ''))}" aria-label="Ampliar imagem">
      <div class="browser"><span></span><span></span><span></span></div>
      <img loading="lazy" src="{img_src(slug, principal['arquivo'])}" alt="{e(principal.get('legenda', ''))}">
    </button>
    <div class="thumbs">{thumbs}</div>
  </div>
  <div class="info">
    <span class="cat">{e(p.get('categoria', ''))}</span>
    <h2>{e(p['titulo'])}</h2>
    <p class="resumo">{e(p.get('resumo', ''))}</p>
    <h3>O problema</h3>
    <p>{e(p.get('problema', ''))}</p>
    <h3>O que entrega</h3>
    <ul class="feats">{feats}</ul>
    <div class="stack">{stack}</div>
  </div>
</section>"""


cats = sorted({p.get("categoria", "") for p in projetos if p.get("categoria")} | ({"Automação"} if (ROOT / "automacoes.json").exists() else set()))
filtros = '<button class="f on" data-f="*">Todos</button>' + "".join(
    f'<button class="f" data-f="{e(c)}">{e(c)}</button>' for c in cats
)

WA_ICON = ('<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="currentColor"><path d="M17.47 14.38c-.3-.15-1.76-.87-2.03-.97-.27-.1-.47-.15-.67.15-.2.3-.77.97-.94 1.17-.17.2-.35.22-.65.07-.3-.15-1.26-.46-2.4-1.48-.89-.79-1.49-1.77-1.66-2.07-.17-.3-.02-.46.13-.61.13-.13.3-.35.45-.52.15-.17.2-.3.3-.5.1-.2.05-.37-.02-.52-.08-.15-.67-1.62-.92-2.22-.24-.58-.49-.5-.67-.51h-.57c-.2 0-.52.07-.79.37-.27.3-1.04 1.02-1.04 2.48 0 1.46 1.07 2.88 1.21 3.08.15.2 2.1 3.2 5.08 4.49.71.31 1.26.49 1.69.63.71.23 1.36.2 1.87.12.57-.08 1.76-.72 2.01-1.42.25-.7.25-1.29.17-1.42-.07-.12-.27-.2-.57-.35M12.05 21.5h-.01a9.4 9.4 0 0 1-4.8-1.31l-.34-.2-3.56.93.95-3.47-.22-.36a9.4 9.4 0 0 1-1.44-5.01c0-5.2 4.23-9.43 9.44-9.43 2.52 0 4.89.98 6.67 2.77a9.37 9.37 0 0 1 2.76 6.67c0 5.2-4.24 9.43-9.45 9.43M20.07 3.92A11.3 11.3 0 0 0 12.05.6C5.79.6.7 5.69.7 11.95c0 2 .52 3.95 1.52 5.67L.6 23.4l5.92-1.55a11.3 11.3 0 0 0 5.43 1.38h.01c6.25 0 11.35-5.09 11.35-11.35 0-3.03-1.18-5.88-3.32-8.02"/></svg>')
wa_url = ""
if cfg.get("whatsapp"):
    num = "".join(ch for ch in cfg["whatsapp"] if ch.isdigit())
    msg = quote(cfg.get("whatsapp_msg", "Olá, Pedro! Vi seu portfólio e quero saber mais sobre dashboards e sistemas para a minha empresa."))
    wa_url = f"https://wa.me/{num}?text={msg}"

contatos = []
if wa_url:
    contatos.append(f'<a class="btn wa" href="{wa_url}" target="_blank" rel="noopener">{WA_ICON}Chamar no WhatsApp</a>')
if cfg.get("email"):
    contatos.append(f'<a class="btn ghost" href="mailto:{e(cfg["email"])}">{e(cfg["email"])}</a>')
if cfg.get("linkedin"):
    contatos.append(f'<a class="btn ghost" href="{e(cfg["linkedin"])}" target="_blank" rel="noopener">LinkedIn</a>')
contato_html = "".join(contatos) or '<span class="muted">Entre em contato para uma demonstração.</span>'

# ---------- Automações ----------
import re

ICONS = {
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "db": '<ellipse cx="12" cy="5.5" rx="7" ry="2.5"/><path d="M5 5.5v13c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5v-13"/><path d="M5 12c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5"/>',
    "filter": '<path d="M4 5h16l-6 7.5V19l-4 1.5v-8L4 5z"/>',
    "code": '<path d="M9 8l-4 4 4 4M15 8l4 4-4 4"/>',
    "whatsapp": '<path d="M4 20l1.3-3.9A8 8 0 1 1 8 19l-4 1z"/><path d="M9.5 9.5c.3 1.8 2.2 3.8 4.5 4.5l1-1 1.5.7c-.3 1-1.1 1.6-2 1.6-3.4-.3-6-2.9-6.3-6.3 0-.9.6-1.7 1.6-2l.7 1.5-1 1z"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3.5 6l8.5 7 8.5-7"/>',
    "webhook": '<circle cx="12" cy="6" r="2.5"/><circle cx="6" cy="17" r="2.5"/><circle cx="18" cy="17" r="2.5"/><path d="M11 8.5L7.2 15M13 8.5l3.8 6.5M8.5 17h7"/>',
    "branch": '<circle cx="6" cy="6" r="2.2"/><circle cx="6" cy="18" r="2.2"/><circle cx="18" cy="9" r="2.2"/><path d="M6 8.2v7.6M6 12c0-2 2-3 5-3h4.8"/>',
    "wait": '<path d="M7 3h10M7 21h10M8 3c0 5 8 5 8 9s-8 4-8 9M16 3c0 5-8 5-8 9"/>',
    "api": '<rect x="4" y="4" width="16" height="16" rx="3"/><path d="M8 10h8M8 14h5"/>',
}
NODE_COR = {"clock": "#f59e0b", "db": "#3b82f6", "filter": "#8b5cf6", "code": "#64748b",
            "whatsapp": "#22c55e", "mail": "#ef4444", "webhook": "#ec4899", "branch": "#14b8a6",
            "wait": "#f97316", "api": "#0ea5e9"}


MARCA = '<span class="blur" aria-label="nome da empresa ocultado">Sua Empresa</span>'


def marca(t):
    """Escapa o texto e troca {{marca}} pelo nome borrado."""
    return e(t).replace("{{marca}}", MARCA)


def fmt_msg(t):
    t = marca(t)
    t = re.sub(r"\*(.+?)\*", r"<b>\1</b>", t)
    return t.replace("\n", "<br>")


def svg_icon(tipo):
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS.get(tipo, ICONS["code"])}</svg>')


def fluxo_html(nodes):
    out = []
    for i, n in enumerate(nodes):
        if i:
            out.append('<span class="edge" aria-hidden="true"></span>')
        out.append(
            f'<div class="node"><div class="ico" style="--c:{NODE_COR.get(n["tipo"], "#64748b")}">{svg_icon(n["tipo"])}</div>'
            f'<b>{e(n["nome"])}</b><small>{e(n.get("det", ""))}</small></div>')
    return f'<div class="flow"><div class="flow-bar"><span class="n8n">n8n</span> workflow</div><div class="flow-nodes">{"".join(out)}</div></div>'


def mockup_html(m):
    if m["tipo"] == "whatsapp":
        def bolha(b):
            eu = b.get("eu")
            nome = "" if eu else f'<span class="nm">{e(b["de"])}</span>'
            check = " ✓✓" if eu else ""
            return (f'<div class="bub {"out" if eu else "in"}">{nome}{fmt_msg(b["txt"])}'
                    f'<span class="tm">{e(b["hora"])}{check}</span></div>')
        bolhas = "".join(bolha(b) for b in m["msgs"])
        return (f'<div class="wa-phone"><div class="wa-head"><div class="av">{e(m["chat"][0])}</div>'
                f'<div><b>{e(m["chat"])}</b><small>{e(m.get("sub", ""))}</small></div></div>'
                f'<div class="wa-body">{bolhas}</div></div>')
    return (f'<div class="mail"><div class="mail-head"><div><span>De</span>{marca(m["de"])}</div>'
            f'<div><span>Para</span>{e(m["para"])}</div><h4>{e(m["assunto"])}</h4></div>'
            f'<div class="mail-body"><div class="mail-logo">◆ {MARCA}</div><p>{fmt_msg(m["corpo"])}</p>'
            f'<span class="mail-btn">{e(m.get("botao", ""))}</span></div></div>')


auto_html = ""
auto_path = ROOT / "automacoes.json"
if auto_path.exists():
    A = json.loads(auto_path.read_text(encoding="utf-8"))
    blocos = []
    for it in A["itens"]:
        bens = "".join(f"<li>{e(b)}</li>" for b in it.get("beneficios", []))
        blocos.append(f"""
  <article class="auto" id="auto-{e(it['id'])}">
    <div class="auto-txt">
      <h3>{e(it['titulo'])}</h3>
      <p>{e(it['resumo'])}</p>
      <ul class="feats">{bens}</ul>
    </div>
    <div class="auto-mock">{mockup_html(it['mockup'])}</div>
    {fluxo_html(it['fluxo'])}
  </article>""")
    stack_a = "".join(f'<span class="chip">{e(s)}</span>' for s in A.get("stack", []))
    auto_html = f"""
<section class="autos" id="automacoes" data-cat="Automação">
  <div class="autos-head">
    <span class="cat">Automação</span>
    <h2>{e(A['titulo'])}</h2>
    <p>{e(A['subtitulo'])}</p>
    <div class="stack center">{stack_a}</div>
  </div>
  {''.join(blocos)}
  <p class="note center">Exemplos com dados fictícios. Os fluxos são adaptados aos sistemas e à rotina de cada empresa.</p>
</section>"""

nav = '<a href="#sobre">Sobre</a><a href="#projetos">Projetos</a>'
if auto_html:
    nav += '<a href="#automacoes">Automações</a>'
nav += '<a href="#contato">Contato</a>'
cards = "".join(card(p, i) for i, p in enumerate(projetos))

# ---------- Hero ----------
CHECK_X = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M8.5 8.5l7 7M15.5 8.5l-7 7"/></svg>'
dores = "".join(f"<li>{CHECK_X}<span>{e(d)}</span></li>" for d in cfg.get("dores", []))
hero_imgs = [(s, a) for s, a in cfg.get("hero_imgs", []) if (SITE / "img" / s / a).exists()]
mosaico = "".join(
    f'<div class="hm hm{i}"><div class="browser"><span></span><span></span><span></span></div>'
    f'<img src="{img_src(s, a)}" alt="" loading="{"eager" if i == 0 else "lazy"}"></div>'
    for i, (s, a) in enumerate(hero_imgs[:3]))
cta1 = (f'<a class="btn wa lg" href="{wa_url}" target="_blank" rel="noopener">{WA_ICON}{e(cfg.get("cta_principal", "Fale comigo"))}</a>'
        if wa_url else f'<a class="btn lg" href="#contato">{e(cfg.get("cta_principal", "Fale comigo"))}</a>')
hero_html = f"""
<section class="hero">
  <div class="hero-in">
    <div class="hero-txt">
      <p class="eyebrow">{e(cfg.get('eyebrow', ''))}</p>
      <h1>{e(cfg['titulo'])} <span class="grad">{e(cfg.get('titulo_destaque', ''))}</span></h1>
      <p class="sub">{e(cfg['subtitulo'])}</p>
      <div class="hero-btns">{cta1}<a class="btn ghost lg" href="#projetos">{e(cfg.get('cta_secundario', 'Ver projetos'))}</a></div>
    </div>
    <div class="hero-vis" aria-hidden="true">{mosaico}</div>
  </div>
  <div class="dores">
    <h2>{e(cfg.get('dores_titulo', ''))}</h2>
    <ul>{dores}</ul>
    <p class="dores-sol">Se você marcou pelo menos um item, dá para resolver — e mais rápido do que você imagina. <a href="#projetos">Veja como ↓</a></p>
  </div>
</section>"""

# ---------- Sobre ----------
sobre_html = ""
S = cfg.get("sobre")
if S:
    foto = S.get("foto")
    avatar = (f'<img src="{e(foto)}" alt="{e(cfg["nome"])}">' if foto and (SITE / foto).exists()
              else f'<span>{e("".join(p[0] for p in cfg["nome"].split()[:2]))}</span>')
    pilares = "".join(f'<div class="pilar"><b>{e(p["titulo"])}</b><p>{e(p["texto"])}</p></div>' for p in S.get("pilares", []))
    etapas = "".join(f'<li><i>{i + 1}</i><b>{e(t["titulo"])}</b><p>{e(t["texto"])}</p></li>' for i, t in enumerate(cfg.get("etapas", [])))
    textos = "".join(f"<p>{e(t)}</p>" for t in S.get("texto", []))
    sobre_html = f"""
<section class="sobre" id="sobre">
  <div class="sobre-in">
    <div class="avatar">{avatar}</div>
    <div class="sobre-txt">
      <span class="cat">Sobre mim</span>
      <h2>{e(S['titulo'])}</h2>
      {textos}
    </div>
  </div>
  <div class="pilares">{pilares}</div>
  <div class="etapas-box">
    <h3>Como trabalhamos juntos</h3>
    <ol class="etapas">{etapas}</ol>
  </div>
</section>"""

page = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(cfg['nome'])} · Portfólio</title>
<meta name="description" content="{e(cfg['subtitulo'])}">
<meta property="og:title" content="{e(cfg['nome'])} · Portfólio">
<meta property="og:description" content="{e(cfg['subtitulo'])}">
{f'<meta property="og:image" content="{img_src(projetos[0]["slug"], projetos[0]["telas"][0]["arquivo"])}">' if projetos else ''}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="top">
  <a class="brand" href="#">{e(cfg['nome'])}</a>
  <nav>{nav}</nav>
  {f'<a class="btn sm wa" href="{wa_url}" target="_blank" rel="noopener">{WA_ICON}WhatsApp</a>' if wa_url else '<a class="btn sm" href="#contato">Contato</a>'}
</header>

{hero_html}
{sobre_html}

<div class="sec-head" id="projetos">
  <span class="cat">Projetos</span>
  <h2>Ferramentas que já rodam no dia a dia de empresas reais</h2>
  <p class="note">Telas com dados fictícios e nome da empresa ocultado para preservar o sigilo dos clientes.</p>
</div>

<div class="filters">{filtros}</div>

<main>{cards}</main>
{auto_html}

<section class="cta" id="contato">
  <h2>Quer um painel assim para a sua empresa?</h2>
  <p>Conto como levantamos os dados, quanto tempo leva e mostro uma demonstração ao vivo.</p>
  <div class="cta-btns">{contato_html}</div>
</section>

<footer>© {e(cfg['nome'])}</footer>

{f'<a class="wa-float" href="{wa_url}" target="_blank" rel="noopener" aria-label="Conversar no WhatsApp">{WA_ICON}</a>' if wa_url else ''}

<div class="lb" id="lb" hidden>
  <button class="lb-x" aria-label="Fechar">×</button>
  <figure><img alt=""><figcaption></figcaption></figure>
</div>
<script src="app.js"></script>
</body>
</html>
"""
(SITE / "index.html").write_text(page, encoding="utf-8")
(SITE / ".nojekyll").write_text("", encoding="utf-8")
print(f"OK: {len(projetos)} projetos, {sum(len(p["telas"]) for p in projetos)} telas -> docs/index.html")
