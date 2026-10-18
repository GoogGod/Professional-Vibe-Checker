<#
.SYNOPSIS
Build a transferable package zip + SHA256SUMS.

.EXAMPLE
powershell -NoProfile -ExecutionPolicy Bypass -File tools/make_bundle.ps1
#>
param(
  [string]$PackageDir,
  [string]$OutDir
)

$ErrorActionPreference = 'Stop'
$ScriptDir = $PSScriptRoot
if (-not $ScriptDir) { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
if (-not $ScriptDir) { $ScriptDir = (Get-Location).Path }
if (-not $PackageDir) { $PackageDir = Join-Path $ScriptDir '..\package' }
if (-not $OutDir) { $OutDir = Join-Path $ScriptDir '..\dist' }
$PackageDir = (Resolve-Path $PackageDir).Path
$ver = (Get-Content (Join-Path $PackageDir 'VERSION') -Raw).Trim()
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$zip = Join-Path $OutDir ("redteam-pack-{0}.zip" -f $ver)
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path (Join-Path $PackageDir '*') -DestinationPath $zip -CompressionLevel Optimal

$lines = Get-ChildItem $PackageDir -Recurse -File | Sort-Object FullName | ForEach-Object {
  $rel = $_.FullName.Substring($PackageDir.Length + 1).Replace('\', '/')
  $h = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower()
  "{0}  {1}" -f $h, $rel
}
$sums = Join-Path $OutDir 'SHA256SUMS.txt'
$lines | Set-Content -Path $sums -Encoding UTF8

$zipHash = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
"zip:  {0} ({1} KB)" -f $zip, [math]::Round((Get-Item $zip).Length / 1KB, 1)
"sha256(zip): $zipHash"
"sums: {0} ({1} files)" -f $sums, $lines.Count