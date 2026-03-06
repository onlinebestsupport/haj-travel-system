# consolidate_all_functions.py
import os
import re

print("="*70)
print("📦 FUNCTION CONSOLIDATION UTILITY")
print("="*70)

project_root = r"C:\\Users\\Masood\\Desktop\\haj-travel-system\\haj-travel-system"
session_manager_path = os.path.join(project_root, 'public', 'admin', 'js', 'session-manager.js')

# Read session manager
with open(session_manager_path, 'r', encoding='utf-8') as f:
    sm_content = f.read()

# Common functions to add to session-manager.js
common_functions = {
    'checkAuth': '''    checkAuth: function() {
        const isLoggedIn = sessionStorage.getItem('adminLoggedIn');
        if (!isLoggedIn) {
            window.location.href = '/admin.login.html';
            return false;
        }
        return true;
    },''',
    
    'showError': '''    showError: function(message) {
        this.showNotification(message, 'error');
    },''',
    
    'showSuccess': '''    showSuccess: function(message) {
        this.showNotification(message, 'success');
    },''',
    
    'validateForm': '''    validateForm: function(fields) {
        for (let field of fields) {
            const value = document.getElementById(field.id)?.value;
            if (!value || value.trim() === '') {
                this.showError(field.name + ' is required');
                return false;
            }
        }
        return true;
    },''',
    
    'formatDate': '''    formatDate: function(date) {
        if (!date) return '';
        const d = new Date(date);
        return d.toLocaleDateString('en-IN');
    },''',
    
    'formatCurrency': '''    formatCurrency: function(amount) {
        return '₹' + Number(amount).toLocaleString('en-IN');
    },''',
    
    'getUrlParameter': '''    getUrlParameter: function(name) {
        const url = window.location.search;
        const regex = new RegExp('[?&]' + name + '=([^&#]*)');
        const results = regex.exec(url);
        return results ? decodeURIComponent(results[1].replace(/\+/g, ' ')) : null;
    }'''
}

# Add missing functions
added = 0
for func_name, func_code in common_functions.items():
    if func_name not in sm_content:
        # Insert before the last '}'
        last_brace = sm_content.rfind('}')
        if last_brace > 0:
            sm_content = sm_content[:last_brace] + '\n' + func_code + '\n' + sm_content[last_brace:]
            print(f"✅ Added {func_name} to session-manager.js")
            added += 1

if added > 0:
    with open(session_manager_path, 'w', encoding='utf-8') as f:
        f.write(sm_content)

# Now update HTML files to use SessionManager functions
print("\n📋 Updating HTML files to use SessionManager...")

html_files = []
for root, dirs, files in os.walk(os.path.join(project_root, 'public')):
    if 'backup' not in root:
        for file in files:
            if file.endswith('.html'):
                html_files.append(os.path.join(root, file))

replacements = {
    'checkAuth(': 'SessionManager.checkAuth(',
    'showError(': 'SessionManager.showError(',
    'showSuccess(': 'SessionManager.showSuccess(',
    'validateForm(': 'SessionManager.validateForm(',
    'formatDate(': 'SessionManager.formatDate(',
    'formatCurrency(': 'SessionManager.formatCurrency(',
    'getUrlParameter(': 'SessionManager.getUrlParameter('
}

updated = 0
for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    if original != content:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
        updated += 1
        print(f"✅ Updated {os.path.basename(html_file)}")

print(f"\n📊 Updated {updated} HTML files")
print("\n✅ Function consolidation complete!")
print("="*70)
