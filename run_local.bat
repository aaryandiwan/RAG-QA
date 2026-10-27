@echo off
echo ========================================================
echo   Starting RAG-QA (100%% Python RAG with Streamlit)
echo ========================================================
echo.

cd /d "%~dp0"

set PYTHONPATH=backend;.

if exist "backend\.venv\Scripts\python.exe" (
    echo [INFO] Using virtual environment (backend\.venv)...
    "backend\.venv\Scripts\python.exe" -m streamlit run streamlit_app.py
) else if exist ".venv\Scripts\python.exe" (
    echo [INFO] Using virtual environment (.venv)...
    ".venv\Scripts\python.exe" -m streamlit run streamlit_app.py
) else (
    echo [INFO] Launching Streamlit via system python...
    python -m streamlit run streamlit_app.py
)

pause
