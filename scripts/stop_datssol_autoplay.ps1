$repoRoot = Split-Path -Parent $PSScriptRoot
$launcherPath = Join-Path $repoRoot "logs\\live\\launcher.json"

if (-not (Test-Path $launcherPath)) {
    Write-Output '{"stopped":false,"reason":"launcher.json not found"}'
    exit 1
}

$launcher = Get-Content $launcherPath -Raw | ConvertFrom-Json
if (-not $launcher.pid) {
    Write-Output '{"stopped":false,"reason":"pid missing"}'
    exit 1
}

$process = Get-Process -Id $launcher.pid -ErrorAction SilentlyContinue
if ($null -eq $process) {
    Write-Output (@{
        stopped = $false
        reason = "process not running"
        pid = $launcher.pid
    } | ConvertTo-Json)
    exit 1
}

Stop-Process -Id $launcher.pid
@{
    stopped = $true
    pid = $launcher.pid
    stoppedAt = (Get-Date).ToUniversalTime().ToString("o")
} | ConvertTo-Json
