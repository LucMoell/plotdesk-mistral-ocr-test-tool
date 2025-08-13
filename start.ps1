# Mistral OCR Test Suite - Windows Startup Script
# PowerShell Script zum Starten der Anwendung

Write-Host "🚀 Starting Mistral OCR Test Suite..." -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan

# Check if Python is installed
try {
    $pythonVersion = python --version
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.8+ and add it to PATH" -ForegroundColor Red
    exit 1
}

# Check if pip is available
try {
    pip --version | Out-Null
    Write-Host "✓ pip found" -ForegroundColor Green
} catch {
    Write-Host "✗ pip not found" -ForegroundColor Red
    exit 1
}

# Install dependencies if requirements.txt exists
if (Test-Path "requirements.txt") {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
}

# Create necessary directories
$directories = @("uploads", "test_files", "results", "logs")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "✓ Created directory: $dir" -ForegroundColor Green
    }
}

# Check if .env file exists
if (!(Test-Path ".env")) {
    Write-Host "⚠ No .env file found" -ForegroundColor Yellow
    Write-Host "Please copy env_example.txt to .env and configure your settings" -ForegroundColor Yellow
    Write-Host "Press any key to continue anyway..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Check if Redis is running
Write-Host "🔍 Checking Redis..." -ForegroundColor Yellow
try {
    $redisTest = redis-cli ping 2>$null
    if ($redisTest -eq "PONG") {
        Write-Host "✓ Redis is running" -ForegroundColor Green
    } else {
        throw "Redis not responding"
    }
} catch {
    Write-Host "✗ Redis is not running" -ForegroundColor Red
    Write-Host "Please start Redis manually or use Docker:" -ForegroundColor Yellow
    Write-Host "  docker run -d -p 6379:6379 redis:alpine" -ForegroundColor Cyan
    Write-Host "Press any key to continue anyway..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Start Celery worker in background
Write-Host "🔄 Starting Celery worker..." -ForegroundColor Yellow
$celeryJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    celery -A tasks worker --loglevel=info --concurrency=2
}

# Wait a moment for Celery to start
Start-Sleep -Seconds 3

# Check if Celery started successfully
if ($celeryJob.State -eq "Running") {
    Write-Host "✓ Celery worker started" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to start Celery worker" -ForegroundColor Red
    exit 1
}

# Start Flask application
Write-Host "🌐 Starting Flask application..." -ForegroundColor Yellow
Write-Host "Application will be available at: http://localhost:5000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the application" -ForegroundColor Yellow
Write-Host ""

try {
    python start.py
} catch {
    Write-Host "✗ Error starting Flask application: $_" -ForegroundColor Red
} finally {
    # Cleanup
    Write-Host "🛑 Stopping Celery worker..." -ForegroundColor Yellow
    Stop-Job $celeryJob
    Remove-Job $celeryJob
    Write-Host "✓ Cleanup completed" -ForegroundColor Green
}
