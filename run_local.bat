@echo off
echo ========================================================
echo   Starting RAG-QA (Streamlit)
echo ========================================================
echo.

cd /d "%~dp0"
set PYTHONPATH=backend;.

set "PYTHON_EXE=backend\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

echo [INFO] Starting application...
"%PYTHON_EXE%" -m streamlit run streamlit_app.py

pause
