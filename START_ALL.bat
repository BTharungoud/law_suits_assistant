@echo off
REM Law Assistant - Start Both Frontend and Backend

echo.
echo ===================================
echo 🚀 Law Assistant Startup
echo ===================================
echo.

REM Check if Node is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Node.js not found! Install from https://nodejs.org
    pause
    exit /b 1
)

REM Check if Python venv exists
if not exist "venv\Scripts\Activate.ps1" (
    echo ❌ Python venv not found! Run: python -m venv venv
    pause
    exit /b 1
)

echo ✅ All prerequisites found
echo.

REM Start Backend in new terminal
echo 📡 Starting Backend (FastAPI)...
start "Law Assistant - Backend" powershell -NoExit -Command "cd $([char]34)%CD%$([char]34); .\venv\Scripts\Activate.ps1; cd backend; python -m uvicorn app.main:app --reload"

REM Wait a moment for backend to start
timeout /t 3 /nobreak

REM Start Frontend in new terminal
echo 🎨 Starting Frontend (React)...
start "Law Assistant - Frontend" powershell -NoExit -Command "cd $([char]34)%CD%\frontend$([char]34)); npm run dev"

echo.
echo ===================================
echo ✅ Both services starting!
echo.
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8000
echo.
echo 📝 Close the terminal windows to stop
echo ===================================
echo.
pause
