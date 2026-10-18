<#
.SYNOPSIS
Package check: forbidden entities (competition names/markers, personal paths, flag candidates).

.DESCRIPTION
Exit codes: 0 - clean; 1 - violations; 2 - review candidates present.
Whitelist: C:\Users\suspect (training example in library materials), literal C:\Users\... doc example; <user> placeholders allowed.

.EXAMPLE
powershell -NoProfile -ExecutionPolicy Bypass -File tools/check_package.ps1
#>
param(
  [string]$PackageDir
)

$ErrorActionPreference = 'Stop'
$ScriptDir = $PSScriptRoot
if (-not $ScriptDir) { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
if (-not $ScriptDir) { $ScriptDir = (Get-Location).Path }
if (-not $PackageDir) { $PackageDir = Join-Path (Join-Path $ScriptDir '..') 'package' }
$PackageDir = (Resolve-Path $PackageDir).Path
$files = Get-ChildItem $PackageDir -Recurse -File

$nameHits = @($files | Select-String -Pattern 'Immortal|kubstu|goctf|rdgctf' -Encoding UTF8)
$pathHits = @($files | Select-String -Pattern 'C:\\Users\\[^<\\]|/home/Immortal' -Encoding UTF8 |
  Where-Object { $_.Line -notmatch 'C:\\Users\\suspect' -and $_.Line -notmatch 'C:\\Users\\\.\.\.' })
$flagCand = @($files | Select-String -Pattern '[A-Za-z0-9_]{2,24}\{[A-Za-z0-9_@!#$%^&*\-\.\?\+]{8,80}\}' -Encoding UTF8 |
  Where-Object { $_.Line -notmatch '(?i)flag\{|ctf\{|<hex>|\.\.\.|example|prefix|decoy|filecontents|begin\{|candidate|attempt_|hour_bucket|admin\{|seed_|document' })

function Show($title, $items, $limit = 20) {
  $items = @($items)
  if ($items.Count -eq 1 -and $null -eq $items[0]) { $items = @() }
  "== ${title}: $($items.Count) =="
  $n = [Math]::Min($limit, $items.Count)
  for ($i = 0; $i -lt $n; $i++) {
    $m = $items[$i]
    $t = "$($m.Line)".Trim(); if ($t.Length -gt 140) { $t = $t.Substring(0, 140) }
    "  {0}:{1}: {2}" -f $m.Filename, $m.LineNumber, $t
  }
}

Show 'violations (names/markers)' $nameHits
Show 'personal paths (review)' $pathHits
Show 'flag candidates (review)' $flagCand

if (@($nameHits).Count -gt 0) { Write-Output 'RESULT: 1 (violations)'; exit 1 }
if ((@($pathHits).Count -gt 0) -or (@($flagCand).Count -gt 0)) { Write-Output 'RESULT: 2 (manual review needed)'; exit 2 }
Write-Output 'RESULT: 0 (clean)'