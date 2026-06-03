@echo off
title Crear EXE GAMETRONIX Admin Pro Taller Limpio
echo ==========================================
echo    CREANDO EXE GAMETRONIX ADMIN PRO
echo ==========================================
echo.
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m PyInstaller ^
--onefile ^
--name "GAMETRONIX_Admin_Pro" ^
--add-data "app.py;." ^
--add-data "config.py;." ^
--add-data "db;db" ^
--add-data "pages;pages" ^
--add-data "components;components" ^
--add-data "utils;utils" ^
--hidden-import streamlit ^
--hidden-import streamlit.web.cli ^
--hidden-import reportlab ^
--hidden-import pandas ^
--hidden-import openpyxl ^
--collect-all reportlab ^
launcher.py
echo.
echo LISTO. Archivo:
echo dist\GAMETRONIX_Admin_Pro_Taller_Limpio.exe
pause
