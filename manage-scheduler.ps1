# Euraxess 一体化应用管理脚本 (Windows PowerShell)

param(
    [Parameter(Position=0)]
    [string]$Action
)

Write-Host "=== Euraxess 一体化应用管理 ===" -ForegroundColor Green
Write-Host "定时爬取 + 实时Web界面" -ForegroundColor Cyan
Write-Host ""

switch ($Action.ToLower()) {
    "start" {
        Write-Host "🚀 启动一体化服务..." -ForegroundColor Yellow
        Write-Host "包含: 定时爬虫 + Streamlit Web界面" -ForegroundColor White
        docker-compose up -d
        Write-Host ""
        Write-Host "✅ 服务已启动!" -ForegroundColor Green
        Write-Host "� 定时爬取: 每天UTC 18:00 (世界时间下午6点)" -ForegroundColor Cyan
        Write-Host "🌐 Web界面: http://localhost:8501" -ForegroundColor Cyan
    }
    
    "stop" {
        Write-Host "🛑 停止所有服务..." -ForegroundColor Yellow
        docker-compose down
        Write-Host "✅ 服务已停止" -ForegroundColor Green
    }
    
    "status" {
        Write-Host "📋 服务状态:" -ForegroundColor Yellow
        docker-compose ps
    }
    
    "logs" {
        Write-Host "📝 查看应用日志:" -ForegroundColor Yellow
        docker-compose logs -f
    }
    
    "run-now" {
        Write-Host "⚡ 立即运行爬虫一次..." -ForegroundColor Yellow
        docker-compose --profile manual up euraxess-scraper-once
    }
    
    "schedule" {
        Write-Host "⏰ 定时任务信息:" -ForegroundColor Yellow
        Write-Host "运行时间: 每天 UTC 18:00 (世界时间下午6点)" -ForegroundColor Cyan
        Write-Host "当前UTC时间: $((Get-Date).ToUniversalTime())" -ForegroundColor Cyan
        
        $now = (Get-Date).ToUniversalTime()
        $today6pm = (Get-Date -Hour 18 -Minute 0 -Second 0).ToUniversalTime()
        
        if ($now -lt $today6pm) {
            Write-Host "下次运行时间: $today6pm" -ForegroundColor Cyan
        } else {
            $tomorrow6pm = $today6pm.AddDays(1)
            Write-Host "下次运行时间: $tomorrow6pm" -ForegroundColor Cyan
        }
    }
    
    "build" {
        Write-Host "🔨 重新构建镜像..." -ForegroundColor Yellow
        docker-compose build --no-cache
        Write-Host "✅ 镜像构建完成" -ForegroundColor Green
    }
    
    default {
        Write-Host "用法: .\manage-scheduler.ps1 {start|stop|status|logs|run-now|schedule|build}" -ForegroundColor Red
        Write-Host ""
        Write-Host "命令说明:" -ForegroundColor Yellow
        Write-Host "  start     - 启动一体化服务 (定时爬虫 + Web界面)" -ForegroundColor White
        Write-Host "  stop      - 停止所有服务" -ForegroundColor White
        Write-Host "  status    - 查看服务状态" -ForegroundColor White
        Write-Host "  logs      - 查看应用日志" -ForegroundColor White
        Write-Host "  run-now   - 立即运行爬虫一次" -ForegroundColor White
        Write-Host "  schedule  - 查看定时信息" -ForegroundColor White
        Write-Host "  build     - 重新构建Docker镜像" -ForegroundColor White
        Write-Host ""
        Write-Host "🎯 一体化功能:" -ForegroundColor Cyan
        Write-Host "  - 自动定时爬取: 每天UTC 18:00" -ForegroundColor White
        Write-Host "  - 实时Web界面: http://localhost:8501" -ForegroundColor White
        Write-Host "  - 数据持久化: ./output/ 目录" -ForegroundColor White
    }
}