# Betteragy Installer for Windows (PowerShell)
# Usage: irm https://raw.githubusercontent.com/mncuchiinhuttt/betteragy/master/install.ps1 | iex

$ErrorActionPreference = 'Stop'

$RepoUrl = "https://github.com/mncuchiinhuttt/betteragy.git"
$InstallDir = Join-Path $env:USERPROFILE ".betteragy"
$BinDir = Join-Path $env:USERPROFILE ".local\bin"

Write-Host "   __         __   __                          " -ForegroundColor Cyan
Write-Host "  / /  ___   / /_ / /_ ___  ____ ___ _ ___ _ __ __" -ForegroundColor Cyan
Write-Host " / _ \/ -_) / __// __// -_)/ __// _ `// _ `// // /" -ForegroundColor Cyan
Write-Host "/_.__/\__/  \__/ \__/ \__//_/   \_,_/ \_, / \_, / " -ForegroundColor Cyan
Write-Host "                                     /___/ /___/  " -ForegroundColor Cyan
Write-Host "`n==> Installing Betteragy v1.0.0 for Windows...`n" -ForegroundColor Green

# 1. Try uv or pipx if available
$Installed = $false

if (Get-Command "uv" -ErrorAction SilentlyContinue) {
    Write-Host "[+] Detected uv. Installing via uv tool..." -ForegroundColor Green
    & uv tool install "git+$RepoUrl" --force
    $Installed = $true
} elseif (Get-Command "pipx" -ErrorAction SilentlyContinue) {
    Write-Host "[+] Detected pipx. Installing via pipx..." -ForegroundColor Green
    & pipx install "git+$RepoUrl" --force
    $Installed = $true
} else {
    # 2. Fallback to isolated venv
    Write-Host "[!] uv/pipx not found. Installing into isolated virtual environment..." -ForegroundColor Yellow
    
    $PythonCmd = $null
    $candidates = @("python", "py", "python3")
    foreach ($cand in $candidates) {
        if (Get-Command $cand -ErrorAction SilentlyContinue) {
            try {
                $ver = & $cand -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
                $parts = $ver.Split('.')
                if ([int]$parts[0] -eq 3 -and [int]$parts[1] -ge 11) {
                    $PythonCmd = $cand
                    break
                }
            } catch {}
        }
    }

    if (-not $PythonCmd) {
        Write-Host "[x] Error: Python 3.11+ is required to install Betteragy." -ForegroundColor Red
        Write-Host "    Please install Python from https://www.python.org/downloads/ (check 'Add python.exe to PATH') and retry."
        exit 1
    }

    Write-Host "[+] Using Python: $PythonCmd" -ForegroundColor Green
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    New-Item -ItemType Directory -Force -Path $BinDir | Out-Null

    $VenvPath = Join-Path $InstallDir "venv"
    if (-not (Test-Path $VenvPath)) {
        & $PythonCmd -m venv $VenvPath
    }

    $VenvPython = Join-Path $VenvPath "Scripts\python.exe"
    $VenvPip = Join-Path $VenvPath "Scripts\pip.exe"

    & $VenvPython -m pip install --upgrade pip --quiet
    & $VenvPip install "git+$RepoUrl" --quiet

    # Create batch wrapper scripts in ~/.local/bin
    $BetteragyCmdPath = Join-Path $BinDir "betteragy.cmd"
    $AgyCmdPath = Join-Path $BinDir "agy.cmd"
    $TargetExe = Join-Path $VenvPath "Scripts\betteragy.exe"

    Set-Content -Path $BetteragyCmdPath -Value "@echo off`r`n`"$TargetExe`" %*"
    Set-Content -Path $AgyCmdPath -Value "@echo off`r`n`"$TargetExe`" %*"

    # Ensure ~/.local/bin is in User PATH
    $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($UserPath -notlike "*$BinDir*") {
        Write-Host "[!] Adding $BinDir to User PATH..." -ForegroundColor Yellow
        $NewPath = if ($UserPath) { "$UserPath;$BinDir" } else { $BinDir }
        [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
        $env:Path = "$env:Path;$BinDir"
    }
    $Installed = $true
}

Write-Host "`n[ok] Betteragy v1.0.0 installed successfully!" -ForegroundColor Green
Write-Host "--------------------------------------------------------"
Write-Host "Quick Start:"
Write-Host "  betteragy           Launch Interactive TUI & Command Center" -ForegroundColor Cyan
Write-Host "  betteragy quota     View live AI model quotas & reset timers" -ForegroundColor Cyan
Write-Host "  betteragy proxy     Start transparent proxy with 429 auto-swap" -ForegroundColor Cyan
Write-Host "  betteragy --help    See all available commands" -ForegroundColor Cyan
Write-Host "--------------------------------------------------------`n"
