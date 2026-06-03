@echo off
title GAMETRONIX Admin Pro - Ngrok Cloud
echo ==========================================
echo   INICIANDO GAMETRONIX + NGROK
echo ==========================================
echo.
echo Iniciando Streamlit en puerto 8501...
start "Streamlit" cmd /c "python -m streamlit run app.py --server.headless=true --browser.gatherUsageStats=false"
timeout /t 5 /nobreak >nul
echo Iniciando ngrok...
start "Ngrok" cmd /c "C:\Users\Brayam\AppData\Local\ngrok\ngrok.exe http 8501 --url=brayam-gametronix.ngrok-free.app 2>&1"
echo.
echo ==========================================
echo   ABRE ESTE LINK EN TUS DISPOSITIVOS:
echo   https://brayam-gametronix.ngrok-free.app
echo ==========================================
echo.
pause
