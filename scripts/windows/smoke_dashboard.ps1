param(
    [string]$BaseUrl = "http://127.0.0.1:8787",
    [string]$Index = "SPX"
)

$ErrorActionPreference = "Stop"

Write-Host "[1/4] Health..."
$health = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/health"
Write-Host "status=$($health.status) refresh=$($health.refresh_seconds) fast_mode=$($health.strategy_fast_mode)"

Write-Host "[2/4] Snapshot..."
$snapshot = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/dashboard/snapshot?index=$Index"
$hasStrategy = $null -ne $snapshot.strategy
$checksCount = 0
if ($hasStrategy -and $null -ne $snapshot.strategy.checks) {
    $checks = $snapshot.strategy.checks
    if ($checks -is [System.Management.Automation.PSCustomObject]) {
        $checksCount = ($checks | Get-Member -MemberType NoteProperty).Count
    } elseif ($checks -is [System.Collections.IDictionary]) {
        $checksCount = ($checks.Keys | Measure-Object).Count
    } elseif (($checks -is [System.Collections.IEnumerable]) -and -not ($checks -is [string])) {
        $checksCount = ($checks | Measure-Object).Count
    } else {
        $checksCount = 1
    }
}
Write-Host "has_strategy=$hasStrategy action=$($snapshot.strategy.tradeable.action) checks=$checksCount stale=$($snapshot.system.stale)"

Write-Host "[3/4] History..."
$history = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/dashboard/history?index=$Index&limit=5"
Write-Host "history_items=$($history.items.Count)"

Write-Host "[4/4] Debug..."
$debug = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/dashboard/debug?index=$Index"
Write-Host "recent_events=$($debug.recent_events.Count) recent_errors=$($debug.recent_errors.Count)"
Write-Host "server_log=$($debug.log_files.server_log)"
Write-Host "error_log=$($debug.log_files.error_log)"

Write-Host "Smoke check complete."
