import os
import re

print("=" * 70)
print("🔧 ULTIMATE FIX SCRIPT - HAJ TRAVEL SYSTEM")
print("=" * 70)

def fix_payments_py():
    """Fix the incomplete payments.py file"""
    payments_file = "app/routes/payments.py"
    
    if not os.path.exists(payments_file):
        print(f"❌ {payments_file} not found!")
        return False
    
    with open(payments_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if the file is cut off
    if "get_traveler_payments" in content and "cursor.execute('''" in content and "SELECT" in content and "'''" not in content[content.find("cursor.execute('''"):]:
        print(" Found incomplete get_traveler_payments function - fixing...")
        
        # Find the position of the incomplete function
        start_marker = "@bp.route('/traveler/<int:traveler_id>', methods=['GET'])"
        if start_marker in content:
            start_pos = content.find(start_marker)
            # Find the next function or end of file
            next_func = content.find("@bp.route", start_pos + len(start_marker))
            if next_func == -1:
                next_func = len(content)
            
            # Replace with complete function - using simple string concatenation to avoid indentation issues
            complete_function = '''@bp.route('/traveler/<int:traveler_id>', methods=['GET'])
def get_traveler_payments(traveler_id):
    """Get payments for a specific traveler with enhanced details"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn, cursor = get_db()
    try:
        cursor.execute(
            "SELECT p.*, b.batch_name, "
            "CASE WHEN p.status = 'pending' AND p.due_date < CURRENT_DATE THEN 'overdue' ELSE p.status END as current_status "
            "FROM payments p JOIN batches b ON p.batch_id = b.id "
            "WHERE p.traveler_id = %s ORDER BY p.payment_date DESC",
            (traveler_id,)
        )
        payments = cursor.fetchall()

        cursor.execute(
            "SELECT COALESCE(SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END), 0) as total_paid, "
            "COALESCE(SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END), 0) as total_pending, "
            "COUNT(CASE WHEN status = 'completed' THEN 1 END) as paid_count, "
            "COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count, "
            "MAX(CASE WHEN status = 'completed' THEN payment_date END) as last_payment_date "
            "FROM payments WHERE traveler_id = %s",
            (traveler_id,)
        )
        totals = cursor.fetchone()

        cursor.execute(
            "SELECT COUNT(*) as overdue_count, COALESCE(SUM(amount), 0) as overdue_amount "
            "FROM payments WHERE traveler_id = %s AND status = 'pending' AND due_date < CURRENT_DATE",
            (traveler_id,)
        )
        overdue = cursor.fetchone()
        release_db(conn, cursor)

        return jsonify({
            'success': True,
            'payments': [dict(p) for p in payments],
            'totals': dict(totals) if totals else {},
            'overdue': dict(overdue) if overdue else {'overdue_count': 0, 'overdue_amount': 0}
        })

    except Exception as e:
        release_db(conn, cursor)
        return jsonify({'success': False, 'error': str(e)}), 500
'''
            content = content[:start_pos] + complete_function + content[next_func:]
            
            with open(payments_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(" Fixed payments.py")
            return True
    
    print(" payments.py looks complete, no fix needed")
    return True

def fix_server_py():
    """Add users and backup to server.py imports and registrations"""
    server_file = "app/server.py"
    
    if not os.path.exists(server_file):
        print(f"❌ {server_file} not found!")
        return False
    
    with open(server_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    changes_made = False
    
    # Fix imports line
    import_line_pattern = r'from app\.routes import (.*?)$'
    import_match = re.search(import_line_pattern, content, re.MULTILINE)
    
    if import_match:
        imports = import_match.group(1)
        if 'users' not in imports or 'backup' not in imports:
            new_imports = imports.rstrip()
            if not new_imports.endswith(','):
                new_imports += ','
            if 'users' not in imports:
                new_imports += ' users'
            if 'backup' not in imports:
                new_imports += ', backup' if 'users' in imports else ' backup'
            
            content = content.replace(import_match.group(0), f"from app.routes import {new_imports}")
            print(" Added users/backup to imports")
            changes_made = True
    
    # Add blueprint registrations if missing
    if 'app.register_blueprint(users.bp)' not in content:
        # Find the last blueprint registration
        last_reg = content.rfind('app.register_blueprint(')
        if last_reg != -1:
            next_newline = content.find('\n', last_reg)
            insert_pos = next_newline + 1
            content = content[:insert_pos] + 'app.register_blueprint(users.bp)\n' + content[insert_pos:]
            print(" Added users blueprint registration")
            changes_made = True
    
    if 'app.register_blueprint(backup.bp)' not in content:
        if 'app.register_blueprint(users.bp)' in content:
            last_reg = content.rfind('app.register_blueprint(users.bp)')
        else:
            last_reg = content.rfind('app.register_blueprint(')
        
        if last_reg != -1:
            next_newline = content.find('\n', last_reg)
            insert_pos = next_newline + 1
            content = content[:insert_pos] + 'app.register_blueprint(backup.bp)\n' + content[insert_pos:]
            print(" Added backup blueprint registration")
            changes_made = True
    
    if changes_made:
        with open(server_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(" Updated server.py")
    else:
        print(" server.py already has users/backup registered")
    
    return True

def fix_invoices_html():
    """Add SessionManager.initPage to invoices.html"""
    invoices_file = "public/admin/invoices.html"
    
    if not os.path.exists(invoices_file):
        print(f"❌ {invoices_file} not found!")
        return False
    
    with open(invoices_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'SessionManager.initPage' not in content:
        # Add init script before </body>
        init_script = '''
<script>
// Initialize page with session check
document.addEventListener('DOMContentLoaded', function() {
    if (typeof SessionManager !== 'undefined' && SessionManager.initPage) {
        SessionManager.initPage(function() {
            console.log('Invoices page initialized');
            if (typeof loadInvoicesData === 'function') {
                loadInvoicesData();
            }
        });
    }
});
</script>
'''
        if '</body>' in content:
            content = content.replace('</body>', init_script + '\n</body>')
            with open(invoices_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(" Added SessionManager.initPage to invoices.html")
            return True
    
    print(" invoices.html already has SessionManager.initPage")
    return True

def check_api_files():
    """Verify all API files exist"""
    api_files = {
        'users.py': 'app/routes/users.py',
        'backup.py': 'app/routes/backup.py',
        'reports.py': 'app/routes/reports.py',
        'payments.py': 'app/routes/payments.py',
    }
    
    print("\n📁 Checking API files:")
    all_ok = True
    for name, path in api_files.items():
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"  ✅ {name} exists ({size} bytes)")
        else:
            print(f"  ❌ {name} MISSING at {path}")
            all_ok = False
    
    return all_ok

def main():
    print("\n📋 STEP 1: Fixing payments.py...")
    fix_payments_py()
    
    print("\n📋 STEP 2: Fixing server.py imports...")
    fix_server_py()
    
    print("\n📋 STEP 3: Fixing invoices.html...")
    fix_invoices_html()
    
    print("\n📋 STEP 4: Verifying all files...")
    check_api_files()
    
    print("\n" + "=" * 70)
    print("🚀 DEPLOYMENT COMMANDS")
    print("=" * 70)
    print("\nRun these commands to deploy the fixes:")
    print("  git add app/routes/payments.py")
    print("  git add app/server.py")
    print("  git add public/admin/invoices.html")
    print('  git commit -m "Fix: Complete payments.py, register users/backup, add SessionManager to invoices"')
    print("  git push origin main")
    
    print("\n" + "=" * 70)
    print("✅ FIXES COMPLETE! Run the deployment commands above.")
    print("=" * 70)

if __name__ == "__main__":
    main()