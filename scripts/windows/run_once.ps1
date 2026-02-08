param(
    [string]$Index = "SPX",
    [string]$Mode = "PAPER"
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
Set-Location $RepoRoot

Write-Host "[1/3] Running blackbox snapshot..."
python run_blackbox_recorder.py $Index

Write-Host "[2/3] Running scalper..."
python run_scalper.py $Index $Mode

Write-Host "[3/3] Running monitor once (manual stop required)..."
python run_monitor.py $Mode

