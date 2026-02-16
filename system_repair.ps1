$ErrorActionPreference = "Continue"
Write-Host "=== COHERENCE SRE: SYSTEM INTEGRITY REPAIR ===" -ForegroundColor Cyan
Write-Host "Targeting 'Class Not Registered' (REGDB_E_CLASSNOTREG) error." -ForegroundColor Yellow
Write-Host "This process addresses deep system corruption." -ForegroundColor Yellow

# 1. System File Checker
Write-Host "`n[1/4] Running System File Checker (SFC)..." -ForegroundColor Cyan
sfc /scannow

# 2. DISM RestoreHealth
Write-Host "`n[2/4] Running DISM Image Repair..." -ForegroundColor Cyan
dism /online /cleanup-image /restorehealth

# 3. Re-register WSL Service (Attempt)
Write-Host "`n[3/4] Attempting to re-register WSL Service..." -ForegroundColor Cyan
wsl --status 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "WSL still reporting errors. Attempting update..." -ForegroundColor Yellow
    wsl --update
} else {
    Write-Host "WSL appears responsive." -ForegroundColor Green
}

Write-Host "`n=== OPERATION COMPLETE ===" -ForegroundColor Green
Write-Host "If SFC or DISM reported fixing files, please REBOOT."
Write-Host "Press ENTER to exit..."
Read-Host
