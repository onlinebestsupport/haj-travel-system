@echo off
echo ========================================
echo    FORCE FIXING ALL MERGE CONFLICTS
echo ========================================
echo.

:: Get all files with potential merge conflicts
dir /s /b *.py *.html *.js *.css *.txt *.md *.json > all_files.txt

echo Processing files...
for /f "tokens=*" %%f in (all_files.txt) do (
    echo Checking %%f...
    powershell -Command "$content = Get-Content '%%f' -Raw; $content = $content -replace '<<<<<<< HEAD.*?=======.*?>>>>>>> [a-f0-9]+', '' -replace '=======', '' -replace '<<<<<<< HEAD', '' -replace '>>>>>>> [a-f0-9]+', ''; if ($content -match '<<<<<<<|=======|>>>>>>>') { Write-Host '  Still has conflicts: %%f' -ForegroundColor Red } else { Set-Content '%%f' -Value $content -NoNewline; Write-Host '  Cleaned: %%f' -ForegroundColor Green }"
)

del all_files.txt

echo.
echo ========================================
echo Merge conflict cleanup complete!
echo ========================================
pause