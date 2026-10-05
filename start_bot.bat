@echo off
chcp 65001 > nul
echo ======================================================
echo    LINE Bot x Google Gemini AI 啟動小幫手
echo ======================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [提示] 尚未建立虛擬環境，正在初始化...
    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
)

echo [1/2] 正在啟動後端 Flask 伺服器 (Port 5000)...
start "LINE Bot Flask Server" cmd /k "chcp 65001 > nul && .\.venv\Scripts\python.exe app.py"

timeout /t 3 /nobreak > nul

echo [2/2] 正在啟動 Cloudflare 公開連線通道 (Tunnel)...
start "Cloudflare Tunnel" cmd /k "chcp 65001 > nul && "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url http://127.0.0.1:5000"

echo.
echo ======================================================
echo 服務已啟動！
echo 1. 請在「Cloudflare Tunnel」視窗中找到產生的 https://...trycloudflare.com 網址
echo 2. 在網址後加上 /callback，填入 LINE Developers 的 Webhook URL
echo ======================================================
pause
