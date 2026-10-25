@echo off
chcp 65001 > nul
echo ======================================================
echo    LINE Bot 本地模型聯網搜尋伺服器啟動小幫手
echo ======================================================
echo.

echo [1/2] 正在啟動本機搜尋伺服器 (Port 5001)...
start "Local Search Server" cmd /k "chcp 65001 > nul && .\.venv\Scripts\python.exe local_search_server.py"

timeout /t 3 /nobreak > nul

echo [2/2] 正在啟動 Cloudflare Tunnel (將 Port 5001 對外開放)...
start "Cloudflare Tunnel Local" cmd /k "chcp 65001 > nul && "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url http://127.0.0.1:5001"

echo.
echo ======================================================
echo 服務已啟動！
echo 1. 請在「Cloudflare Tunnel Local」視窗中找到產生的 https://...trycloudflare.com 網址
echo 2. 將此網址填入 Google Apps Script 的指令碼屬性 LOCAL_SERVER_URL
echo ======================================================
pause
