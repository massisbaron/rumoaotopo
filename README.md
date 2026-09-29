# Rumo ao Topo: loja de links de afiliado (Mercado Livre)

Site estático (HTML/CSS/JS puro) gerado a partir da planilha de links.

```
data/links.xlsx       planilha: Produto | Categoria | Link afiliado
data/catalogo.json    categorias do site, títulos curtos e descrições de cada produto
data/raw.json         preços/fotos buscados no Mercado Livre (gerado pelo scrape.py)
scripts/scrape.py     busca preço, preço antigo, desconto, selo e foto de cada link
scripts/build.py      gera o site em site/ (SITE_URL e nome da loja no topo do arquivo)
assets/               CSS, JS e favicon
```

## Rodar localmente
```
pip install openpyxl
python scripts/scrape.py      # atualiza preços
python scripts/build.py       # gera site/
python -m http.server 8080 --directory site
```

## Publicar grátis (Cloudflare Pages + GitHub)
1. Crie um repositório no GitHub e suba esta pasta.
2. Em dash.cloudflare.com > Workers & Pages > Create > Pages > Connect to Git, escolha o repositório.
   - Build command: `python scripts/build.py`
   - Build output directory: `site`
3. Depois do primeiro deploy, troque `SITE_URL` em `scripts/build.py` pelo endereço final (ex.: https://rumoaotopo.pages.dev).
4. O workflow `.github/workflows/atualizar-precos.yml` atualiza os preços todo dia às 06:00 e o Cloudflare republica sozinho.

## Adicionar produtos
Edite a planilha, substitua `data/links.xlsx` e suba no GitHub. O robô busca os preços automaticamente.
Categorias novas caem em "Outros" até serem mapeadas em `data/catalogo.json` (campo `de_para`).
Para uma descrição própria, adicione o código do link (ex.: `2SfM6AY` de https://meli.la/2SfM6AY) em `produtos` no catalogo.json.
