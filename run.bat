@echo off
setlocal
cd /d "%~dp0"

rem Start backend API
start "FreightRate Backend" cmd /k "C:\Users\abhis\AppData\Local\Programs\Python\Python311\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

rem Start frontend dashboard
start "FreightRate Frontend" cmd /k "cd /d "%~dp0frontend" && npm.cmd run dev -- --hostname 0.0.0.0 --port 3000"

echo.
echo FreightRate Predictor is starting...
echo Backend:  http://localhost:8000/docs
echo Frontend: http://localhost:3000
echo.
echo Close the terminal windows when you are finished.
