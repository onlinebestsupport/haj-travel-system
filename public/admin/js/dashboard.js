/**
 * dashboard.js - Dashboard statistics and chart functions
 * Alhudha Haj Travel Admin Panel
 * Alhudha Haj Travel Management System
 * dashboard.js - Dashboard for Alhudha Haj Travel Admin
 * Depends on: common.js, session-manager.js, Chart.js (loaded via CDN in HTML)
 */

'use strict';

// ====== STATE ======
let dashboardChartInstances = {};
// Module-level state
let dashboardCharts = {};
let dashboardRefreshInterval = null;

// ====== LOAD DASHBOARD STATS ======
/**
 * Fetch dashboard statistics from /api/admin/dashboard/stats
 */
async function loadDashboardStats() {
    // Show skeleton loading
    document.querySelectorAll('.stat-number, .badge, [id$="Count"], [id$="Travelers"], [id$="Batches"], [id$="Collections"], [id$="Payments"]')
        .forEach(el => el.classList.add('skeleton'));

    try {
        const data = await makeAPICall('GET', '/api/admin/dashboard/stats');
        if (data.success || data.stats) {
            const stats = data.stats || data;
            updateStatCards(stats);
            console.log('✅ Dashboard stats loaded');
        } else {
            await loadStatsFromIndividualAPIs();
        }
    } catch (error) {
        console.warn('Dashboard stats API not available, loading from individual APIs');
        await loadStatsFromIndividualAPIs();
    } finally {
        document.querySelectorAll('.skeleton').forEach(el => el.classList.remove('skeleton'));
    }
}

// ====== LOAD FROM INDIVIDUAL APIS ======
async function loadStatsFromIndividualAPIs() {
    try {
        const [travelersRes, batchesRes, paymentsRes] = await Promise.allSettled([
            makeAPICall('GET', '/api/travelers'),
            makeAPICall('GET', '/api/batches'),
            makeAPICall('GET', '/api/payments')
        ]);

        const travelers = travelersRes.status === 'fulfilled' && travelersRes.value.travelers ? travelersRes.value.travelers : [];
        const batches = batchesRes.status === 'fulfilled' && batchesRes.value.batches ? batchesRes.value.batches : [];
        const payments = paymentsRes.status === 'fulfilled' && paymentsRes.value.payments ? paymentsRes.value.payments : [];

        const totalCollections = payments.filter(p => p.status === 'completed').reduce((s, p) => s + (p.amount || 0), 0);
        const pendingPayments = payments.filter(p => p.status !== 'completed').reduce((s, p) => s + (p.amount || 0), 0);
        const activeBatches = batches.filter(b => b.status === 'Open').length;

        updateStatCards({
            total_travelers: travelers.length,
            active_batches: activeBatches,
            total_collections: totalCollections,
            pending_payments: pendingPayments,
            traveler_count: travelers.length,
            batch_count: batches.length,
            payment_count: payments.length
        });

        // Update nav badges
        setEl('travelerCount', travelers.length);
        setEl('batchCount', batches.length);
        setEl('paymentCount', payments.length);

        // Initialize charts with real data
        initCharts({ travelers, batches, payments });

    } catch (error) {
        handleAPIError(error, 'loadStatsFromIndividualAPIs');
 * Fetch dashboard statistics from the API
 */
async function loadDashboardStats() {
    try {
        const stats = await makeApiCall('GET', '/api/admin/dashboard/stats');
        updateStatCards(stats);
        console.log('✅ Dashboard stats loaded');
        return stats;
    } catch (error) {
        handleApiError(error, 'Load dashboard stats');
        return null;
    }
}

// ====== UPDATE STAT CARDS ======
/**
 * Update the stat card values on the dashboard
 * @param {Object} stats
 */
function updateStatCards(stats) {
    if (!stats) return;

    setEl('totalTravelers', stats.total_travelers || stats.traveler_count || 0);
    setEl('activeBatches', stats.active_batches || stats.batch_count || 0);
    setEl('totalCollections', formatCurrency(stats.total_collections || stats.collections || 0));
    setEl('pendingPayments', formatCurrency(stats.pending_payments || stats.pending || 0));

    // Nav sidebar badges
    setEl('travelerCount', stats.traveler_count || stats.total_travelers || 0);
    setEl('batchCount', stats.batch_count || stats.active_batches || 0);
    setEl('paymentCount', stats.payment_count || 0);
    setEl('invoiceCount', stats.invoice_count || 0);
    setEl('receiptCount', stats.receipt_count || 0);
    setEl('userCount', stats.user_count || 0);
    const mappings = {
        'totalTravelers':    stats.total_travelers    || stats.travelers    || 0,
        'totalBatches':      stats.total_batches      || stats.batches      || 0,
        'totalPayments':     stats.total_payments     || stats.payments     || 0,
        'totalRevenue':      formatCurrency(stats.total_revenue || stats.revenue || 0),
        'pendingPayments':   stats.pending_payments   || stats.pending      || 0,
        'activeBatches':     stats.active_batches     || stats.open_batches || 0,
        'totalInvoices':     stats.total_invoices     || stats.invoices     || 0,
        'totalUsers':        stats.total_users        || stats.users        || 0
    };

    Object.entries(mappings).forEach(([id, value]) => {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = value;
            el.classList.remove('skeleton');
        }
    });

    // Also update any elements with data-stat attributes
    document.querySelectorAll('[data-stat]').forEach(el => {
        const key = el.getAttribute('data-stat');
        if (stats[key] !== undefined) {
            el.textContent = key.includes('revenue') || key.includes('amount')
                ? formatCurrency(stats[key])
                : stats[key];
        }
    });
}

// ====== LOAD RECENT ACTIVITY ======
/**
 * Fetch recent activity from /api/admin/recent-activity
 */
async function loadRecentActivity() {
    try {
        const data = await makeAPICall('GET', '/api/admin/dashboard/stats');
        if (data.recent_activity || data.activity) {
            displayActivity(data.recent_activity || data.activity);
        } else {
            displayActivity(getDemoActivity());
        }
    } catch (error) {
        displayActivity(getDemoActivity());
    }
}

// ====== DISPLAY ACTIVITY ======
/**
 * Render the activity feed
 * @param {Array} activities
 */
function displayActivity(activities) {
    const container = document.getElementById('recentActivity');
    if (!container) return;

    if (!activities || activities.length === 0) {
        container.innerHTML = '<div style="text-align:center;padding:20px;color:#7f8c8d;">No recent activity</div>';
 * Fetch recent activity from the API
 */
async function loadRecentActivity() {
    try {
        const data = await makeApiCall('GET', '/api/admin/recent-activity');
        const activity = Array.isArray(data) ? data : (data.activity || data.activities || []);
        displayRecentActivity(activity);
        return activity;
    } catch (error) {
        handleApiError(error, 'Load recent activity');
        return [];
    }
}

// ====== DISPLAY RECENT ACTIVITY ======
/**
 * Render the activity feed
 * @param {Array} activity
 */
function displayRecentActivity(activity) {
    const container = document.getElementById('recentActivity') || document.getElementById('activityFeed');
    if (!container) return;

    if (!activity || activity.length === 0) {
        container.innerHTML = '<p style="text-align:center;color:#95a5a6;padding:20px;">No recent activity</p>';
        return;
    }

    const iconMap = {
        payment: 'credit-card',
        traveler: 'user',
        batch: 'layer-group',
        invoice: 'file-invoice',
        login: 'sign-in-alt',
        logout: 'sign-out-alt',
        default: 'bell'
    };

    container.innerHTML = activities.slice(0, 10).map(a => {
        const icon = iconMap[a.type] || iconMap.default;
        const colorClass = a.type === 'payment' ? 'payment' : a.type === 'traveler' ? 'traveler' : 'default';
        return `<div class="activity-item">
            <div class="activity-icon ${colorClass}"><i class="fas fa-${icon}"></i></div>
            <div class="activity-content">
                <p>${escapeHtml(a.description || a.action || 'Activity')}</p>
                <small>${formatDate(a.created_at || a.timestamp)}</small>
            </div>
        </div>`;
        traveler: 'fa-user',
        payment:  'fa-credit-card',
        batch:    'fa-layer-group',
        invoice:  'fa-file-invoice',
        receipt:  'fa-receipt',
        login:    'fa-sign-in-alt',
        default:  'fa-bell'
    };

    container.innerHTML = activity.slice(0, 10).map(item => {
        const type = (item.type || item.action_type || 'default').toLowerCase();
        const icon = Object.keys(iconMap).find(k => type.includes(k)) ? iconMap[Object.keys(iconMap).find(k => type.includes(k))] : iconMap.default;
        return `
            <div style="display:flex;align-items:flex-start;gap:12px;padding:12px 0;border-bottom:1px solid #ecf0f1;">
                <div style="width:36px;height:36px;background:rgba(52,152,219,0.1);border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <i class="fas ${icon}" style="color:#3498db;font-size:0.9rem;"></i>
                </div>
                <div style="flex:1;">
                    <div style="font-size:0.9rem;color:#2c3e50;">${escapeHtml(item.description || item.message || item.action || 'Activity')}</div>
                    <div style="font-size:0.8rem;color:#95a5a6;margin-top:3px;">${formatDate(item.created_at || item.timestamp)}</div>
                </div>
            </div>`;
    }).join('');
}

// ====== INIT CHARTS ======
/**
 * Initialize Chart.js charts on the dashboard
 * @param {Object} [data] - Optional data for charts
 */
function initCharts(data = {}) {
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js not loaded yet, retrying in 1s...');
        setTimeout(() => initCharts(data), 1000);
        return;
    }

    try {
        initPaymentsChart(data.payments || []);
        initTravelersChart(data.batches || []);
    } catch (e) {
        console.warn('Chart initialization error:', e);
    }
}

function initPaymentsChart(payments) {
    const ctx = document.getElementById('paymentsChart')?.getContext('2d');
    if (!ctx) return;

    if (dashboardChartInstances.payments) dashboardChartInstances.payments.destroy();

    const methodCounts = {};
    payments.forEach(p => {
        const method = p.payment_method || p.method || 'Other';
        methodCounts[method] = (methodCounts[method] || 0) + (p.amount || 0);
    });

    const labels = Object.keys(methodCounts).length ? Object.keys(methodCounts) : ['Cash', 'Bank Transfer', 'UPI', 'Cheque'];
    const values = Object.values(methodCounts).length ? Object.values(methodCounts) : [40, 30, 20, 10];

    dashboardChartInstances.payments = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: ['#3498db', '#27ae60', '#f39c12', '#e74c3c', '#9b59b6'],
                borderWidth: 2,
                borderColor: '#fff'
 */
function initCharts() {
    // Wait for Chart.js to be available
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js not loaded yet, retrying in 500ms...');
        setTimeout(initCharts, 500);
        return;
    }

    // Payment trend chart
    const paymentCtx = document.getElementById('paymentChart') || document.getElementById('paymentsChart');
    if (paymentCtx && !dashboardCharts.payment) {
        dashboardCharts.payment = new Chart(paymentCtx, {
            type: 'line',
            data: {
                labels: getLast6Months(),
                datasets: [{
                    label: 'Payments (₹)',
                    data: [0, 0, 0, 0, 0, 0],
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52,152,219,0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, ticks: { callback: v => '₹' + v.toLocaleString('en-IN') } }
                }
            }
        });
    }

    // Traveler status chart
    const travelerCtx = document.getElementById('travelerChart') || document.getElementById('travelersChart');
    if (travelerCtx && !dashboardCharts.traveler) {
        dashboardCharts.traveler = new Chart(travelerCtx, {
            type: 'doughnut',
            data: {
                labels: ['Active', 'Pending', 'Inactive'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: ['#27ae60', '#f39c12', '#e74c3c'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }

    // Batch capacity chart
    const batchCtx = document.getElementById('batchChart') || document.getElementById('batchesChart');
    if (batchCtx && !dashboardCharts.batch) {
        dashboardCharts.batch = new Chart(batchCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [
                    { label: 'Capacity', data: [], backgroundColor: 'rgba(52,152,219,0.6)' },
                    { label: 'Enrolled', data: [], backgroundColor: 'rgba(39,174,96,0.6)' }
                ]
            },
            options: {
                responsive: true,
                scales: { y: { beginAtZero: true } }
            }
        });
    }

    console.log('✅ Dashboard charts initialized');
}

/**
 * Get labels for the last 6 months
 * @returns {string[]}
 */
function getLast6Months() {
    const months = [];
    for (let i = 5; i >= 0; i--) {
        const d = new Date();
        d.setMonth(d.getMonth() - i);
        months.push(d.toLocaleString('en-IN', { month: 'short', year: '2-digit' }));
    }
    return months;
}

// ====== UPDATE CHARTS ======
/**
 * Update chart data with fresh values
 * @param {Object} data - { payments: [], travelers: {}, batches: [] }
 */
function updateCharts(data) {
    if (!data || typeof Chart === 'undefined') return;

    // Update payment trend chart
    if (dashboardCharts.payment && data.payment_trend) {
        dashboardCharts.payment.data.datasets[0].data = data.payment_trend;
        dashboardCharts.payment.update();
    }

    // Update traveler status chart
    if (dashboardCharts.traveler && data.traveler_status) {
        const s = data.traveler_status;
        dashboardCharts.traveler.data.datasets[0].data = [
            s.active || 0,
            s.pending || 0,
            s.inactive || 0
        ];
        dashboardCharts.traveler.update();
    }

    // Update batch capacity chart
    if (dashboardCharts.batch && data.batches) {
        dashboardCharts.batch.data.labels   = data.batches.map(b => b.name || b.batch_name || '');
        dashboardCharts.batch.data.datasets[0].data = data.batches.map(b => b.capacity || 0);
        dashboardCharts.batch.data.datasets[1].data = data.batches.map(b => b.enrolled || b.traveler_count || 0);
        dashboardCharts.batch.update();
    }
}

// ====== LOAD TABLE COUNTS ======
/**
 * Fetch table record counts from the API
 */
async function loadTableCounts() {
    try {
        const data = await makeApiCall('GET', '/api/admin/table-counts');

        const countMappings = {
            'travelerCount':  data.travelers || 0,
            'batchCount':     data.batches   || 0,
            'paymentCount':   data.payments  || 0,
            'invoiceCount':   data.invoices  || 0,
            'receiptCount':   data.receipts  || 0,
            'userCount':      data.users     || 0
        };

        Object.entries(countMappings).forEach(([id, value]) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        });

        // Also update module stat elements
        document.querySelectorAll('.module-traveler-count').forEach(el => { el.textContent = data.travelers || 0; });
        document.querySelectorAll('.module-batch-count').forEach(el => { el.textContent = data.batches || 0; });
        document.querySelectorAll('.module-payment-count').forEach(el => { el.textContent = data.payments || 0; });
        document.querySelectorAll('.module-user-count').forEach(el => { el.textContent = data.users || 0; });

        return data;
    } catch (error) {
        handleApiError(error, 'Load table counts');
        return null;
    }
}

// ====== REFRESH DASHBOARD ======
/**
 * Refresh all dashboard data
 */
async function refreshDashboard() {
    showLoading(true);
    try {
        const [stats, , counts] = await Promise.allSettled([
            loadDashboardStats(),
            loadRecentActivity(),
            loadTableCounts()
        ]);

        // Update charts with fresh data if stats loaded
        if (stats.status === 'fulfilled' && stats.value) {
            updateCharts(stats.value);
        }

        showNotification('Dashboard refreshed!', 'success');
        console.log('✅ Dashboard refreshed');
    } catch (error) {
        handleApiError(error, 'Refresh dashboard');
    } finally {
        showLoading(false);
    }
}

/**
 * Start auto-refresh interval for the dashboard
 * @param {number} intervalMs - Refresh interval in milliseconds (default: 5 minutes)
 */
function startDashboardAutoRefresh(intervalMs = 300000) {
    if (dashboardRefreshInterval) clearInterval(dashboardRefreshInterval);
    dashboardRefreshInterval = setInterval(refreshDashboard, intervalMs);
    console.log(`✅ Dashboard auto-refresh started (every ${intervalMs / 1000}s)`);
}

/**
 * Stop the dashboard auto-refresh interval
 */
function stopDashboardAutoRefresh() {
    if (dashboardRefreshInterval) {
        clearInterval(dashboardRefreshInterval);
        dashboardRefreshInterval = null;
    }
}
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
            plugins: { legend: { position: 'bottom' } }
        }
    });
}

function initTravelersChart(batches) {
    const ctx = document.getElementById('travelersChart')?.getContext('2d');
    if (!ctx) return;

    if (dashboardChartInstances.travelers) dashboardChartInstances.travelers.destroy();

    const labels = batches.length ? batches.map(b => b.batch_name) : ['Haj Platinum', 'Haj Gold', 'Umrah'];
    const values = batches.length ? batches.map(b => b.booked_seats || 0) : [45, 82, 24];

    dashboardChartInstances.travelers = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Booked Seats',
                data: values,
                backgroundColor: '#3498db',
                borderRadius: 5
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
            scales: { y: { beginAtZero: true } }
        }
    });
}

// ====== UPDATE CHARTS ======
/**
 * Update chart data without reinitializing
 */
function updateCharts() {
    loadStatsFromIndividualAPIs();
}

// ====== LOAD TABLE COUNTS ======
/**
 * Fetch table counts from /api/admin/table-counts
 */
async function loadTableCounts() {
    try {
        const data = await makeAPICall('GET', '/api/admin/table-counts');
        if (data.success && data.counts) {
            const c = data.counts;
            setEl('travelerCount', c.travelers || 0);
            setEl('batchCount', c.batches || 0);
            setEl('paymentCount', c.payments || 0);
            setEl('invoiceCount', c.invoices || 0);
            setEl('receiptCount', c.receipts || 0);
            setEl('userCount', c.users || 0);
        }
    } catch (error) {
        // Table counts are optional
        console.log('ℹ️ Table counts API not available');
    }
}

// ====== REFRESH DASHBOARD ======
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
    showNotification('Refreshing dashboard...', 'info');
    await Promise.allSettled([
    console.log('🔄 Refreshing dashboard…');
    await Promise.all([
        loadDashboardStats(),
        loadRecentActivity(),
        loadTableCounts()
    ]);
    showNotification('Dashboard refreshed!', 'success');
}

// ====== DEMO ACTIVITY ======
function getDemoActivity() {
    return [
        { type: 'payment', description: 'Payment of ₹85,000 received from Ahmed Khan', created_at: new Date().toISOString() },
        { type: 'traveler', description: 'New traveler Fatima Begum registered', created_at: new Date(Date.now() - 3600000).toISOString() },
        { type: 'batch', description: 'Haj Platinum 2026 batch updated', created_at: new Date(Date.now() - 7200000).toISOString() },
        { type: 'invoice', description: 'Invoice #INV-0042 generated', created_at: new Date(Date.now() - 10800000).toISOString() }
    ];
}

// ====== HELPER ======
function setEl(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
}
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
