// Filtros, ordenação e busca das listas de produtos (sem dependências).
(function () {
  const grid = document.querySelector(".toolbar + .grid");
  if (!grid) return;
  const cards = Array.from(grid.children);
  const sortSel = document.getElementById("sort");
  const q = document.getElementById("q");
  const count = document.getElementById("count");
  const empty = document.getElementById("empty");
  let sub = "";

  const norm = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();

  function apply() {
    const terms = q ? norm(q.value).split(/\s+/).filter(Boolean) : [];
    let shown = 0;
    cards.forEach((c) => {
      const name = norm(c.dataset.name);
      const ok = (!sub || c.dataset.sub === sub) && terms.every((t) => name.includes(t));
      c.hidden = !ok;
      if (ok) shown++;
    });
    const key = sortSel ? sortSel.value : "order";
    const val = (c) => key === "pct" ? -+c.dataset.pct
      : key === "price-asc" ? +c.dataset.price
      : key === "price-desc" ? -+c.dataset.price : +c.dataset.order;
    cards.slice().sort((a, b) => val(a) - val(b) || a.dataset.order - b.dataset.order).forEach((c) => grid.appendChild(c));
    if (count) count.textContent = shown + (shown === 1 ? " produto" : " produtos");
    if (empty) empty.hidden = shown > 0;
  }

  document.querySelectorAll(".chip").forEach((b) =>
    b.addEventListener("click", () => {
      document.querySelectorAll(".chip").forEach((x) => x.classList.toggle("on", x === b));
      sub = b.dataset.sub;
      apply();
    })
  );
  if (sortSel) sortSel.addEventListener("change", apply);
  if (q) {
    const params = new URLSearchParams(location.search);
    if (params.get("q")) {
      q.value = params.get("q");
      const top = document.querySelector(".search input");
      if (top) top.value = q.value;
    }
    q.addEventListener("input", apply);
  }
  apply();
})();
