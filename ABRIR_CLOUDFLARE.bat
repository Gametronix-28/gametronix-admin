@echo off
title GAMETRONIX Admin Pro - Cloudflare Tunnel
echo ==========================================
echo   INICIANDO GAMETRONIX + CLOUDFLARE
echo ==========================================
echo.
echo Iniciando Streamlit...
start "Streamlit" cmd /c "python -m streamlit run app.py --server.headless=true --browser.gatherUsageStats=false"
timeout /t 5 /nobreak >nul
echo Iniciando Cloudflare Tunnel...
echo.
echo ==========================================
echo   COPIA ESTE LINK PARA TUS DISPOSITIVOS:
echo ==========================================
echo.
%LOCALAPPDATA%\cloudflared\cloudflared.exe tunnel --url http://localhost:8501
pause
