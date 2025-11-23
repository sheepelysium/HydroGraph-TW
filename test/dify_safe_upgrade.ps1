# Dify 安全升級腳本 (含自動備份)

param(
    [switch]$SkipBackup = $false
)

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Dify 安全升級腳本" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

$DifyPath = "D:\Dify\docker"  # 請修改為您的路徑
$BackupPath = "D:\Dify\backups\$(Get-Date -Format 'yyyyMMdd_HHmmss')"

Set-Location $DifyPath

# 1. 備份 (除非指定跳過)
if (-not $SkipBackup) {
    Write-Host "`n[1/5] 創建備份..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null

    # 備份環境變數
    Copy-Item .env "$BackupPath\.env"

    # 備份 docker-compose.yml (如果有自定義)
    if (Test-Path docker-compose.override.yml) {
        Copy-Item docker-compose.override.yml "$BackupPath\"
    }

    Write-Host "  ✓ 備份已保存到: $BackupPath" -ForegroundColor Green
} else {
    Write-Host "`n[1/5] 跳過備份 (--SkipBackup)" -ForegroundColor Yellow
}

# 2. 停止服務
Write-Host "`n[2/5] 停止 Dify 服務..." -ForegroundColor Yellow
docker compose down

# 3. 拉取最新代碼
Write-Host "`n[3/5] 拉取最新代碼..." -ForegroundColor Yellow
git pull origin main

# 4. 拉取最新映像
Write-Host "`n[4/5] 拉取最新 Docker 映像..." -ForegroundColor Yellow
docker compose pull

# 5. 啟動服務
Write-Host "`n[5/5] 啟動 Dify 服務..." -ForegroundColor Yellow
docker compose up -d

# 等待服務啟動
Write-Host "`n等待服務啟動..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 檢查服務狀態
Write-Host "`n================================" -ForegroundColor Green
Write-Host "升級完成!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

Write-Host "`n服務狀態:" -ForegroundColor Cyan
docker compose ps

Write-Host "`n" -ForegroundColor Cyan
Write-Host "如需查看日誌: docker compose logs -f" -ForegroundColor White
Write-Host "如需回滾: 還原 $BackupPath 中的檔案" -ForegroundColor White

# 使用方法
Write-Host "`n使用說明:" -ForegroundColor Yellow
Write-Host "  有備份升級: .\dify_safe_upgrade.ps1" -ForegroundColor White
Write-Host "  跳過備份:   .\dify_safe_upgrade.ps1 -SkipBackup" -ForegroundColor White
