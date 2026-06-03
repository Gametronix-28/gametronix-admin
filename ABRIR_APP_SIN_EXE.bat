@echo off
title GAMETRONIX Admin Pro Taller Limpio
echo ==========================================
echo   INICIANDO GAMETRONIX ADMIN PRO
echo ==========================================
echo.
python -m pip install -r requirements.txt
python -m streamlit run app.py
pause
