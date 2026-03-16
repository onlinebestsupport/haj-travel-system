@echo off
echo 📁 Git Status:
git status

echo.
set /p files="Enter files to add (or press Enter for all): "
if "%files%"=="" (git add .) else (git add %files%)

echo.
set /p message="Enter commit message: "
git commit -m "%message%"

echo.
git push origin main
pause