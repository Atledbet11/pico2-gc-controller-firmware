param(
  [string]$PythonSpec = ""  # optional override, e.g. "C:\Python312\python.exe"
)

$ErrorActionPreference = "Stop"

# Resolve Python executable + args (prefer 'py -3' if available)
$pyExe  = "python"
$pyArgs = @()
if (Get-Command py -ErrorAction SilentlyContinue) {
  $pyExe  = "py"
  $pyArgs = @("-3")
}
if ($PSBoundParameters.ContainsKey('PythonSpec') -and $PythonSpec) {
  $parts = $PythonSpec -split '\s+'
  $pyExe  = $parts[0]
  $pyArgs = @()
  if ($parts.Length -gt 1) { $pyArgs = $parts[1..($parts.Length-1)] }
}

# --- robust Python version probe (no nested quotes) ---
$ver = & $pyExe @pyArgs -c "import sys; v=sys.version_info; print('%d.%d.%d' % (v[0], v[1], v[2]))"
if (-not $ver) { throw "Unable to read Python version from $pyExe $($pyArgs -join ' ')" }
$split = $ver.Trim().Split('.')
if ([int]$split[0] -lt 3 -or (([int]$split[0] -eq 3) -and ([int]$split[1] -lt 8))) {
  throw "Python 3.8+ required (found $ver)"
}

# Create venv if missing
if (-not (Test-Path ".venv")) {
  & $pyExe @pyArgs -m venv .venv
}

# Activate and install tools
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r tools\requirements-dev.txt

Write-Host "Bootstrap complete. Venv: .venv (Python $ver)"
