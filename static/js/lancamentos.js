// Estado de filtros/ordenação e ações da tela de Lançamentos.
const filtrosLanc = { origem: 'todos', fonte: 'todos', mes: 'todos', busca: '', ordem: 'data', direcao: 'desc' };

function recarregarTabela() {
  htmx.ajax('GET', '/lancamentos/tabela', {
    target: '#tbody-lancamentos', swap: 'innerHTML', values: filtrosLanc
  });
}

function setFiltroLanc(grupo, valor, btn) {
  filtrosLanc[grupo] = valor;
  const wrap = btn.closest('.filtros');
  wrap.querySelectorAll('.filtro').forEach(b => b.classList.remove('ativo'));
  btn.classList.add('ativo');
  recarregarTabela();
}

let buscaTimer = null;
function onBusca(valor) {
  filtrosLanc.busca = valor;
  clearTimeout(buscaTimer);
  buscaTimer = setTimeout(recarregarTabela, 250);
}

function setOrdemCol(campo) {
  if (filtrosLanc.ordem === campo) {
    filtrosLanc.direcao = filtrosLanc.direcao === 'desc' ? 'asc' : 'desc';
  } else {
    filtrosLanc.ordem = campo;
    filtrosLanc.direcao = 'desc';
  }
  ['data', 'categoria', 'valor'].forEach(c => {
    const el = document.getElementById('ord-' + c);
    if (!el) return;
    if (c === campo) { el.textContent = filtrosLanc.direcao === 'desc' ? '↓' : '↑'; el.style.color = 'var(--azul)'; }
    else { el.textContent = '↕'; el.style.color = 'var(--hint)'; }
  });
  recarregarTabela();
}

// ── Seleção e ações em lote ──
function onSelecao() {
  const marcados = document.querySelectorAll('.row-check:checked');
  const total = document.querySelectorAll('.row-check');
  const n = marcados.length;
  document.getElementById('count-sel').textContent = n;
  document.getElementById('count-conf').textContent = n;
  document.getElementById('btn-excluir-sel').style.display = n > 0 ? '' : 'none';
  document.getElementById('btn-confirmar-sel').style.display = n > 0 ? '' : 'none';
  const selTodos = document.getElementById('sel-todos');
  if (selTodos) { selTodos.indeterminate = n > 0 && n < total.length; selTodos.checked = n === total.length && total.length > 0; }
}

function selecionarTodos(checked) {
  document.querySelectorAll('.row-check').forEach(c => { c.checked = checked; });
  onSelecao();
}

function idsSelecionados() {
  return [...document.querySelectorAll('.row-check:checked')].map(c => c.dataset.id);
}

async function acaoLote(url) {
  const ids = idsSelecionados();
  if (!ids.length) return null;
  const form = new FormData();
  ids.forEach(id => form.append('ids', id));
  const resp = await fetch(url, { method: 'POST', body: form });
  const html = await resp.text();
  document.getElementById('tbody-lancamentos').innerHTML = html;
  if (window.lucide) lucide.createIcons();
  onSelecao();
  const selTodos = document.getElementById('sel-todos');
  if (selTodos) selTodos.checked = false;
}

function confirmarSelecionados() { acaoLote('/lancamentos/batch-confirmar'); }
function excluirSelecionados() {
  if (!confirm(`Excluir ${idsSelecionados().length} lançamento(s)?`)) return;
  acaoLote('/lancamentos/batch-excluir');
}

// ── Modal novo ──
function abrirModalNovo() {
  document.getElementById('novo-data').value = new Date().toISOString().slice(0, 10);
  document.getElementById('form-novo').reset();
  document.getElementById('novo-data').value = new Date().toISOString().slice(0, 10);
  document.getElementById('novo-cat').value = '';
  document.getElementById('novo-cat-hidden').value = 'NAO LEMBRO';
  document.getElementById('novo-sub-hidden').value = '';
  document.getElementById('msg-novo').style.display = 'none';
  document.getElementById('modal-novo').classList.add('open');
}
function fecharModalNovo() { document.getElementById('modal-novo').classList.remove('open'); }

// Fecha o modal quando o lançamento é criado (HX-Trigger do servidor).
document.body.addEventListener('lancamentoCriado', () => {
  fecharModalNovo();
  if (window.lucide) lucide.createIcons();
});
