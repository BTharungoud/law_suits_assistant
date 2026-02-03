# Law Assistant - Start Both Frontend and Backend
# Usage: .\start-all.ps1

Write-Host "`n===================================" -ForegroundColor Cyan
Write-Host "🚀 Law Assistant Startup" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# Check if Node is installed
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
    Write-Host "❌ Node.js not found! Install from https://nodejs.org" -ForegroundColor Red
    exit 1
}

# Check if Python venv exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "❌ Python venv not found! Run: python -m venv venv" -ForegroundColor Red
    exit 1
}

Write-Host "✅ All prerequisites found" -ForegroundColor Green
Write-Host ""

# Start Backend
Write-Host "📡 Starting Backend (FastAPI on port 8000)..." -ForegroundColor Yellow
$backendScript = @'
    cd "LAW_ASSISTANT_PATH"
    .\venv\Scripts\Activate.ps1
    cd backend
    python -m uvicorn app.main:app --reload
'@
$backendScript = $backendScript.Replace("LAW_ASSISTANT_PATH", (Get-Location).Path)

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript `
    -WindowStyle Normal

# Wait for backend to start
Start-Sleep -Seconds 3

# Start Frontend
Write-Host "🎨 Starting Frontend (React on port 3000)..." -ForegroundColor Yellow
$frontendScript = @'
    cd "LAW_ASSISTANT_PATH\frontend"
    npm run dev
'@
$frontendScript = $frontendScript.Replace("LAW_ASSISTANT_PATH", (Get-Location).Path)

Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript `
    -WindowStyle Normal

# Display info
Write-Host "`n===================================" -ForegroundColor Cyan
Write-Host "✅ Both services starting!" -ForegroundColor Green
Write-Host "`nFrontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "`n📝 Close the terminal windows to stop" -ForegroundColor Yellow
Write-Host "===================================" -ForegroundColor Cyan
