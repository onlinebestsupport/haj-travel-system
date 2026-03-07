@echo off
curl -X POST https://haj-web-app-production.up.railway.app/api/login -H "Content-Type: application/json" -d "{\"username\":\"admin1\",\"password\":\"admin123\"}"
pause