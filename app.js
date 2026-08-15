const DATA_BASE = 'data';
const currentCache = {};

// 顶部导航：当前榜 / 历史榜
document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const view = btn.dataset.view;
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById(view + '-view').classList.add('active');
    if (view === 'history') loadHistoryDates('daily');
  });
});

// 当前榜 tab：日 / 周 / 月
document.querySelectorAll('#current-view .tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('#current-view .tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    loadCurrent(btn.dataset.period);
  });
});

// 历史榜 tab：日 / 周 / 月
document.querySelectorAll('#history-view .tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('#history-view .tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    loadHistoryDates(btn.dataset.histPeriod);
  });
});

// 加载当前榜
async function loadCurrent(period) {
  const container = document.getElementById('current-list');
  if (currentCache[period]) {
    renderList(container, currentCache[period]);
    return;
  }
  container.innerHTML = '<div class="empty">加载中...</div>';
  try {
    const res = await fetch(`${DATA_BASE}/${period}.json`);
    const data = await res.json();
    currentCache[period] = data;
    renderList(container, data);
  } catch (e) {
    container.innerHTML = '<div class="empty">数据加载失败</div>';
  }
}

// 加载历史日期列表
async function loadHistoryDates(period) {
  const datesContainer = document.getElementById('history-dates');
  const listContainer = document.getElementById('history-list');
  listContainer.innerHTML = '';
  try {
    const res = await fetch(`${DATA_BASE}/history/index.json`);
    const index = await res.json();
    const dates = index[period] || [];
    if (dates.length === 0) {
      datesContainer.innerHTML = '';
      listContainer.innerHTML = '<div class="empty">暂无历史数据，等待 Actions 首次抓取</div>';
      return;
    }
    datesContainer.innerHTML = dates.map(d =>
      `<button class="date-btn" data-date="${d}">${d}</button>`
    ).join('');
    document.querySelectorAll('.date-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.date-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        loadHistoryDetail(period, btn.dataset.date);
      });
    });
    document.querySelector('.date-btn').click();
  } catch (e) {
    listContainer.innerHTML = '<div class="empty">历史索引加载失败</div>';
  }
}

// 加载某个历史日期的榜单
async function loadHistoryDetail(period, date) {
  const container = document.getElementById('history-list');
  container.innerHTML = '<div class="empty">加载中...</div>';
  try {
    const res = await fetch(`${DATA_BASE}/history/${period}/${date}.json`);
    const data = await res.json();
    renderList(container, data);
  } catch (e) {
    container.innerHTML = '<div class="empty">历史数据加载失败</div>';
  }
}

// 渲染榜单列表
function renderList(container, data) {
  if (!data || data.length === 0) {
    container.innerHTML = '<div class="empty">暂无数据</div>';
    return;
  }
  container.innerHTML = data.map(item => `
    <div class="card" data-url="${item.url}">
      <div class="card-header">
        <span class="rank">#${item.rank}</span>
        <span class="repo-name">${item.repo}</span>
      </div>
      <div class="card-desc">${item.description || '暂无简介'}</div>
      <div class="card-meta">
        ${item.language ? `<span class="lang">${item.language}</span>` : ''}
        <span class="stars">+${formatNum(item.stars_period)} 本期</span>
        <span>${formatNum(item.stars_total)} 总计</span>
        <span>${formatNum(item.forks)} forks</span>
      </div>
      <div class="card-detail">
        <a class="detail-link" href="${item.url}" target="_blank" rel="noopener">在 GitHub 查看 →</a>
      </div>
    </div>
  `).join('');
  container.querySelectorAll('.card').forEach(card => {
    card.addEventListener('click', (e) => {
      if (e.target.classList.contains('detail-link')) return;
      card.classList.toggle('expanded');
    });
  });
}

function formatNum(n) {
  if (!n) return '0';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
  return n.toString();
}

// 初始加载周榜
loadCurrent('weekly');
