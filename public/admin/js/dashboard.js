/**
 * dashboard.js - Dashboard for Alhudha Haj Travel Admin
 * Depends on: common.js, session-manager.js, Chart.js (loaded via CDN in HTML)
 */

'use strict';

// ── State ────────────────────────────────────────────────────
let chartInstances = {};
let refreshInterval = null;
const REFRESH_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes

// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    SessionManager.initPage(async () => {
        updateDateTime();
        setInterval(updateDateTime, 1000);

        await Promise.all([
            loadDashboardStats(),
            loadRecentActivity(),
            loadTableCounts()
        ]);

        // Wait for Chart.js to be available then init charts
        waitForChartJS(() => initCharts());

        // Auto-refresh
        refreshInterval = setInterval(refreshDashboard, REFRESH_INTERVAL_MS);
    });
});

// ── Date/Time ────────────────────────────────────────────────

function updateDateTime() {
    const now = new Date();
    const dateOpts = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    const timeOpts = { hour: '2-digit', minute: '2-digit', second: '2-digit' };

    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    setEl('currentDate', now.toLocaleDateString('en-IN', dateOpts));
    setEl('currentTime', now.toLocaleTimeString('en-IN', timeOpts));
    setEl('headerDate',  now.toLocaleDateString('en-IN', { weekday: 'short', month: 'short', day: 'numeric' }));
    setEl('headerTime',  now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }));
}

// ── Stats ─────────────────────────────────────────────────────

/**
 * Fetch and display dashboard statistics
 */
async function loadDashboardStats() {
    try {
        const data = await makeAPICall('GET', '/api/admin/dashboard/stats');
        if (data.success) {
            updateStats(data.stats || {});
        }
    } catch (error) {
        console.error('❌ Dashboard stats error:', error.message);
    }
}

/**
 * Update all stat cards with fresh data
 * @param {Object} stats
 */
function updateStats(stats) {
    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };

    setEl('totalTravelers',   stats.total_travelers || 0);
    setEl('activeBatches',    stats.active_batches  || 0);
    setEl('totalCollections', formatCurrency(stats.total_collected || 0));
    setEl('pendingPayments',  formatCurrency(stats.pending_amount  || 0));
    setEl('travelerCount',    stats.total_travelers || 0);
    setEl('batchCount',       stats.total_batches   || 0);
    setEl('paymentCount',     stats.paid_count      || 0);
    setEl('receiptCount',     stats.paid_count      || 0);

    // Module card counts
    const setModule = (sel, val) => { const el = document.querySelector(sel); if (el) el.textContent = val; };
    setModule('.module-traveler-count', stats.total_travelers || 0);
    setModule('.module-batch-count',    stats.total_batches   || 0);
    setModule('.module-payment-count',  stats.paid_count      || 0);
    setModule('.module-receipt-count',  stats.paid_count      || 0);

    // Remove skeleton loaders
    document.querySelectorAll('.skeleton').forEach((el) => el.classList.remove('skeleton'));
}

// ── Recent Activity ───────────────────────────────────────────

/**
 * Fetch and display recent activity feed
 */
async function loadRecentActivity() {
    const activityEl = document.getElementById('recentActivity');
    if (!activityEl) return;

    try {
        const data = await makeAPICall('GET', '/api/admin/dashboard/stats');
        if (!data.success) return;

        const activities = [];

        (data.recent_travelers || []).slice(0, 3).forEach((t) => {
            activities.push({
                icon: 'fa-user-plus', color: '#3498db',
                text: `New traveler: ${escapeHtml(t.first_name || '')} ${escapeHtml(t.last_name || '')}`,
                time: t.created_at ? formatDate(t.created_at, true) : 'Just now'
            });
        });

        (data.recent_payments || []).slice(0, 3).forEach((p) => {
            activities.push({
                icon: 'fa-credit-card', color: '#27ae60',
                text: `Payment: ${escapeHtml(p.first_name || '')} ${escapeHtml(p.last_name || '')} — ${formatCurrency(p.amount)}`,
                time: p.payment_date ? formatDate(p.payment_date, true) : 'Just now'
            });
        });

        (data.upcoming_batches || []).slice(0, 2).forEach((b) => {
            activities.push({
                icon: 'fa-layer-group', color: '#f39c12',
                text: `Batch: ${escapeHtml(b.batch_name || '')} — ${b.booked_seats || 0}/${b.total_seats || 0} seats`,
                time: b.departure_date ? `Departs: ${formatDate(b.departure_date)}` : ''
            });
        });

        if (activities.length === 0) {
            activityEl.innerHTML = '<div style="text-align:center; padding:20px; color:#7f8c8d;">No recent activity</div>';
            return;
        }

        activityEl.innerHTML = activities.slice(0, 8).map((a) => `
            <div class="activity-item" style="display:flex; align-items:flex-start; gap:12px; padding:12px 0; border-bottom:1px solid #ecf0f1;">
                <div style="width:36px; height:36px; border-radius:50%; background:${a.color}20; display:flex; align-items:center; justify-content:center; flex-shrink:0;">
                    <i class="fas ${a.icon}" style="color:${a.color};"></i>
                </div>
                <div>
                    <p style="margin:0; font-size:0.9rem; color:#2c3e50;">${a.text}</p>
                    <small style="color:#7f8c8d;"><i class="fas fa-clock"></i> ${a.time}</small>
                </div>
            </div>`).join('');
    } catch (error) {
        console.error('❌ Recent activity error:', error.message);
    }
}

// ── Table Counts ─────────────────────────────────────────────

/**
 * Fetch and display table record counts
 */
async function loadTableCounts() {
    try {
        const data = await makeAPICall('GET', '/api/admin/table-counts');
        if (data.success && data.counts) {
            const counts = data.counts;
            const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
            setEl('userCount',    counts.users     || 0);
            setEl('invoiceCount', counts.invoices  || 0);
            setEl('receiptCount', counts.receipts  || 0);
            setEl('travelerCount', counts.travelers || 0);
            setEl('batchCount',   counts.batches   || 0);
            setEl('paymentCount', counts.payments  || 0);

            const setModule = (sel, val) => { const el = document.querySelector(sel); if (el) el.textContent = val; };
            setModule('.module-user-count',    counts.users    || 0);
            setModule('.module-invoice-count', counts.invoices || 0);
        }
    } catch (error) {
        console.error('❌ Table counts error:', error.message);
    }
}

// ── Charts ────────────────────────────────────────────────────

/**
 * Wait for Chart.js to load, then call callback
 * @param {Function} callback
 * @param {number} attempts
 */
function waitForChartJS(callback, attempts = 0) {
    if (typeof Chart !== 'undefined') {
        callback();
    } else if (attempts < 20) {
        setTimeout(() => waitForChartJS(callback, attempts + 1), 200);
    } else {
        console.warn('Chart.js not available after waiting');
    }
}

/**
 * Initialise all dashboard charts
 */
function initCharts() {
    try {
        destroyCharts();
        initPaymentsChart();
        initTravelersChart();
    } catch (e) {
        console.error('Chart init error:', e);
    }
}

function destroyCharts() {
    Object.values(chartInstances).forEach((chart) => {
        if (chart && typeof chart.destroy === 'function') {
            try { chart.destroy(); } catch (e) { /* ignore */ }
        }
    });
    chartInstances = {};
}

function initPaymentsChart() {
    const canvas = document.getElementById('paymentsChart');
    if (!canvas) return;

    chartInstances.payments = new Chart(canvas.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: ['Bank Transfer', 'UPI', 'Cash', 'Credit Card', 'Cheque'],
            datasets: [{
                data: [45, 25, 15, 10, 5],
                backgroundColor: ['#3498db', '#2ecc71', '#f1c40f', '#e74c3c', '#9b59b6'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { font: { size: 12 } } }
            },
            cutout: '60%'
        }
    });
}

function initTravelersChart() {
    const canvas = document.getElementById('travelersChart');
    if (!canvas) return;

    chartInstances.travelers = new Chart(canvas.getContext('2d'), {
        type: 'bar',
        data: {
            labels: ['Haj Platinum', 'Haj Gold', 'Haj Silver', 'Umrah Ramadhan', 'Umrah Winter'],
            datasets: [{
                label: 'Travelers',
                data: [45, 82, 120, 170, 140],
                backgroundColor: '#3498db',
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, grid: { display: false } },
                x: { grid: { display: false } }
            }
        }
    });
}

/**
 * Update chart data (called when period selector changes)
 * @param {string} chartName - 'payments' | 'travelers'
 * @param {string} period
 */
function updateCharts(chartName, period) {
    showNotification(`Updating ${chartName} chart for ${period}`, 'info');
    // In a full implementation this would fetch new data and call chart.data.datasets[0].data = newData; chart.update();
}

// ── Refresh ───────────────────────────────────────────────────

/**
 * Refresh all dashboard data
 */
async function refreshDashboard() {
    console.log('🔄 Refreshing dashboard…');
    await Promise.all([
        loadDashboardStats(),
        loadRecentActivity(),
        loadTableCounts()
    ]);
    showNotification('Dashboard refreshed', 'info', 2000);
}

// ── Cleanup ───────────────────────────────────────────────────
window.addEventListener('beforeunload', () => {
    if (refreshInterval) clearInterval(refreshInterval);
    destroyCharts();
});

// Expose globals
window.loadDashboardStats  = loadDashboardStats;
window.updateStats         = updateStats;
window.loadRecentActivity  = loadRecentActivity;
window.initCharts          = initCharts;
window.updateCharts        = updateCharts;
window.loadTableCounts     = loadTableCounts;
window.refreshDashboard    = refreshDashboard;

console.log('✅ dashboard.js loaded');
