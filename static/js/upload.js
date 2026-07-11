// Upload de faturas (.csv) e extratos (.ofx): drag & drop + POST para a API.
let arquivosSelecionados = [];

const drop = document.getElementById('drop');
const inputArquivo = document.getElementById('arquivo');

drop.addEventListener('dragover', e => { e.preventDefault(); drop.classList.add('over'); });
drop.addEventListener('dragleave', () => drop.classList.remove('over'));
drop.addEventListener('drop', e => {
  e.preventDefault();
  drop.classList.remove('over');
  arquivosSelecionados = [...e.dataTransfer.files].filter(f =>
    f.name.toLowerCase().endsWith('.csv') || f.name.toLowerCase().endsWith('.ofx'));
  atualizarNomeArquivo();
});
inputArquivo.addEventListener('change', function () {
  arquivosSelecionados = [...this.files];
  atualizarNomeArquivo();
});

function atualizarNomeArquivo() {
  document.getElementById('arquivo-nome').textContent =
    arquivosSelecionados.map(f => f.name).join(', ');
  document.getElementById('btn-processar').disabled = arquivosSelecionados.length === 0;
}

function setProgresso(pct, texto) {
  document.getElementById('prog-bar').style.width = pct + '%';
  document.getElementById('prog-texto').textContent = texto;
}

function mostrarMsg(tipo, texto) {
  const el = document.getElementById('msg-upload');
  el.className = 'msg ' + (tipo === 'ok' ? 'msg-ok' : 'msg-err');
  el.textContent = texto;
}

async function processarUpload() {
  const btn = document.getElementById('btn-processar');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>Processando...';
  document.getElementById('progresso').style.display = 'block';
  document.getElementById('msg-upload').textContent = '';
  document.getElementById('msg-upload').className = '';

  let totalNovos = 0, totalDup = 0, hist = 0, ia = 0;

  try {
    for (let i = 0; i < arquivosSelecionados.length; i++) {
      const f = arquivosSelecionados[i];
      const ext = f.name.toLowerCase().endsWith('.ofx') ? 'ofx' : 'csv';
      setProgresso(
        Math.round((i / arquivosSelecionados.length) * 90) + 5,
        `Enviando ${f.name} (${i + 1}/${arquivosSelecionados.length})...`);

      const form = new FormData();
      form.append('file', f);
      const resp = await fetch(`/api/upload/${ext}`, { method: 'POST', body: form });
      if (!resp.ok) throw new Error(`Falha ao enviar ${f.name}`);
      const data = await resp.json();
      totalNovos += data.novos;
      totalDup += data.duplicados;
      hist += (data.por_origem.regra_usuario || 0);
      ia += (data.por_origem.ia || 0) + (data.por_origem.erro || 0);
    }

    setProgresso(100, 'Concluído!');
    if (totalNovos === 0) {
      mostrarMsg('ok', 'Todos os lançamentos já haviam sido carregados anteriormente.');
    } else {
      mostrarMsg('ok', `✓ ${totalNovos} lançamentos carregados — ${hist} do histórico, ${ia} pela IA.` +
        (totalDup ? ` (${totalDup} duplicados ignorados)` : ''));
    }
    // Atualiza as métricas do topo sem recarregar a página inteira.
    if (window.htmx) htmx.ajax('GET', '/upload/metricas', { target: '#metrics', swap: 'outerHTML' });
  } catch (e) {
    mostrarMsg('err', 'Erro: ' + e.message);
  }

  arquivosSelecionados = [];
  inputArquivo.value = '';
  atualizarNomeArquivo();
  btn.disabled = true;
  btn.innerHTML = '<i data-lucide="zap" style="width:14px;height:14px"></i> Carregar e categorizar';
  if (window.lucide) lucide.createIcons();
  setTimeout(() => { document.getElementById('progresso').style.display = 'none'; }, 1800);
}
