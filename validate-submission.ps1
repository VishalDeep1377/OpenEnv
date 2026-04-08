# validate-submission.ps1 — OpenEnv Submission Validator (Windows/PowerShell)
param(
    [string]$PingUrl = "https://vishaldeep1022-exec-env-assistant.hf.space",
    [string]$RepoDir = "."
)

# Colors and configuration
$ErrorActionPreference = "Stop"
$DockerBuildTimeout = 600
$Green = "`e[0;32m"
$Red = "`e[0;31m"
$Yellow = "`e[1;33m"
$Reset = "`e[0m"

function Log-Message($msg) { Write-Host "[$((Get-Date).ToString('HH:mm:ss'))] $msg" }
function Pass-Check($msg) { Write-Host "[$((Get-Date).ToString('HH:mm:ss'))] ${Green}PASSED${Reset} -- $msg" }
function Fail-Check($msg) { Write-Host "[$((Get-Date).ToString('HH:mm:ss'))] ${Red}FAILED${Reset} -- $msg" }
function Hint-Message($msg) { Write-Host "  ${Yellow}Hint:${Reset} $msg" }

Write-Host "`n========================================"
Write-Host "  OpenEnv Submission Validator (PS)"
Write-Host "========================================"
Log-Message "Repo: $RepoDir"
Log-Message "Ping URL: $PingUrl`n"

# Step 1: Ping HF Space
Log-Message "Step 1/3: Pinging HF Space ($PingUrl/reset) ..."
try {
    # Use -UseBasicParsing to avoid IE engine dependencies on some Windows versions
    $response = Invoke-WebRequest -Method Post -Uri "$PingUrl/reset" -ContentType "application/json" -Body '{}' -TimeoutSec 30 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Pass-Check "HF Space is live and responds to /reset"
    } else {
        Fail-Check "HF Space /reset returned HTTP $($response.StatusCode)"
        exit 1
    }
} catch {
    Fail-Check "HF Space not reachable: $($_.Exception.Message)"
    Hint-Message "Check your network connection and that the Space is running."
    exit 1
}

# Step 2: Docker Build
Log-Message "Step 2/3: Running docker build ..."
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "${Yellow}WARNING: Docker not found in PATH. Skipping docker build validation step.${Reset}"
    Hint-Message "Install Docker if you want to verify the container build locally: https://docs.docker.com/get-docker/"
} else {
    $dockerContext = "."
    if (Test-Path "$RepoDir/Dockerfile") { $dockerContext = $RepoDir }
    elseif (Test-Path "$RepoDir/server/Dockerfile") { $dockerContext = "$RepoDir/server" }
    else {
        Fail-Check "No Dockerfile found in repo root or server/ directory"
        exit 1
    }
    
    Log-Message "Found Dockerfile in $dockerContext. Building..."
    docker build $dockerContext
    if ($LASTEXITCODE -eq 0) {
        Pass-Check "Docker build succeeded"
    } else {
        Fail-Check "Docker build failed"
        exit 1
    }
}

# Step 3: OpenEnv Validate
Log-Message "Step 3/3: Running openenv validate ..."
$openenv = "$RepoDir\.venv\Scripts\openenv.exe"
if (-not (Test-Path $openenv)) {
    $openenv = "openenv" # fallback to path
}

if (-not (Get-Command $openenv -ErrorAction SilentlyContinue)) {
    Fail-Check "openenv command not found"
    Hint-Message "Install it: pip install openenv-core or make sure your .venv is active."
    exit 1
}

Log-Message "Using openenv: $openenv"
& $openenv validate
if ($LASTEXITCODE -eq 0) {
    Pass-Check "openenv validate passed"
} else {
    Fail-Check "openenv validate failed"
    exit 1
}

Write-Host "`n========================================"
Write-Host "${Green}  Checks complete!${Reset}"
Write-Host "========================================`n"
