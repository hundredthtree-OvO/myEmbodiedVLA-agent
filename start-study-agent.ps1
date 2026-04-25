$ErrorActionPreference = "Stop"
$workspace = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $workspace

if (-not $env:UV_CACHE_DIR) {
    $env:UV_CACHE_DIR = Join-Path $workspace ".tmp\uv-cache"
}

if (-not $env:PYTHONPATH) {
    $env:PYTHONPATH = Join-Path $workspace "src"
}

uv run python study_agent_cli.py tui
