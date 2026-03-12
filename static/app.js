const API = '';
let typeFilter = '';
let currentCurrency = 'IDR';
let currentPage = 1;
const PER_PAGE = 20;

document.addEventListener('DOMContentLoaded', () => {
    createStarfield();
    fetchBalance();
    fetchSettings();
    fetchTransactions();
});

// --- Starfield ---
function createStarfield() {
    const container = document.getElementById('starfield');
    for (let i = 0; i < 120; i++) {
        const star = document.createElement('div');
        star.className = 'star';
        const size = Math.random() * 2.5 + 0.5;
        star.style.width = size + 'px';
        star.style.height = size + 'px';
        star.style.left = Math.random() * 100 + '%';
        star.style.top = Math.random() * 100 + '%';
        star.style.setProperty('--duration', (Math.random() * 4 + 2) + 's');
        star.style.animationDelay = Math.random() * 4 + 's';
        container.appendChild(star);
    }
}

// --- Format ---
function formatMoney(amount) {
    const abs = Math.abs(amount);
    if (currentCurrency === 'IDR') {
        return (amount < 0 ? '-' : '') + 'Rp ' + abs.toLocaleString('id-ID');
    }
    return (amount < 0 ? '-' : '') + currentCurrency + ' ' + abs.toLocaleString();
}

function formatDate(isoStr) {
    const d = new Date(isoStr);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

// --- API ---
async function fetchBalance() {
    try {
        const [balRes, statusRes] = await Promise.all([
            fetch(`${API}/balance`),
            fetch(`${API}/spending-status`),
        ]);
        const bal = await balRes.json();
        const status = await statusRes.json();
        currentCurrency = bal.currency;
        renderBalance(bal, status);
    } catch (e) {
        console.error('Failed to fetch balance:', e);
    }
}

async function fetchSettings() {
    try {
        const res = await fetch(`${API}/settings`);
        const s = await res.json();
        document.getElementById('settingCurrency').value = s.currency;
        document.getElementById('settingBudget').value = s.monthly_budget;
        currentCurrency = s.currency;
    } catch (e) {
        console.error('Failed to fetch settings:', e);
    }
}

async function saveSettings() {
    const currency = document.getElementById('settingCurrency').value.trim() || 'IDR';
    const budget = parseInt(document.getElementById('settingBudget').value) || 0;
    try {
        await fetch(`${API}/settings`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ currency, monthly_budget: budget }),
        });
        currentCurrency = currency;
        fetchBalance();
        showToast('Settings saved');
    } catch (e) {
        console.error('Failed to save settings:', e);
    }
}

async function fetchTransactions(page) {
    if (page !== undefined) currentPage = page;
    const params = new URLSearchParams();
    if (typeFilter) params.set('type', typeFilter);
    const cat = document.getElementById('categoryFilter').value.trim();
    if (cat) params.set('category', cat);
    params.set('page', currentPage);
    params.set('per_page', PER_PAGE);

    try {
        const res = await fetch(`${API}/transactions?${params}`);
        const data = await res.json();
        renderTransactions(data.items || data, data.total || 0);
    } catch (e) {
        console.error('Failed to fetch transactions:', e);
    }
}

async function handleCreate() {
    const type = document.getElementById('txType').value;
    const amount = parseInt(document.getElementById('txAmount').value);
    if (!amount || amount <= 0) return;

    const body = {
        type,
        amount,
        description: document.getElementById('txDesc').value.trim(),
        category: document.getElementById('txCategory').value.trim(),
    };

    try {
        await fetch(`${API}/transactions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        document.getElementById('txAmount').value = '';
        document.getElementById('txDesc').value = '';
        document.getElementById('txCategory').value = '';
        fetchTransactions();
        fetchBalance();
    } catch (e) {
        console.error('Failed to create transaction:', e);
    }
}

async function deleteTx(id) {
    try {
        await fetch(`${API}/transactions/${id}`, { method: 'DELETE' });
        fetchTransactions();
        fetchBalance();
    } catch (e) {
        console.error('Delete failed:', e);
    }
}

async function seedData() {
    await fetch(`${API}/dev/seed`, { method: 'POST' });
    fetchBalance();
    fetchSettings();
    fetchTransactions();
}

async function resetData() {
    if (!confirm('Clear all transactions?')) return;
    await fetch(`${API}/dev/reset`, { method: 'POST' });
    fetchBalance();
    fetchTransactions();
}

// --- Filters ---
function setTypeFilter(filter, btn) {
    typeFilter = filter;
    currentPage = 1;
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    fetchTransactions();
}

// --- Rendering ---
function renderBalance(bal, status) {
    const amountEl = document.getElementById('balanceAmount');
    amountEl.textContent = formatMoney(bal.balance);
    amountEl.className = 'balance-amount' + (bal.balance < 0 ? ' negative' : '');

    document.getElementById('monthlyIncome').textContent = formatMoney(bal.monthly_income);
    document.getElementById('monthlyExpense').textContent = formatMoney(bal.monthly_expense);

    // Spending bar
    const bar = document.getElementById('spendingBar');
    const label = document.getElementById('spendingLabel');

    if (status.monthly_budget > 0) {
        const pct = Math.min(status.spent_percent, 100);
        bar.style.width = pct + '%';
        bar.className = 'spending-bar' + (status.threshold === 'critical' ? ' critical' : status.threshold === 'warning' ? ' warning' : '');
        label.textContent = `${status.spent_percent}% of ${formatMoney(status.monthly_budget)} budget spent`;
    } else {
        bar.style.width = '0%';
        label.textContent = 'No monthly budget set';
    }
}

function renderTransactions(txs, total) {
    const list = document.getElementById('txList');

    if (txs.length === 0) {
        list.innerHTML = '<p class="empty-state">No transactions yet.</p>';
        return;
    }

    // All values are escaped via escapeHtml() — safe for innerHTML
    const cards = txs.map(t => {
        const icon = t.type === 'income' ? '+' : '-';
        const prefix = t.type === 'income' ? '+' : '-';
        return `
            <div class="tx-card ${t.type}">
                <div class="tx-icon">${icon}</div>
                <div class="tx-body">
                    <div class="tx-desc">${escapeHtml(t.description || t.type)}</div>
                    <div class="tx-meta">
                        ${t.category ? `<span class="tag">${escapeHtml(t.category)}</span>` : ''}
                        <span>${formatDate(t.created_at)}</span>
                    </div>
                </div>
                <span class="tx-amount">${prefix}${formatMoney(t.amount).replace(/^-/, '')}</span>
                <div class="tx-actions">
                    <button onclick="deleteTx('${t.id}')">Del</button>
                </div>
            </div>
        `;
    }).join('');

    const totalPages = Math.ceil(total / PER_PAGE);
    const pagination = totalPages > 1 ? `
        <div class="pagination">
            <button class="page-btn" onclick="fetchTransactions(${currentPage - 1})" ${currentPage <= 1 ? 'disabled' : ''}>Prev</button>
            <span class="page-info">${currentPage} / ${totalPages}</span>
            <button class="page-btn" onclick="fetchTransactions(${currentPage + 1})" ${currentPage >= totalPages ? 'disabled' : ''}>Next</button>
        </div>
    ` : '';

    list.innerHTML = cards + pagination;
}

function showToast(message) {
    const container = document.getElementById('toasts');
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
