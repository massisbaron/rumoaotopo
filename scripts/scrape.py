"""Lê a planilha de links de afiliado e busca preço, preço antigo, desconto, selo e foto no Mercado Livre.
Uso: python scripts/scrape.py [planilha.xlsx]   (padrão: data/links.xlsx)
Gera data/raw.json (usado por build.py). Se um produto falhar, mantém o último preço conhecido."""
import json, sys, time, urllib.request, http.cookiejar
from datetime import date
from pathlib import Path
import openpyxl

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
dec = json.JSONDecoder()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9"})
    with opener.open(req, timeout=30) as r:
        return r.geturl(), r.read().decode("utf-8", "replace")

def decode_after(s, marker, start=0):
    i = s.find(marker, start)
    if i < 0:
        return None
    j = i + len(marker)
    try:
        return dec.raw_decode(s, j)[0]
    except Exception:
        return None

def parse_social(html):
    i = html.find('"id":"card-featured"')
    if i < 0:
        return None
    cards = decode_after(html, '"polycards":', i)
    if not cards:
        return None
    c = cards[0]
    md = c["metadata"]
    out = {"item_id": md["id"], "pdp_url": "https://" + md["url"] + md.get("url_params", "")}
    out["thumb"] = [p["id"] for p in c.get("pictures", {}).get("pictures", [])]
    for comp in c.get("components", []):
        if comp["type"] == "title":
            out["ml_title"] = comp["title"]["text"]
        elif comp["type"] == "price":
            p = comp["price"]
            out["price"] = p.get("current_price", {}).get("value")
            out["old_price"] = (p.get("previous_price") or {}).get("value")
            out["discount"] = (p.get("discount_label") or {}).get("text")
            inst = p.get("installments")
            if inst:
                out["installments_raw"] = inst
        elif comp["type"] == "highlight":
            out["badge"] = comp["highlight"]["text"]
        elif comp["type"] == "shipping":
            out["shipping_raw"] = comp.get("shipping")
        elif comp["type"] == "reviews":
            r = comp.get("reviews", {})
            out["rating"] = r.get("rating_average")
            out["reviews"] = r.get("total")
    return out

def main(xlsx):
    root = Path(__file__).resolve().parent.parent
    wb = openpyxl.load_workbook(xlsx)
    ws = wb.active
    rows = [r for r in ws.iter_rows(min_row=2, values_only=True) if r and r[2]]
    raw_path = root / "data" / "raw.json"
    previous = {}
    if raw_path.exists():
        previous = {r["link"]: r for r in json.loads(raw_path.read_text(encoding="utf-8"))}
    results, failures = [], 0
    for n, (name, cat, link) in enumerate(rows, 1):
        rec = {"name": name.strip(), "category": (cat or "").strip(), "link": link.strip()}
        try:
            final, html = get(rec["link"])
            soc = parse_social(html) if "/social/" in final else None
            if not soc:
                raise RuntimeError("página de afiliado sem produto em destaque: " + final[:80])
            rec.update(soc)
            rec["checked_at"] = date.today().isoformat()
            print(f"[{n}/{len(rows)}] OK  R$ {rec.get('price')}  {rec['name'][:60]}")
        except Exception as e:
            failures += 1
            old = previous.get(rec["link"])
            if old and old.get("price"):
                rec = {**old, "name": rec["name"], "category": rec["category"]}
                print(f"[{n}/{len(rows)}] ERRO {e} -> mantendo preço anterior  {rec['name'][:60]}")
            else:
                rec["error"] = repr(e)
                print(f"[{n}/{len(rows)}] ERRO {e}  {rec['name'][:60]}")
        results.append(rec)
        time.sleep(1.5)
    (root / "data").mkdir(exist_ok=True)
    raw_path.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(rows) - failures}/{len(rows)} produtos atualizados")
    if failures == len(rows):
        sys.exit("Nenhum produto atualizado (bloqueio do Mercado Livre?). Preços anteriores mantidos.")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parent.parent / "data" / "links.xlsx"))
