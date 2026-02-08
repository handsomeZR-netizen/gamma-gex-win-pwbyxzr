param(
    [string]$Mode = "PAPER",
    [string]$Index = "SPX",
    [switch]$IncludeBlackbox
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
$PowerShellExe = (Get-Command powershell).Source

$monitorScript = Join-Path $RepoRoot "scripts\windows\start_monitor.ps1"
$scalperScript = Join-Path $RepoRoot "scripts\windows\start_scalper.ps1"
$blackboxScript = Join-Path $RepoRoot "scripts\windows\start_blackbox.ps1"

$monitorTask = "GammaMonitor-$Mode"
$scalperTask = "GammaScalper-$Index-$Mode"
$blackboxTask = "GammaBlackbox-$Index"

$monitorCmd = "`"$PowerShellExe`" -NoProfile -ExecutionPolicy Bypass -File `"$monitorScript`" -Mode $Mode"
$scalperCmd = "`"$PowerShellExe`" -NoProfile -ExecutionPolicy Bypass -File `"$scalperScript`" -Index $Index -Mode $Mode"
$blackboxCmd = "`"$PowerShellExe`" -NoProfile -ExecutionPolicy Bypass -File `"$blackboxScript`" -Index $Index"

# Start monitor on startup
schtasks /Create /TN $monitorTask /TR $monitorCmd /SC ONSTART /RL HIGHEST /F | Out-Null

# Weekday scalper run at 09:36 ET equivalent local time (adjust manually if needed)
schtasks /Create /TN $scalperTask /TR $scalperCmd /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 09:36 /RL HIGHEST /F | Out-Null

if ($IncludeBlackbox) {
    # Weekday blackbox snapshots every 5 minutes during session window
    schtasks /Create /TN $blackboxTask /TR $blackboxCmd /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 09:35 /RI 5 /DU 06:30 /RL HIGHEST /F | Out-Null
}

Write-Host "Registered tasks:"
Write-Host "  $monitorTask"
Write-Host "  $scalperTask"
if ($IncludeBlackbox) { Write-Host "  $blackboxTask" }

