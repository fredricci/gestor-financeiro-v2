// Inicializa o gráfico de barras empilhadas (Chart.js) com os dados do servidor.
(function () {
  const el = document.getElementById('chart-data');
  const canvas = document.getElementById('grafico');
  if (!el || !canvas) return;

  const chart = JSON.parse(el.textContent);
  const fmt = v => v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const labels = chart.labels.map(m => { const [y, mo] = m.split('-'); return `${mo}/${y}`; });

  const datasets = chart.datasets.map((d, idx) => ({
    label: d.label,
    data: d.data,
    backgroundColor: d.cor + 'dd',
    borderColor: d.cor,
    borderWidth: 0,
    borderRadius: 6,
    borderSkipped: false,
    order: chart.datasets.length - idx
  }));

  new Chart(canvas.getContext('2d'), {
    type: 'bar',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#64748b', font: { size: 11, family: 'Inter' }, boxWidth: 10, boxHeight: 10, borderRadius: 4, useBorderRadius: true, padding: 16 } },
        tooltip: {
          backgroundColor: '#fff', titleColor: '#0f172a', bodyColor: '#64748b',
          borderColor: '#e2e8f0', borderWidth: 1, padding: 12, cornerRadius: 10,
          callbacks: { label: c => `${c.dataset.label}: R$ ${fmt(c.parsed.y)}` }
        }
      },
      scales: {
        x: { stacked: true, ticks: { color: '#94a3b8', font: { size: 11 } }, grid: { display: false }, border: { display: false } },
        y: { stacked: true, ticks: { color: '#94a3b8', font: { size: 11 }, callback: v => 'R$ ' + fmt(v) }, grid: { color: '#f1f5f9' }, border: { display: false } }
      }
    }
  });
})();
