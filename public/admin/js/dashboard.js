/**
 * dashboard.js - Dashboard statistics and chart functions
 * Alhudha Haj Travel Admin Panel
 * Alhudha Haj Travel Management System
 * Depends on: common.js, session-manager.js, Chart.js (loaded via CDN in HTML)
 */

'use strict';

// ====== STATE ======
let dashboardChartInstances = {};
let dashboardRefreshInterval = null;
const REFRESH_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes

// ====== LOAD DASHBOARD STATS ======
/**
 * Fetch dashboard statistics from /api/admin/dashboard/stats
 */
async function loadDashboardStats() {
    try {
        const data = await makeAPICall('GET', '/api/admin/dashboard/stats');
        if (data.success || data.stats) {
            const stats = data.stats || data;
            updateStatCards(stats);
            console.log('✅ Dashboard stats loaded');
            return stats;
        } else {
            await loadStatsFromIndividualAPIs();
        }
    } catch (error) {
        console.warn('Dashboard stats API not available, loading from individual APIs');
        await loadStatsFromIndividualAPIs();
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
        
        // Update batch return dates
        updateBatchReturnDates(batches);

    } catch (error) {
        handleAPIError(error, 'loadStatsFromIndividualAPIs');
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

// ====== UPDATE BATCH RETURN DATES ======
/**
 * Update batch return dates from batch data
 * @param {Array} batches
 */
function updateBatchReturnDates(batches) {
    if (!batches || batches.length === 0) return;
    
    // Find elements that display return dates
    const returnDateElements = document.querySelectorAll('[data-batch-return], .batch-return-date, #batchReturnDate');
    
    if (returnDateElements.length === 0) return;
    
    // Sort batches by return date (latest first)
    const sortedBatches = batches
        .filter(b => b.return_date)
        .sort((a, b) => new Date(b.return_date) - new Date(a.return_date));
    
    if (sortedBatches.length === 0) return;
    
    const latestBatch = sortedBatches[0];
    const returnDate = formatDate(latestBatch.return_date);
    
    console.log(`📅 Latest batch return date: ${returnDate} (${latestBatch.batch_name})`);
    
    // Update all return date elements
    returnDateElements.forEach(el => {
        el.textContent = returnDate;
        el.setAttribute('data-batch-name', latestBatch.batch_name || '');
        el.setAttribute('data-batch-id', latestBatch.id || '');
    });
}

// ====== LOAD RECENT ACTIVITY ======
/**
 * Fetch recent activity from /api/admin/dashboard/stats
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
            <div class="activity-details">
                <p>${escapeHtml(a.description || a.action || 'Activity')}</p>
                <small>${formatDate(a.created_at || a.timestamp, true)}</small>
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

    const labels = batches.length ? batches.map(b => b.batch_name || b.name) : ['Haj Platinum', 'Haj Gold', 'Umrah'];
    const values = batches.length ? batches.map(b => b.booked_seats || b.traveler_count || 0) : [45, 82, 24];

    dashboardChartInstances.travelers = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Booked Seats',
                data: values,
                backgroundColor: '#3498db',
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom' } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

// ====== UPDATE CHARTS ======
/**
 * Update chart data with fresh values
 * @param {Object} data - { payments: [], travelers: {}, batches: [] }
 */
function updateCharts(data) {
    if (!data || typeof Chart === 'undefined') return;

    // Charts will be re-initialized on refresh
    console.log('📊 Charts updated');
}

// ====== LOAD TABLE COUNTS ======
/**
 * Fetch table record counts from the API
 */
async function loadTableCounts() {
    try {
        const data = await makeAPICall('GET', '/api/admin/table-counts');

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

        return data;
    } catch (error) {
        handleAPIError(error, 'Load table counts');
        return null;
    }
}

// ====== REFRESH DASHBOARD ======
/**
 * Refresh all dashboard data
 */
async function refreshDashboard() {
    showLoading('Refreshing dashboard...');
    try {
        await Promise.allSettled([
            loadDashboardStats(),
            loadRecentActivity(),
            loadTableCounts()
        ]);

        showNotification('Dashboard refreshed!', 'success');
        console.log('✅ Dashboard refreshed');
    } catch (error) {
        handleAPIError(error, 'Refresh dashboard');
    } finally {
        hideLoading();
    }
}

/**
 * Start auto-refresh interval for the dashboard
 * @param {number} intervalMs - Refresh interval in milliseconds (default: 5 minutes)
 */
function startDashboardAutoRefresh(intervalMs = REFRESH_INTERVAL_MS) {
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

// ====== DATE/TIME UPDATE ======
function updateDateTime() {
    const now = new Date();
    const dateOpts = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    const timeOpts = { hour: '2-digit', minute: '2-digit', second: '2-digit' };

    setEl('currentDate', now.toLocaleDateString('en-IN', dateOpts));
    setEl('currentTime', now.toLocaleTimeString('en-IN', timeOpts));
    setEl('headerDate',  now.toLocaleDateString('en-IN', { weekday: 'short', month: 'short', day: 'numeric' }));
    setEl('headerTime',  now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }));
}

// ====== INITIALIZATION ======
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 Dashboard page loaded');
    
    // Setup logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('🚪 Logout button clicked');
            logout();
        });
    }
    
    // Initialize session and load data
    SessionManager.initPage(async () => {
        console.log('✅ Session verified, initializing dashboard');
        
        updateDateTime();
        setInterval(updateDateTime, 1000);

        await Promise.all([
            loadDashboardStats(),
            loadRecentActivity(),
            loadTableCounts()
        ]);

        // Wait for Chart.js to be available then init charts
        if (typeof Chart !== 'undefined') {
            initCharts();
        }

        // Auto-refresh
        startDashboardAutoRefresh();
    });
});

// ====== CLEANUP ======
window.addEventListener('beforeunload', () => {
    stopDashboardAutoRefresh();
});

// Expose globals
window.loadDashboardStats  = loadDashboardStats;
window.updateStatCards    = updateStatCards;
window.loadRecentActivity = loadRecentActivity;
window.initCharts         = initCharts;
window.updateCharts       = updateCharts;
window.loadTableCounts    = loadTableCounts;
window.refreshDashboard   = refreshDashboard;
window.updateBatchReturnDates = updateBatchReturnDates;

console.log('✅ dashboard.js loaded');
