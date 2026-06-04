$ErrorActionPreference = "Stop"

$modelDir = Join-Path $PSScriptRoot "models"
$modelFile = Join-Path $modelDir "face_landmarker.task"

Write-Host "=== MediaPipe Face Landmarker Downloader ===" -ForegroundColor Cyan
Write-Host ""

if (!(Test-Path $modelDir)) {
    New-Item -ItemType Directory -Path $modelDir | Out-Null
}

if (Test-Path $modelFile) {
    $size = (Get-Item $modelFile).Length
    if ($size -gt 1000000) {
        Write-Host "Model already exists ($([math]::Round($size/1MB,2)) MB): $modelFile" -ForegroundColor Green
        Write-Host "Done!"
        exit 0
    }
}

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ProgressPreference = 'SilentlyContinue'

$url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"

Write-Host "Downloading from: $url" -ForegroundColor Yellow
Write-Host "Saving to: $modelFile" -ForegroundColor Yellow
Write-Host ""

try {
    Invoke-WebRequest -Uri $url -OutFile $modelFile -TimeoutSec 120
    $fileSize = (Get-Item $modelFile).Length
    if ($fileSize -gt 1000000) {
        Write-Host ""
        Write-Host "Download success!" -ForegroundColor Green
        Write-Host "Size: $([math]::Round($fileSize/1MB, 2)) MB"
    } else {
        Write-Host "File too small ($fileSize bytes), invalid." -ForegroundColor Yellow
        Remove-Item $modelFile -ErrorAction SilentlyContinue
    }
} catch {
    Write-Host "Download failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure your proxy is on, then run this script again." -ForegroundColor Cyan
    Write-Host "Or download manually in browser and save to:" -ForegroundColor Cyan
    Write-Host $modelFile -ForegroundColor Yellow
}
