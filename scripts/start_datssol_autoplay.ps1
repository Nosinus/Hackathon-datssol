param(
    [double]$Hours = 8.0,
    [string]$SessionName = "autoplay",
    [int]$SummaryEvery = 25,
    [int]$MaxConsecutiveErrors = 20,
    [switch]$WatchOnly
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$liveDir = Join-Path $repoRoot "logs\\live"
New-Item -ItemType Directory -Force -Path $liveDir | Out-Null

$stdoutPath = Join-Path $liveDir "autoplay_stdout.log"
$stderrPath = Join-Path $liveDir "autoplay_stderr.log"

$arguments = @(
    "-m", "scripts.cli",
    "datssol", "autoplay",
    "--hours", "$Hours",
    "--session-name", $SessionName,
    "--summary-every", "$SummaryEvery",
    "--max-consecutive-errors", "$MaxConsecutiveErrors"
)

if ($WatchOnly.IsPresent) {
    $arguments += "--watch-only"
}

$env:PYTHONPATH = "src"
$process = Start-Process `
    -FilePath "python" `
    -ArgumentList $arguments `
    -WorkingDirectory $repoRoot `
    -RedirectStandardOutput $stdoutPath `
    -RedirectStandardError $stderrPath `
    -PassThru

$payload = [ordered]@{
    pid = $process.Id
    launchedAt = (Get-Date).ToUniversalTime().ToString("o")
    repoRoot = $repoRoot
    stdout = $stdoutPath
    stderr = $stderrPath
    arguments = $arguments
}

$payload | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $liveDir "launcher.json")
$payload | ConvertTo-Json -Depth 6
