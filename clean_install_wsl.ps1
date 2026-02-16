$ErrorActionPreference = "Continue"
Write-Host "=== COHERENCE SRE: WSL CLEAN SLATE PROTOCOL ===" -ForegroundColor Cyan
Write-Host "Target: Remove corrupted Store App registration." -ForegroundColor Yellow

try {
    Write-Host "[1/3] Identifying WSL Packages..."
    $apps = Get-AppxPackage -AllUsers *WindowsSubsystemforLinux*
    if ($apps) {
        Write-Host "Found $($apps.Count) package(s). Removing..." -ForegroundColor Yellow
        $apps | Remove-AppxPackage -AllUsers
        Write-Host "Removal Complete." -ForegroundColor Green
    }
    else {
        Write-Host "No existing WSL Appx packages found. (This causes the 'Class Not Registered' if the feature expects it)" -ForegroundColor Yellow
    }

    Write-Host "`n[2/3] Installing fresh WSL from Web..." -ForegroundColor Cyan
    # Using the direct update command which fetches the latest store bundle
    wsl --update --web-download
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`nSUCCESS. WSL Should be operational." -ForegroundColor Green
        wsl --status
    }
    else {
        Write-Host "`nStandard update failed. Attempting MSI repair..." -ForegroundColor Red
        # Fallback to direct download if wsl command is still failing
        $dwn = "$env:USERPROFILE\Downloads\wsl_update.msi"
        Invoke-WebRequest -Uri "https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi" -OutFile $dwn
        Start-Process msiexec.exe -ArgumentList "/i `"$dwn`" /quiet" -Wait
        Write-Host "MSI Installed. Checking status..."
        wsl --status
    }

}
catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nPress ENTER to exit..."
Read-Host
