"""Gera o site estático em site/ a partir de data/raw.json (preços) + data/catalogo.json (categorias e textos).
Uso: python scripts/build.py"""
import json, re, shutil, unicodedata
from datetime import date
from html import escape
from pathlib import Path

# ---------- configuração ----------
SITE_NAME = "Rumo ao Topo"
SITE_TAGLINE = "Equipamentos para servir no Legendários"
SITE_URL = "https://rumoaotopo.pages.dev"   # troque pelo domínio final depois do deploy

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site"
ASSETS = ROOT / "assets"

raw = json.loads((ROOT / "data" / "raw.json").read_text(encoding="utf-8"))
cat_cfg = json.loads((ROOT / "data" / "catalogo.json").read_text(encoding="utf-8"))
_checked = max((r.get("checked_at") for r in raw if r.get("checked_at")), default=date.today().isoformat())
PRICE_DATE = "/".join(reversed(_checked.split("-")))

def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def brl(v):
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s.split(",")

def img(pic_id, size="O"):
    # O = original (~500px) · V = 320px · C = 400px · B = 800px
    prefix = "D_NQ_NP" if size == "O" else "D_Q_NP"
    return f"https://http2.mlstatic.com/{prefix}_{pic_id}-{size}.webp"

# ---------- monta o catálogo ----------
old_to_cat = {}
for c in cat_cfg["categorias"]:
    c["produtos"] = []
    for old in c["de_para"]:
        old_to_cat[old.lower()] = c

products, used_slugs = [], set()
for order, r in enumerate(raw):
    if r.get("error") or not r.get("price"):
        print("PULANDO (sem preço):", r["name"])
        continue
    code = r["link"].rstrip("/").split("/")[-1]
    extra = cat_cfg["produtos"].get(code, {})
    cat = old_to_cat.get(r["category"].lower())
    if not cat:
        # categoria nova na planilha: cai em "Outros" até ser mapeada em catalogo.json
        print(f"AVISO: categoria {r['category']!r} sem mapeamento em catalogo.json -> Outros")
        cat = old_to_cat.setdefault("__outros__", {"slug": "outros", "nome": "Outros Equipamentos", "icone": "check",
              "resumo": "Mais equipamentos para trilha e camping.", "de_para": [], "produtos": []})
        if cat not in cat_cfg["categorias"]:
            cat_cfg["categorias"].append(cat)
    title = extra.get("titulo") or r["name"]
    slug = slugify(title)
    while slug in used_slugs:
        slug += "-2"
    used_slugs.add(slug)
    old = r.get("old_price")
    pct = round((1 - r["price"] / old) * 100) if old and old > r["price"] else 0
    p = {
        "order": order, "code": code, "slug": slug, "title": title, "full_name": r["name"],
        "link": r["link"], "price": r["price"], "old_price": old if pct else None, "pct": pct,
        "pix": bool(r.get("discount") and "pix" in r["discount"].lower()),
        "badge": r.get("badge"), "pic": (r.get("thumb") or [None])[0],
        "cat": cat, "sub": cat_cfg["subcategorias"].get(r["category"], r["category"]),
        "desc": extra.get("descricao") or f'{r["name"]}. Confira preço, frete e condições de pagamento no Mercado Livre.', "highlights": extra.get("destaques", []),
    }
    cat["produtos"].append(p)
    products.append(p)

cats = [c for c in cat_cfg["categorias"] if c["produtos"]]

# ---------- ícones (SVG próprios, traço simples) ----------
ICONS = {
    "tent": '<path d="M3 20h18M12 4 3 20M12 4l9 16M12 4v16M9 20l3-6 3 6"/>',
    "moon": '<path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5Z"/>',
    "pack": '<path d="M8 6V5a4 4 0 0 1 8 0v1M6 6h12a1 1 0 0 1 1 1v12a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V7a1 1 0 0 1 1-1ZM9 13h6M9 13v3h6v-3"/>',
    "bolt": '<path d="M9 3h6l-1 6h4l-7 12 1-8H8l1-10Z"/>',
    "boot": '<path d="M5 3h6v8l6 3a3 3 0 0 1 3 3v2H4V4a1 1 0 0 1 1-1ZM4 17h16M11 8h2M11 11h3"/>',
    "shirt": '<path d="m8 3-5 3 2 5 3-1v11h8V10l3 1 2-5-5-3a4 4 0 0 1-8 0Z"/>',
    "battery": '<rect x="6" y="4" width="12" height="17" rx="2"/><path d="M10 2h4M13 8l-3 5h4l-3 5"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    "ext": '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
    "shield": '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6l-8-3Z"/><path d="m9 12 2 2 4-4"/>',
    "card": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18M7 15h4"/>',
    "truck": '<path d="M3 6h11v10H3zM14 10h4l3 3v3h-7M7 19a2 2 0 1 0 0-4 2 2 0 0 0 0 4ZM17 19a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z"/>',
    "check": '<path d="m5 12 5 5 9-10"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
}
def icon(name, cls="ico"):
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>'

LOGO = ('<a class="brand" href="/" aria-label="{0}: início">'
        '<img src="/logo.png" alt="" width="69" height="40">'
        '<span>RUMO AO <b>TOPO</b></span></a>').format(SITE_NAME)

# ---------- componentes ----------
def price_block(p, big=False):
    ints, cents = brl(p["price"])
    old = f'<s class="old">R$ {",".join(brl(p["old_price"]))}</s>' if p["old_price"] else ""
    off = f'<span class="off">{p["pct"]}% OFF{" no Pix" if p["pix"] else ""}</span>' if p["pct"] else ""
    return (f'<div class="price{" price-lg" if big else ""}">{old}'
            f'<div class="now"><span class="cur">R$</span><span class="int">{ints}</span><sup>{cents}</sup>{off}</div>'
            f'<small class="price-note">*Confira o preço original no Mercado Livre</small></div>')

def card(p, lazy=True):
    badge = f'<span class="badge">{escape(p["badge"].title())}</span>' if p.get("badge") else ""
    return f'''<article class="card" data-price="{p["price"]}" data-pct="{p["pct"]}" data-order="{p["order"]}" data-sub="{escape(p["sub"])}" data-name="{escape((p["title"] + " " + p["full_name"] + " " + p["sub"] + " " + p["cat"]["nome"]).lower())}">
  <a class="card-img" href="/produto/{p["slug"]}/">{badge}<img src="{img(p["pic"], "V")}" srcset="{img(p["pic"], "V")} 320w, {img(p["pic"])} 500w" sizes="(max-width:600px) 50vw, 260px" alt="{escape(p["title"])}" width="320" height="320"{' loading="lazy"' if lazy else ''} decoding="async"></a>
  <div class="card-body">
    <span class="card-cat">{escape(p["sub"])}</span>
    <h3><a href="/produto/{p["slug"]}/">{escape(p["title"])}</a></h3>
    {price_block(p)}
    <a class="btn btn-sm" href="{p["link"]}" target="_blank" rel="sponsored nofollow noopener" data-track="{p["code"]}">Ver no Mercado Livre {icon("ext")}</a>
  </div>
</article>'''

def grid(items, lazy_from=4):
    return '<div class="grid">' + "".join(card(p, lazy=i >= lazy_from) for i, p in enumerate(items)) + "</div>"

def toolbar(items, with_search=False):
    subs = sorted({p["sub"] for p in items})
    chips = "" if len(subs) < 2 else ('<div class="chips" role="group" aria-label="Filtrar">'
        '<button class="chip on" data-sub="">Todos</button>'
        + "".join(f'<button class="chip" data-sub="{escape(s)}">{escape(s)}</button>' for s in subs) + "</div>")
    search = ('<label class="find">' + icon("search") +
              '<input type="search" id="q" placeholder="Filtrar produtos…" aria-label="Filtrar produtos"></label>') if with_search else ""
    return f'''<div class="toolbar">{chips}<div class="toolbar-r">{search}<label class="sort">Ordenar
  <select id="sort"><option value="order">Relevância</option><option value="price-asc">Menor preço</option><option value="price-desc">Maior preço</option><option value="pct">Maior desconto</option></select></label>
  <span class="count" id="count">{len(items)} produtos</span></div></div>'''

NAV = "".join(f'<a href="/categoria/{c["slug"]}/">{escape(c["nome"])}</a>' for c in cats)

def page(path, title, desc, body, og_image=None, jsonld=None, active=None):
    canonical = SITE_URL + path
    og = f'<meta property="og:image" content="{og_image}">' if og_image else ""
    ld = "".join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>' for j in (jsonld or []))
    nav = NAV if not active else NAV.replace(f'href="/categoria/{active}/"', f'href="/categoria/{active}/" aria-current="page"')
    html = f'''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
<meta name="description" content="{escape(desc)}">
<link rel="canonical" href="{canonical}">
<meta name="theme-color" content="#0b0b0b">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(desc)}">
<meta property="og:url" content="{canonical}">
{og}
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.png" type="image/png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preconnect" href="https://http2.mlstatic.com">
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/styles.css">
{ld}
</head>
<body>
<div class="topbar">Compra 100% segura pelo <b>Mercado Livre</b> · Pix, cartão e parcelamento · Compra Garantida</div>
<header class="header">
  <div class="wrap header-in">
    {LOGO}
    <form class="search" action="/produtos/" role="search">
      <input type="search" name="q" placeholder="Buscar barraca, saco de dormir, lanterna…" aria-label="Buscar produtos">
      <button aria-label="Buscar">{icon("search")}</button>
    </form>
  </div>
  <nav class="nav" aria-label="Categorias"><div class="wrap nav-in"><a href="/produtos/">Todos</a>{nav}<a class="nav-hl" href="/checklist-legendarios/">Checklist</a></div></nav>
</header>
<main>
{body}
</main>
<footer class="footer">
  <div class="wrap footer-in">
    <div>{LOGO}<p>{SITE_TAGLINE}. Tudo o que você precisa para encarar a trilha, o acampamento e as noites ao ar livre servindo no TOP.</p></div>
    <div><h4>Categorias</h4>{"".join(f'<a href="/categoria/{c["slug"]}/">{escape(c["nome"])}</a>' for c in cats)}</div>
    <div><h4>Guia</h4><a href="/checklist-legendarios/">Checklist para servir</a><a href="/produtos/">Todos os produtos</a></div>
  </div>
  <div class="wrap disclosure">
    <p class="copy">© {date.today().year} {SITE_NAME}</p>
  </div>
</footer>
<script src="/app.js" defer></script>
</body>
</html>'''
    dest = OUT / path.strip("/") / "index.html" if not path.endswith(".html") else OUT / path.strip("/")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html, encoding="utf-8")

def breadcrumbs(items):
    html = '<nav class="crumbs" aria-label="Você está em">' + " <span>/</span> ".join(
        f'<a href="{u}">{escape(n)}</a>' if u else f'<span aria-current="page">{escape(n)}</span>' for n, u in items) + "</nav>"
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, **({"item": SITE_URL + u} if u else {})} for i, (n, u) in enumerate(items)]}
    return html, ld

def section(title, items, more=None, lead=None):
    more_html = f'<a class="more" href="{more}">Ver todos →</a>' if more else ""
    lead_html = f"<p class='lead'>{escape(lead)}</p>" if lead else ""
    return f'<section class="wrap block"><div class="block-hd"><h2>{escape(title)}</h2>{more_html}</div>{lead_html}{grid(items)}</section>'

# ---------- build ----------
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir()
for f in ASSETS.iterdir():
    shutil.copy(f, OUT / f.name)

# Home
kit = next((p for p in products if p["code"] == "1LaRLiq"), products[0])
best = [p for p in products if p.get("badge")][:8]
deals = sorted(products, key=lambda p: -p["pct"])[:8]
tiles = "".join(f'''<a class="tile" href="/categoria/{c["slug"]}/">{icon(c["icone"], "tile-ico")}<span class="tile-n">{escape(c["nome"])}</span><span class="tile-c">{len(c["produtos"])} produtos</span><img src="{img(c["produtos"][0]["pic"], "V")}" alt="" loading="lazy" width="160" height="160"></a>''' for c in cats)
home = f'''
<section class="hero">
  <div class="wrap hero-in">
    <div class="hero-txt">
      <span class="eyebrow">Para quem vai servir no Legendários</span>
      <h1>Preparado para<br><em>chegar ao topo.</em></h1>
      <p>Barracas, sacos de dormir, mochilas, lanternas e tênis de trilha selecionados para quem vai servir no Legendários, com os melhores preços do Mercado Livre.</p>
      <div class="hero-cta"><a class="btn" href="/categoria/acampamento/">Ver barracas e kits</a><a class="btn btn-ghost" href="/checklist-legendarios/">Checklist para servir</a></div>
    </div>
    <a class="hero-card" href="/produto/{kit["slug"]}/">
      <span class="badge">Kit completo</span>
      <img src="{img(kit["pic"])}" alt="{escape(kit["title"])}" width="500" height="500" fetchpriority="high">
      <div><h3>{escape(kit["title"])}</h3>{price_block(kit)}</div>
    </a>
  </div>
  <svg class="hero-mtn" viewBox="0 0 1440 120" preserveAspectRatio="none" aria-hidden="true"><path d="M0 120 L0 90 L180 40 L300 80 L470 10 L620 70 L760 30 L900 85 L1080 20 L1240 75 L1440 35 L1440 120Z"/></svg>
</section>
<section class="trust wrap">
  <div>{icon("shield")}<span><b>Compra Garantida</b>pagamento e entrega pelo Mercado Livre</span></div>
  <div>{icon("card")}<span><b>Pix ou cartão</b>parcelamento direto no Mercado Pago</span></div>
  <div>{icon("truck")}<span><b>Entrega para todo o Brasil</b>frete calculado no Mercado Livre</span></div>
</section>
<section class="wrap block"><div class="block-hd"><h2>Compre por categoria</h2></div><div class="tiles">{tiles}</div></section>
{section("Mais vendidos", best, "/produtos/")}
<section class="wrap promo"><img class="promo-logo" src="/logo-preto.png" alt="" width="160" height="93" loading="lazy"><div><span class="eyebrow">Guia gratuito</span><h2>Vai servir pela primeira vez?</h2><p>Veja o checklist com tudo o que levar para servir no Legendários: do saco de dormir à meia anti-bolha.</p></div><a class="btn" href="/checklist-legendarios/">Abrir checklist</a></section>
{section("Maiores descontos", deals, "/produtos/")}
'''
page("/", f"{SITE_NAME} | Equipamentos para Servir no Legendários",
     "Equipamentos para servir no Legendários: barracas, sacos de dormir, mochilas cargueiras, lanternas de cabeça e tênis de trilha com os melhores preços do Mercado Livre.",
     home, og_image=img(kit["pic"]),
     jsonld=[{"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": SITE_URL,
              "potentialAction": {"@type": "SearchAction", "target": SITE_URL + "/produtos/?q={q}", "query-input": "required name=q"}}])

# Todos os produtos
crumbs, crumbs_ld = breadcrumbs([("Início", "/"), ("Todos os produtos", None)])
page("/produtos/", f"Todos os produtos | {SITE_NAME}",
     "Todos os equipamentos de trilha e camping: barracas, sacos de dormir, isolantes, mochilas, lanternas, bastões, tênis e roupas.",
     f'<section class="wrap block">{crumbs}<h1 class="page-h">Todos os produtos</h1>{toolbar(products, with_search=True)}{grid(products, 8)}<p class="empty" id="empty" hidden>Nenhum produto encontrado. Tente outra palavra.</p></section>',
     jsonld=[crumbs_ld])

# Categorias
for c in cats:
    crumbs, crumbs_ld = breadcrumbs([("Início", "/"), (c["nome"], None)])
    others = "".join(f'<a href="/categoria/{o["slug"]}/">{icon(o["icone"])}{escape(o["nome"])}</a>' for o in cats if o is not c)
    body = f'''<section class="wrap block">{crumbs}
<div class="cat-hd">{icon(c["icone"], "cat-ico")}<div><h1 class="page-h">{escape(c["nome"])}</h1><p class="lead">{escape(c["resumo"])}</p></div></div>
{toolbar(c["produtos"])}{grid(c["produtos"], 8)}</section>
<section class="wrap block"><div class="block-hd"><h2>Outras categorias</h2></div><div class="pills">{others}</div></section>'''
    page(f'/categoria/{c["slug"]}/', f'{c["nome"]} para servir no Legendários | {SITE_NAME}', c["resumo"], body,
         og_image=img(c["produtos"][0]["pic"]), jsonld=[crumbs_ld], active=c["slug"])

# Produtos
for p in products:
    c = p["cat"]
    crumbs, crumbs_ld = breadcrumbs([("Início", "/"), (c["nome"], f'/categoria/{c["slug"]}/'), (p["title"], None)])
    related = [o for o in c["produtos"] if o is not p]
    related = ([o for o in related if o["sub"] == p["sub"]] + [o for o in related if o["sub"] != p["sub"]])[:4]
    if len(related) < 4:
        related += [o for o in products if o["cat"] is not c][: 4 - len(related)]
    hl = "".join(f"<li>{icon('check')}{escape(h)}</li>" for h in p["highlights"])
    badge = f'<span class="badge">{escape(p["badge"].title())}</span>' if p.get("badge") else ""
    save = f'<p class="save">Você economiza R$ {",".join(brl(p["old_price"] - p["price"]))}</p>' if p["old_price"] else ""
    body = f'''<section class="wrap block">{crumbs}
<div class="pdp">
  <div class="pdp-img">{badge}<img src="{img(p["pic"])}" alt="{escape(p["title"])}" width="500" height="500" fetchpriority="high"></div>
  <div class="pdp-info">
    <a class="card-cat" href="/categoria/{c["slug"]}/">{escape(p["sub"])}</a>
    <h1>{escape(p["title"])}</h1>
    <p class="fullname">{escape(p["full_name"])}</p>
    {price_block(p, big=True)}{save}
    <a class="btn btn-lg" href="{p["link"]}" target="_blank" rel="sponsored nofollow noopener" data-track="{p["code"]}">Comprar no Mercado Livre {icon("ext")}</a>
    <ul class="perks"><li>{icon("shield")}Compra Garantida do Mercado Livre</li><li>{icon("card")}Pix, cartão e parcelamento</li><li>{icon("truck")}Frete e prazo calculados no Mercado Livre</li></ul>
  </div>
</div>
<div class="pdp-desc">
  <div><h2>Sobre o produto</h2><p>{escape(p["desc"])}</p></div>
  {f'<div><h2>Destaques</h2><ul class="hl">{hl}</ul></div>' if hl else ''}
</div>
</section>
{section("Você também pode gostar", related)}
<div class="sticky-buy"><div>{price_block(p)}</div><a class="btn" href="{p["link"]}" target="_blank" rel="sponsored nofollow noopener" data-track="{p["code"]}">Comprar no Mercado Livre</a></div>'''
    ld_product = {"@context": "https://schema.org", "@type": "Product", "name": p["title"], "image": [img(p["pic"])],
                  "description": p["desc"] or p["full_name"], "category": c["nome"],
                  "offers": {"@type": "Offer", "price": f'{p["price"]:.2f}', "priceCurrency": "BRL",
                             "availability": "https://schema.org/InStock", "url": SITE_URL + f'/produto/{p["slug"]}/'}}
    page(f'/produto/{p["slug"]}/', f'{p["title"]} | {SITE_NAME}',
         (p["desc"] or p["full_name"])[:155], body, og_image=img(p["pic"]), jsonld=[crumbs_ld, ld_product], active=c["slug"])

# Checklist (conteúdo para SEO)
CHECK = [
    ("Abrigo", "acampamento", ["Barraca (1 ou 2 pessoas)", "Lona para forrar o chão ou fazer toldo"]),
    ("Dormir bem", "dormir", ["Saco de dormir", "Isolante térmico (essencial, o frio vem do chão)", "Travesseiro inflável", "Cobertor ou manta extra para noites frias"]),
    ("Carregar e hidratar", "mochilas", ["Mochila cargueira para levar tudo", "Mochila de ataque para os deslocamentos", "Reservatório de água (hidratação)"]),
    ("Caminhar com segurança", "trilha", ["Lanterna de cabeça (com pilhas ou carregada)", "Bastão de caminhada ou cajado"]),
    ("Bateria", "powerbank", ["Power bank carregado (celular e lanterna)", "Cabo de carregamento compatível"]),
    ("Pés", "calcados", ["Tênis de trilha com solado aderente, já amaciado", "Meias anti-bolha (leve pares extras)", "Tênis aquático para rio e cachoeira"]),
    ("Roupas", "vestuario", ["Camisa com proteção UV", "Roupa térmica ou de compressão", "Poncho ou capa de chuva"]),
]
blocks = ""
for title, slug, items in CHECK:
    c = next(x for x in cats if x["slug"] == slug)
    lis = "".join(f'<li><label><input type="checkbox"> {escape(i)}</label></li>' for i in items)
    blocks += f'''<div class="ck">{icon(c["icone"], "cat-ico")}<div><h2>{escape(title)}</h2><ul>{lis}</ul><a class="more" href="/categoria/{slug}/">Ver opções de {escape(c["nome"].lower())} →</a></div></div>'''
crumbs, crumbs_ld = breadcrumbs([("Início", "/"), ("Checklist para servir no Legendários", None)])
check_body = f'''<section class="wrap block narrow">{crumbs}
<h1 class="page-h">Checklist: o que levar para servir no Legendários</h1>
<p class="lead">Vai servir no Legendários pela primeira vez? São dias de trilha, acampamento e noites ao ar livre, e esquecer um item faz falta. Use esta lista para não deixar nada para trás. Marque os itens conforme separa. Dica: teste barraca, colchão e tênis <b>antes</b> do dia.</p>
<div class="checklist">{blocks}</div>
<div class="tips"><h2>Dicas rápidas</h2><ul>
<li>{icon("check")}Priorize o <b>isolante térmico</b>: sem ele o saco de dormir perde boa parte do efeito.</li>
<li>{icon("check")}Leve <b>peso total da mochila</b> de até ~20% do seu peso corporal.</li>
<li>{icon("check")}Guarde roupas e saco de dormir em sacos plásticos dentro da mochila para protegê-los da chuva.</li>
<li>{icon("check")}Tênis novo? Use por pelo menos uma semana antes para evitar bolhas.</li></ul></div>
</section>
{section("Kits e itens essenciais", ([kit] + [p for p in products if p is not kit and p.get("badge")])[:4])}'''
page("/checklist-legendarios/", f"Checklist: o que levar para servir no Legendários | {SITE_NAME}",
     "Lista completa do que levar para servir no Legendários: barraca, saco de dormir, isolante, lanterna, mochila, tênis e roupas.",
     check_body, og_image=img(kit["pic"]), jsonld=[crumbs_ld])

# 404
page("/404.html", f"Página não encontrada | {SITE_NAME}", "Página não encontrada.",
     f'<section class="wrap block narrow" style="text-align:center"><h1 class="page-h">Trilha errada 🥾</h1><p class="lead">Essa página não existe. Volte para o início ou veja todos os produtos.</p><p><a class="btn" href="/produtos/">Ver produtos</a></p></section>{section("Mais vendidos", best[:4])}')

# sitemap + robots
urls = ["/", "/produtos/", "/checklist-legendarios/"] + [f'/categoria/{c["slug"]}/' for c in cats] + [f'/produto/{p["slug"]}/' for p in products]
today = date.today().isoformat()
(OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    "".join(f"<url><loc>{SITE_URL}{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
(OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")

print(f"OK: {len(products)} produtos em {len(cats)} categorias -> {OUT}")
