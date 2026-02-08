param(
    [string]$Index = "SPX",
    [string]$Mode = "PAPER",
    [string]$PinOverride = "",
    [string]$PriceOverride = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
Set-Location $RepoRoot

$logDir = Join-Path $RepoRoot "data\logs"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

$envFile = Join-Path $RepoRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $parts = $line.Split("=", 2)
            [Environment]::SetEnvironmentVariable($parts[0], $parts[1], "Process")
        }
    }
}

$args = @("run_scalper.py", $Index, $Mode)
if ($PinOverride) { $args += $PinOverride }
if ($PriceOverride) { $args += $PriceOverride }

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = Join-Path $logDir "scalper_${Index}_${Mode}_$stamp.log"

& python @args *>> $logPath
exit $LASTEXITCODE

