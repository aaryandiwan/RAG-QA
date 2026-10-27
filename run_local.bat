@echo off
echo ========================================================
echo   Starting RAG-QA (100%% Python RAG with Streamlit)
echo ========================================================
echo.

cd /d "%~dp0"

if exist "backend\.venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment (backend\.venv)...
    call "backend\.venv\Scripts\activate.bat"
) else if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment (.venv)...
    call ".venv\Scripts\activate.bat"
) else (
    echo [WARNING] Virtual environment not found. Using system Python...
)

set PYTHONPATH=backend;.

echo [INFO] Launching Streamlit application on http://localhost:8501...
streamlit run streamlit_app.py

pause
