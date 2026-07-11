// Autocomplete de categorias reutilizável (edição inline e modal de novo lançamento).
// Lê as opções de <script id="cat-options" type="application/json">.
(function () {
  let opcoes = [];
  try {
    const raw = document.getElementById('cat-options');
    if (raw) opcoes = JSON.parse(raw.textContent);
  } catch (e) { console.error('cat-options inválido', e); }

  const idxSel = new WeakMap();

  function dropdownDe(input) {
    return input.closest('.ac-wrap').querySelector('.ac-dropdown');
  }

  window.acFiltrar = function (input) {
    const busca = input.value.toLowerCase();
    const drop = dropdownDe(input);
    const filtradas = opcoes.filter(o => o.label.toLowerCase().includes(busca));
    idxSel.set(input, -1);
    drop.innerHTML = '';
    filtradas.forEach((o) => {
      const div = document.createElement('div');
      div.className = 'ac-option';
      div.dataset.cat = o.cat;
      div.dataset.sub = o.sub;
      const receita = o.tipo === 'receita';
      div.innerHTML =
        `<span style="width:8px;height:8px;border-radius:2px;background:${receita ? '#059669' : '#8b5cf6'};flex-shrink:0"></span>` +
        `<span>${o.label}</span>`;
      div.addEventListener('mousedown', (ev) => { ev.preventDefault(); acEscolher(input, o); });
      drop.appendChild(div);
    });
    drop.classList.add('visible');
  };

  window.acFechar = function (input) {
    setTimeout(() => dropdownDe(input).classList.remove('visible'), 150);
  };

  function acEscolher(input, o) {
    input.value = o.label;
    dropdownDe(input).classList.remove('visible');
    const ctx = input.dataset.ctx;
    if (ctx === 'row') {
      const id = input.dataset.id;
      htmx.ajax('POST', `/lancamentos/inline-update/${id}`, {
        target: `#row-${id}`, swap: 'outerHTML',
        values: { categoria: o.cat, subcategoria: o.sub }
      });
    } else if (ctx === 'novo') {
      document.getElementById('novo-cat-hidden').value = o.cat;
      document.getElementById('novo-sub-hidden').value = o.sub;
    }
  }

  window.acNav = function (event, input) {
    const drop = dropdownDe(input);
    const opts = drop.querySelectorAll('.ac-option');
    if (!opts.length) return;
    let idx = idxSel.get(input) ?? -1;
    if (event.key === 'ArrowDown') { event.preventDefault(); idx = Math.min(idx + 1, opts.length - 1); }
    else if (event.key === 'ArrowUp') { event.preventDefault(); idx = Math.max(idx - 1, 0); }
    else if (event.key === 'Enter' && idx >= 0) {
      event.preventDefault();
      const el = opts[idx];
      acEscolher(input, { cat: el.dataset.cat, sub: el.dataset.sub, label: el.querySelector('span:last-child').textContent });
      return;
    } else if (event.key === 'Escape') { drop.classList.remove('visible'); return; }
    idxSel.set(input, idx);
    opts.forEach((o, i) => o.classList.toggle('selected', i === idx));
    opts[idx]?.scrollIntoView({ block: 'nearest' });
  };
})();
