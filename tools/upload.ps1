<#
  Upload helper for Pico (Windows).
  Forwards flags to tools\upload_to_pico.py and bootstraps .venv if needed.

  Examples:
    .\tools\upload.ps1 --clean --yes --reset
    .\tools\upload.ps1 --port COM3 --dry-run
    .\tools\upload.ps1 --list
    .\tools\upload.ps1 --src-root F:\path\to\repo
#>

param(
  [string]$Port = "",
  [switch]$Clean,
  [switch]$DryRun,
  [switch]$Yes,
  [switch]$Reset,
  [switch]$List,
  [string]$SrcRoot = ".",
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Rest
)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location (Resolve-Path "$here\..")

try {
  # Bootstrap venv if missing
  if (-not (Test-Path ".venv")) {
    Write-Host "Bootstrapping .venv..."
    powershell -NoProfile -ExecutionPolicy Bypass -File tools\bootstrap.ps1
  }

  # Activate venv and make sure tools are present
  . .\.venv\Scripts\Activate.ps1
  python -m pip install --upgrade pip | Out-Null
  pip install -r tools\requirements-dev.txt | Out-Null

  # Build arg list for uploader
  $argsList = @()
  if ($Port)      { $argsList += @("--port", $Port) }
  if ($Clean)     { $argsList += "--clean" }
  if ($DryRun)    { $argsList += "--dry-run" }
  if ($Yes)       { $argsList += "--yes" }
  if ($Reset)     { $argsList += "--reset" }
  if ($List)      { $argsList += "--list" }
  if ($SrcRoot -and $SrcRoot -ne ".") { $argsList += @("--src-root", $SrcRoot) }
  if ($Rest)      { $argsList += $Rest }

  # Run the uploader
  python tools\upload_to_pico.py @argsList
}
finally {
  Pop-Location
}
