@echo off
echo ========================================================
echo   Starting DocChat Localhost (FastAPI + React Vite)
echo ========================================================

start "DocChat Backend (FastAPI)" cmd /k "cd /d d:\00-PROJECTS\rag-qa\backend && .venv\Scripts\python.exe -m uvicorn main:app --reload --port 8082"

timeout /t 2 >nul

start "DocChat Frontend (React)" cmd /k "cd /d d:\00-PROJECTS\rag-qa\frontend && npm run dev"

timeout /t 2 >nul

start http://localhost:5173

echo Done! Servers are running.
