<#
.SYNOPSIS
Собрать zip-архив пакета для передачи + SHA256SUMS.

.EXAMPLE
powershell -NoProfile -ExecutionPolicy Bypass -File tools/make_bundle.ps1
#>
param(
  [string]$PackageDir = (Join-Path $PSScriptRoot '..\package'),
  [string]$OutDir = (Join-Path $PSScriptRoot '..\dist')
)

$ErrorActionPreference = 'Stop'
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
"sums: {0} ({1} файлов)" -f $sums, $lines.Count