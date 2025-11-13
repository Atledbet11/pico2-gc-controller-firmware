<#
Upload files to a CircuitPython board (CIRCUITPY).

Modes:
  default : overwrite boot.py, code.py, and lib/ (no delete)
  clean   : delete CIRCUITPY:\lib then copy fresh

Options:
  -MountPath E:\     # override auto-detected CIRCUITPY path

Notes:
  - Copy order is lib -> code.py -> boot.py
  - After changing boot.py, press RESET (or replug) so dual CDC re-enumerates
#>
[CmdletBinding()]
param(
  [ValidateSet('default','clean')]
  [string]$Mode = 'default',
  [string]$MountPath
)

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot  = Split-Path -Parent $ScriptDir
Set-Location $RepoRoot

function Find-CircuitPy {
  param([string]$Override)

  if ($Override) {
    if (-not (Test-Path $Override)) { throw "MountPath '$Override' not found." }
    return (Resolve-Path $Override).Path
  }

  $candidates = @()

  # Preferred: Get-Volume by label
  try {
    $vols = Get-Volume -ErrorAction Stop | Where-Object { $_.FileSystemLabel -eq 'CIRCUITPY' }
    foreach ($v in $vols) {
      if ($v.DriveLetter) { $candidates += ($v.DriveLetter + ':\') }
    }
  } catch {}

  # Fallback: WMI by VolumeName
  if ($candidates.Count -eq 0) {
    try {
      $ld = Get-CimInstance Win32_LogicalDisk | Where-Object { $_.VolumeName -eq 'CIRCUITPY' }
      foreach ($d in $ld) { $candidates += ($d.DeviceID + '\') }
    } catch {}
  }

  # Last resort: scan common drive letters for markers
  if ($candidates.Count -eq 0) {
    foreach ($letter in 'D'..'Z') {
      $p = "$($letter):\"
      if (Test-Path $p) {
        if (Test-Path (Join-Path $p 'boot_out.txt') -or (Test-Path (Join-Path $p 'code.py'))) {
          $candidates += $p
        }
      }
    }
  }

  $candidates = $candidates | Sort-Object -Unique
  if ($candidates.Count -eq 0) { throw "CIRCUITPY not found. Plug the board in as a USB drive or pass -MountPath." }
  if ($candidates.Count -eq 1) { return $candidates[0] }

  Write-Host "Multiple CIRCUITPY drives detected:" -ForegroundColor Yellow
  for ($i=0; $i -lt $candidates.Count; $i++) { Write-Host " [$i] $($candidates[$i])" }
  $idx = Read-Host "Select index"
  if ($idx -as [int] -lt 0 -or $idx -as [int] -ge $candidates.Count) { throw "Invalid selection." }
  return $candidates[[int]$idx]
}

function Copy-Tree {
  param([string]$Src,[string]$Dst)
  if (-not (Test-Path $Src)) { return }
  if (-not (Test-Path $Dst)) { New-Item -ItemType Directory -Path $Dst | Out-Null }
  Copy-Item -Path (Join-Path $Src '*') -Destination $Dst -Recurse -Force
}

# --- main ---
$dstRoot = Find-CircuitPy -Override $MountPath
Write-Host "CIRCUITPY: $dstRoot"

$srcBoot = Join-Path $RepoRoot 'boot.py'
$srcCode = Join-Path $RepoRoot 'code.py'
$srcLib  = Join-Path $RepoRoot 'lib'

if (-not (Test-Path $srcBoot)) { throw "Missing $srcBoot" }
if (-not (Test-Path $srcCode)) { throw "Missing $srcCode" }
# lib/ optional

$dstBoot = Join-Path $dstRoot 'boot.py'
$dstCode = Join-Path $dstRoot 'code.py'
$dstLib  = Join-Path $dstRoot 'lib'

if ($Mode -eq 'clean') {
  Write-Host "Clean mode: removing $dstLib ..." -ForegroundColor Yellow
  if (Test-Path $dstLib) {
    Remove-Item $dstLib -Recurse -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 150
  }
}

# Copy: lib -> code.py -> boot.py
if (Test-Path $srcLib) {
  Write-Host "Copying lib/ ..."
  Copy-Tree -Src $srcLib -Dst $dstLib
}

Write-Host "Copying code.py ..."
Copy-Item -LiteralPath $srcCode -Destination $dstCode -Force

Write-Host "Copying boot.py ..."
Copy-Item -LiteralPath $srcBoot -Destination $dstBoot -Force

Start-Sleep -Milliseconds 200
Write-Host "Done."
Write-Host "If boot.py changed, press RESET (or replug) to re-enumerate dual CDC."
