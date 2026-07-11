// Interações da tela de Categorias: expandir/recolher e renomear via prompt.
function toggleCat(id) {
  const el = document.getElementById('subs-' + id);
  if (el) el.style.display = el.style.display === 'none' ? 'block' : 'none';
}

function renomearCat(id, atual) {
  const nome = prompt('Novo nome da categoria:', atual);
  if (nome && nome.trim() && nome.trim() !== atual) {
    htmx.ajax('POST', `/categorias/${id}/renomear`, {
      target: '#cat-lista', swap: 'outerHTML', values: { nome: nome.trim() }
    });
  }
}

function renomearSub(id, atual) {
  const nome = prompt('Novo nome da subcategoria:', atual);
  if (nome && nome.trim() && nome.trim() !== atual) {
    htmx.ajax('POST', `/subcategorias/${id}/renomear`, {
      target: '#cat-lista', swap: 'outerHTML', values: { nome: nome.trim() }
    });
  }
}
