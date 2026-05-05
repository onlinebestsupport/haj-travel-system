/**
 * dashboard.js - Dashboard statistics and chart functions
 * Alhudha Haj Travel Admin Panel
 */

'use strict';

// ====== STATE ======
let dashboardChartInstances = {};
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
/**
 * Refresh all dashboard data
 */
async function refreshDashboard() {
    showNotification('Refreshing dashboard...', 'info');
    await Promise.allSettled([
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

console.log('✅ dashboard.js loaded');
