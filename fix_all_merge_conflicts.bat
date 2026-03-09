@echo off
echo ========================================
echo    FIXING ALL MERGE CONFLICTS
echo ========================================
echo.

:: List of files with merge conflicts (from your diagnostic)
set FILES=^
auto_fix_all.py ^
auto_fix_production.py ^
CLEANUP_REPORT.txt ^
complete_fix.py ^
complete_system_diagnostic.py ^
complete_system_test.py ^
DUPLICATE_FUNCTIONS_REPORT.txt ^
final_5_fixes.py ^
final_complete_fix.py ^
final_fixes.py ^
find_all_errors.py ^
fix_all_errors.py ^
fix_all_final.py ^
fix_file_names.py ^
fix_invoices_pagination.py ^
fix_merge_conflicts.py ^
fix_payments_pagination.py ^
fix_receipts_pagination.py ^
fix_remaining_8.py ^
fix_remaining_issues.py ^
fix_reports_enhancements.py ^
fix_travelers_pagination.py ^
fix_users_global_scope.py ^
login_page.html ^
railway_check.py ^
railway_check_override.py ^
railway_deploy_final.py ^
run_all_tests.py ^
test_admin_css.py ^
test_corner_cases_production.py ^
test_css_references.py ^
test_file_mismatches.py ^
test_production_railway.py ^
test_suite_complete.py ^
ultimate_final_fix.py ^
ultimate_fix.py ^
ultimate_fix_all.py ^
app\database.py ^
app\middleware.py ^
app\server.py ^
app\routes\admin.py ^
app\routes\company.py ^
app\routes\reports.py ^
public\admin.login.html ^
public\style.css ^
public\traveler_dashboard.html ^
public\admin\admin-style.css ^
public\admin\backup.html ^
public\admin\batches.html ^
public\admin\dashboard.html ^
public\admin\debug_users.html ^
public\admin\email.html ^
public\admin\frontpage.html ^
public\admin\invoices.html ^
public\admin\payments.html ^
public\admin\receipts.html ^
public\admin\reports.html ^
public\admin\travelers.html ^
public\admin\users.html ^
public\admin\whatsapp.html ^
public\admin\js\session-manager.js

for %%f in (%FILES%) do (
    if exist "%%f" (
        echo Processing %%f...
        powershell -Command "(Get-Content '%%f') -replace '<<<<<<< HEAD.*?=======.*?>>>>>>> [a-f0-9]+', '' -replace '=======', '' -replace '<<<<<<< HEAD', '' -replace '>>>>>>> [a-f0-9]+', '' | Set-Content '%%f'"
    ) else (
        echo Skipping %%f - not found
    )
)

echo.
echo ========================================
echo Merge conflict cleanup complete!
echo ========================================
pause