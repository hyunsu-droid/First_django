const metricGrid = document.querySelector('#metric-grid');
const statusLabel = document.querySelector('#data-status');
const updatedAt = document.querySelector('#updated-at');
const refreshButton = document.querySelector('#refresh-button');

function formatPrice(value) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: value < 10 ? 2 : 0 }).format(value);
}

function formatLarge(value) {
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  return `$${(value / 1e6).toFixed(1)}M`;
}

function changeMarkup(value) {
  const positive = value >= 0;
  return `<span class="change ${positive ? 'positive' : 'negative'}">${positive ? '+' : ''}${Number(value).toFixed(2)}%</span>`;
}

function renderSnapshot(data) {
  const btc = data.coins.find((coin) => coin.symbol === 'BTC');
  const eth = data.coins.find((coin) => coin.symbol === 'ETH');
  const sol = data.coins.find((coin) => coin.symbol === 'SOL');
  const indexCards = (data.indices || []).map((index) => `<article class="metric-card"><small>${index.symbol}</small><strong>${Number(index.value).toLocaleString(undefined, { maximumFractionDigits: 2 })}</strong>${changeMarkup(index.change_24h)}<div class="metric-footer"><span>글로벌 지수</span><span>${index.status === 'live' ? 'LIVE' : 'FALLBACK'}</span></div></article>`).join('');
  metricGrid.innerHTML = `
    <article class="metric-card featured"><small>BTC / USD · BITCOIN</small><strong>${formatPrice(btc?.price || 0)}</strong>${changeMarkup(btc?.change_24h || 0)}<div class="metric-footer"><span>24시간 변동</span><span>${btc?.status === 'live' ? 'LIVE' : 'FALLBACK'}</span></div></article>
    <article class="metric-card"><small>ETH / USD</small><strong>${formatPrice(eth?.price || 0)}</strong>${changeMarkup(eth?.change_24h || 0)}</article>
    <article class="metric-card"><small>SOL / USD</small><strong>${formatPrice(sol?.price || 0)}</strong>${changeMarkup(sol?.change_24h || 0)}</article>
    <article class="metric-card"><small>GLOBAL MARKET CAP</small><strong>${formatLarge(data.market_cap)}</strong>${changeMarkup(data.market_cap_change)}</article>
    <article class="metric-card"><small>BTC DOMINANCE</small><strong>${Number(data.btc_dominance).toFixed(1)}%</strong><span class="change positive">시장 점유율</span></article>
    <article class="metric-card"><small>FEAR & GREED</small><strong>${data.fear_greed.value}<small>/100 · ${data.fear_greed.label}</small></strong><span class="change ${data.fear_greed.value >= 55 ? 'positive' : 'negative'}">심리 지수</span></article>${indexCards}`;
  const fallback = data.status !== 'live';
  statusLabel.textContent = fallback ? '지연 데이터 표시 중' : '실시간 데이터 연결됨';
  statusLabel.classList.toggle('is-fallback', fallback);
  updatedAt.textContent = `마지막 갱신 ${new Date(data.updated_at).toLocaleString('ko-KR')}`;
}

async function loadSnapshot() {
  refreshButton.disabled = true;
  refreshButton.textContent = '불러오는 중...';
  try {
    const response = await fetch('/api/market/', { headers: { Accept: 'application/json' } });
    if (!response.ok) throw new Error('market request failed');
    renderSnapshot(await response.json());
  } catch (error) {
    statusLabel.textContent = '데이터 연결 지연';
    statusLabel.classList.add('is-fallback');
    updatedAt.textContent = '잠시 후 새로고침해 주세요';
  } finally {
    refreshButton.disabled = false;
    refreshButton.textContent = '새로고침';
  }
}

refreshButton.addEventListener('click', loadSnapshot);
loadSnapshot();
window.setInterval(loadSnapshot, 60_000);
