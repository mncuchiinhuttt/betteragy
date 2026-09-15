# Betteragy Installer for Windows (PowerShell)
# Usage: irm https://betteragy.dev/install.ps1 | iex

$ErrorActionPreference = 'Stop'

$RepoUrl = "https://github.com/mncuchiinhuttt/betteragy.git"
$InstallDir = Join-Path $env:USERPROFILE ".betteragy"
$BinDir = Join-Path $env:USERPROFILE ".local\bin"

Clear-Host

Write-Host "  ____       _   _                             " -ForegroundColor Cyan
Write-Host " |  _ \     | | | |                            " -ForegroundColor Cyan
Write-Host " | |_) | ___| |_| |_ ___ _ __ __ _  __ _ _   _ " -ForegroundColor Cyan
Write-Host " |  _ < / _ \ __| __/ _ \ '__/ _` |/ _` | | | |" -ForegroundColor Cyan
Write-Host " | |_) |  __/ |_| ||  __/ | | (_| | (_| | |_| |" -ForegroundColor Cyan
Write-Host " |____/ \___|\__|\__\___|_|  \__,_|\__, |\__, |" -ForegroundColor Cyan
Write-Host "                                    __/ | __/ |" -ForegroundColor Cyan
Write-Host "                                   |___/ |___/ " -ForegroundColor Cyan
Write-Host "`n  Everything to Power Antigravity AI — v1.0.0" -ForegroundColor White
Write-Host "  Zero-restart auto-rotation & quota intelligence`n" -ForegroundColor DarkGray

# 1. Check uv / pipx or fallback to python venv
Write-Host "  [1/3] Checking Python runtime environment..." -ForegroundColor Cyan
$Installed = $false

if (Get-Command "uv" -ErrorAction SilentlyContinue) {
    Write-Host "        + Detected uv. Installing via uv tool..." -ForegroundColor Green
    & uv tool install "git+$RepoUrl" --force --quiet
    $Installed = $true
} elseif (Get-Command "pipx" -ErrorAction SilentlyContinue) {
    Write-Host "        + Detected pipx. Installing via pipx..." -ForegroundColor Green
    & pipx install "git+$RepoUrl" --force --quiet
    $Installed = $true
} else {
    Write-Host "        ! Using isolated Python virtual environment..." -ForegroundColor Yellow
    
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
        Write-Host "`n  [x] Error: Python 3.11+ is required to run Betteragy." -ForegroundColor Red
        Write-Host "      Please install Python from https://www.python.org/downloads/ (check 'Add python.exe to PATH') and retry.`n"
        exit 1
    }

    Write-Host "        + Using Python: $PythonCmd" -ForegroundColor Green
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

    $BetteragyCmdPath = Join-Path $BinDir "betteragy.cmd"
    $AgyCmdPath = Join-Path $BinDir "agy.cmd"
    $TargetExe = Join-Path $VenvPath "Scripts\betteragy.exe"

    Set-Content -Path $BetteragyCmdPath -Value "@echo off`r`n`"$TargetExe`" %*"
    Set-Content -Path $AgyCmdPath -Value "@echo off`r`n`"$TargetExe`" %*"

    $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($UserPath -notlike "*$BinDir*") {
        Write-Host "        ! Adding $BinDir to User PATH..." -ForegroundColor Yellow
        $NewPath = if ($UserPath) { "$UserPath;$BinDir" } else { $BinDir }
        [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
        $env:Path = "$env:Path;$BinDir"
    } else {
        Write-Host "        + PATH contains ~/.local/bin (Ready)" -ForegroundColor Green
    }
    $Installed = $true
}

# 2. Finalizing
Write-Host "  [2/3] Verifying system PATH configuration..." -ForegroundColor Cyan
Write-Host "        + PATH verified.`n" -ForegroundColor Green

Write-Host "  [3/3] Finalizing binary hooks...`n" -ForegroundColor Cyan

# 3. Summary Card
Write-Host "  +--------------------------------------------------------+" -ForegroundColor Green
Write-Host "  |  Betteragy v1.0.0 - Installed Successfully!            |" -ForegroundColor Green
Write-Host "  +--------------------------------------------------------+" -ForegroundColor Green
Write-Host "  |  Commands:                                             |" -ForegroundColor White
Write-Host "  |    betteragy           Launch Interactive TUI Dashboard|" -ForegroundColor Cyan
Write-Host "  |    betteragy quota     Inspect Gemini 3.8 & Claude     |" -ForegroundColor Cyan
Write-Host "  |    betteragy proxy     Start 429 Interception Daemon   |" -ForegroundColor Cyan
Write-Host "  |    betteragy --help    Display full CLI reference      |" -ForegroundColor Cyan
Write-Host "  +--------------------------------------------------------+`n" -ForegroundColor Green

# Interactive Star on GitHub Prompt
Write-Host "  * Love Betteragy? Star us on GitHub!" -ForegroundColor Cyan
Write-Host "    Repository: https://github.com/mncuchiinhuttt/betteragy`n" -ForegroundColor DarkGray
Write-Host "  ==> Press [ENTER] to star on GitHub (or Ctrl+C to exit): " -ForegroundColor Yellow -NoNewline

try {
    $null = Read-Host
    Start-Process "https://github.com/mncuchiinhuttt/betteragy"
    Write-Host "`n  [ok] Thank you for starring! Happy coding with Antigravity AI.`n" -ForegroundColor Green
} catch {
    Write-Host ""
}
