$ErrorActionPreference = "Stop"
Write-Host "=== COHERENCE SRE: WSL REPAIR PROTOCOL ===" -ForegroundColor Cyan

try {
    Write-Host "[1/3] Enabling Microsoft-Windows-Subsystem-Linux..." -ForegroundColor Yellow
    dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

    Write-Host "[2/3] Enabling VirtualMachinePlatform..." -ForegroundColor Yellow
    dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

    Write-Host "[3/3] Forcing WSL Update (Web Download)..." -ForegroundColor Yellow
    wsl --update --web-download

    Write-Host "SUCCESS. You MUST restart your computer now for these changes to apply." -ForegroundColor Green
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "Press ENTER to exit..."
Read-Host
