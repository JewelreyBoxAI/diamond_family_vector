# Diamond Family Assistant - Staging Environment Manager (PowerShell)
#
# Quick commands for staging environment management on Windows
# Usage: .\staging-commands.ps1 [command]
# Commands: start, stop, restart, logs, status, clean

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("start", "stop", "restart", "logs", "status", "build", "test")]
    [string]$Command
)

Write-Host "🧪 Diamond Family Assistant - Staging Environment Manager" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan

switch ($Command) {
    "start" {
        Write-Host "🚀 Starting staging environment..." -ForegroundColor Green
        docker-compose -f docker-compose.staging.yml up -d
        Write-Host ""
        Write-Host "✅ Staging server running at: http://localhost:8001" -ForegroundColor Green
        Write-Host "📋 Chat widget: http://localhost:8001/widget" -ForegroundColor Yellow
        Write-Host "🔍 Health check: http://localhost:8001/" -ForegroundColor Yellow
    }
    
    "stop" {
        Write-Host "🛑 Stopping staging environment..." -ForegroundColor Red
        docker-compose -f docker-compose.staging.yml down
        Write-Host "✅ Staging environment stopped" -ForegroundColor Green
    }
    
    "restart" {
        Write-Host "🔄 Restarting staging environment..." -ForegroundColor Yellow
        docker-compose -f docker-compose.staging.yml down
        docker-compose -f docker-compose.staging.yml up -d
        Write-Host "✅ Staging environment restarted" -ForegroundColor Green
    }
    
    "logs" {
        Write-Host "📜 Staging logs (Ctrl+C to exit):" -ForegroundColor Cyan
        docker-compose -f docker-compose.staging.yml logs -f
    }
    
    "status" {
        Write-Host "📊 Staging environment status:" -ForegroundColor Cyan
        docker-compose -f docker-compose.staging.yml ps
    }
    
    "build" {
        Write-Host "🔨 Rebuilding staging environment..." -ForegroundColor Yellow
        docker-compose -f docker-compose.staging.yml up -d --build
        Write-Host "✅ Staging environment rebuilt and started" -ForegroundColor Green
    }
    
    "test" {
        Write-Host "🧪 Running staging tests..." -ForegroundColor Cyan
        Write-Host "🔍 Testing health endpoint..." -ForegroundColor Yellow
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8001/" -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ Health check passed" -ForegroundColor Green
            }
        } catch {
            Write-Host "❌ Health check failed: $($_.Exception.Message)" -ForegroundColor Red
        }
        
        Write-Host "🔍 Testing widget endpoint..." -ForegroundColor Yellow
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8001/widget" -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ Widget check passed" -ForegroundColor Green
            }
        } catch {
            Write-Host "❌ Widget check failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# Usage examples at the end
if ($Command -eq "help" -or $args -contains "--help") {
    Write-Host ""
    Write-Host "Usage: .\staging-commands.ps1 -Command <command>" -ForegroundColor White
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor White
    Write-Host "  start   - Start staging environment on port 8001" -ForegroundColor Gray
    Write-Host "  stop    - Stop staging environment" -ForegroundColor Gray
    Write-Host "  restart - Restart staging environment" -ForegroundColor Gray
    Write-Host "  logs    - View staging logs" -ForegroundColor Gray
    Write-Host "  status  - Check staging container status" -ForegroundColor Gray
    Write-Host "  build   - Rebuild and start staging environment" -ForegroundColor Gray
    Write-Host "  test    - Run basic health checks" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor White
    Write-Host "  .\staging-commands.ps1 -Command start   # Start staging" -ForegroundColor Gray
    Write-Host "  .\staging-commands.ps1 -Command test    # Test endpoints" -ForegroundColor Gray
    Write-Host "  .\staging-commands.ps1 -Command logs    # View logs" -ForegroundColor Gray
} 