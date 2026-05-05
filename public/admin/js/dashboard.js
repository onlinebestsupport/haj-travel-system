/**
 * dashboard.js - Dashboard statistics and chart functions
 * Alhudha Haj Travel Management System
 */

'use strict';

// Module-level state
let dashboardCharts = {};
let dashboardRefreshInterval = null;

// ====== LOAD DASHBOARD STATS ======
/**
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
