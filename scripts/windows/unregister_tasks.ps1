param(
    [string]$Mode = "PAPER",
    [string]$Index = "SPX",
    [switch]$IncludeBlackbox
)

$ErrorActionPreference = "SilentlyContinue"

$tasks = @(
    "GammaMonitor-$Mode",
    "GammaScalper-$Index-$Mode"
)

if ($IncludeBlackbox) {
    $tasks += "GammaBlackbox-$Index"
}

foreach ($task in $tasks) {
    schtasks /Delete /TN $task /F | Out-Null
}

Write-Host "Removed tasks:"
$tasks | ForEach-Object { Write-Host "  $_" }

