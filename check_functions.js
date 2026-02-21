(async function() {
    console.log("%c🔍 DASHBOARD FUNCTION CHECK", "font-size:16px;color:blue");
    console.log("=".repeat(50));
    
    // Check if user is logged in
    console.log("\n📋 SESSION STATUS:");
    console.log("Logged in:", sessionStorage.getItem('adminLoggedIn'));
    console.log("User:", sessionStorage.getItem('adminName'));
    
    // Check DOM elements
    console.log("\n📄 DOM ELEMENTS:");
    const elements = {
        'Welcome Card': 'welcome-card',
        'Stats Grid': 'stats-grid',
        'Batches Tab': 'batchesTab',
        'Travelers Tab': 'travelersTab',
        'Payments Tab': 'paymentsTab',
        'Users Tab': 'usersTab',
        'Create Batch Form': 'createBatchForm',
        'Add Traveler Form': 'addTravelerForm'
    };
    
    for (let [name, id] of Object.entries(elements)) {
        const exists = document.getElementById(id) || document.querySelector('.' + id);
        console.log(`${name}:`, exists ? '✅ Found' : '❌ Missing');
    }
    
    // Check functions
    console.log("\n⚙️ FUNCTIONS:");
    const functions = [
        'showTab', 'loadBatches', 'loadTravelers', 'loadPayments',
        'loadUsers', 'showCreateBatchForm', 'showAddTravelerForm',
        'showAddPaymentForm', 'searchBatches', 'searchTravelers',
        'logout', 'showNotification'
    ];
    
    functions.forEach(fn => {
        console.log(`${fn}:`, typeof window[fn] === 'function' ? '✅ OK' : '❌ Missing');
    });
    
    // Test API connections
    console.log("\n🌐 API CONNECTIONS:");
    
    async function testAPI(name, url) {
        try {
            let res = await fetch(url);
            if (res.ok) {
                let data = await res.json();
                console.log(`${name}: ✅ OK (${res.status})`);
                return true;
            } else {
                console.log(`${name}: ❌ Failed (${res.status})`);
                return false;
            }
        } catch(e) {
            console.log(`${name}: ❌ Error - ${e.message}`);
            return false;
        }
    }
    
    await testAPI('Batches API', '/api/batches');
    await testAPI('Travelers API', '/api/travelers');
    await testAPI('Payments API', '/api/payments');
    
    console.log("\n" + "=".repeat(50));
})();