# Docker Start Script for Mistral OCR Test Suite
Write-Host "🚀 Starting Mistral OCR Test Suite in Docker..." -ForegroundColor Green

# Check if Docker is running
try {
    docker version | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Build and start the container
Write-Host "🔨 Building Docker image..." -ForegroundColor Yellow
docker-compose build

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Docker image built successfully" -ForegroundColor Green
    
    Write-Host "🚀 Starting container..." -ForegroundColor Yellow
    docker-compose up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Container started successfully!" -ForegroundColor Green
        Write-Host "🌐 Application will be available at: http://localhost:82" -ForegroundColor Cyan
        Write-Host "📊 Database: SQLite (persistent)" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "📋 Useful commands:" -ForegroundColor Yellow
        Write-Host "  - View logs: docker-compose logs -f" -ForegroundColor White
        Write-Host "  - Stop container: docker-compose down" -ForegroundColor White
        Write-Host "  - Restart container: docker-compose restart" -ForegroundColor White
    } else {
        Write-Host "❌ Failed to start container" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "❌ Failed to build Docker image" -ForegroundColor Red
    exit 1
}
