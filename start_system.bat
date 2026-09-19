@echo off
echo ======================================================================
echo Starting AI Food Demand Forecasting Engine for College Messes
echo ======================================================================

start "Mess Forecasting FastAPI Backend" cmd /k "cd /d %~dp0 && set PYTHONPATH=backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 3 /nobreak >nul

start "Mess Forecasting React Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo Backend URL:  http://127.0.0.1:8000
echo API Docs:     http://127.0.0.1:8000/docs
echo Frontend URL: http://localhost:5173
echo ======================================================================
pause
