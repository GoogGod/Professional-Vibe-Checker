<#
.SYNOPSIS
Проверка пакета на запрещённые сущности: имена/маркеры соревнований, личные пути, кандидаты флагов.

.DESCRIPTION
Коды выхода: 0 — чисто; 1 — нарушения (имена/маркеры); 2 — есть кандидаты на ручную проверку.
Whitelist: C:\Users\suspect — известный учебный пример в материалах библиотеки; плейсхолдеры <user> допустимы.

.EXAMPLE
powershell -NoProfile -ExecutionPolicy Bypass -File tools/check_package.ps1
#>
param(
  [string]$PackageDir = (Join-Path $PSScriptRoot '..\package')
)

$ErrorActionPreference = 'Stop'
$PackageDir = (Resolve-Path $PackageDir).Path
$files = Get-ChildItem $PackageDir -Recurse -File

$nameHits = $files | Select-String -Pattern 'Immortal|kubstu|goctf|rdgctf' -Encoding UTF8
$pathHits = $files | Select-String -Pattern 'C:\\Users\\[^<\\]|/home/Immortal' -Encoding UTF8 |
  Where-Object { $_.Line -notmatch 'C:\\Users\\suspect' }
$flagCand = $files | Select-String -Pattern '[A-Za-z0-9_]{2,24}\{[A-Za-z0-9_@!#$%^&*\-\.\?\+]{8,80}\}' -Encoding UTF8 |
  Where-Object { $_.Line -notmatch '(?i)flag\{|ctf\{|<hex>|\.\.\.|example|prefix|decoy|filecontents|begin\{|candidate|attempt_|hour_bucket|admin\{|seed_|document' }

function Show($title, $items, $limit = 20) {
  $items = @($items)
  "== $title: $($items.Count) =="
  $items | Select-Object -First $limit | ForEach-Object {
    $t = $_.Line.Trim(); if ($t.Length -gt 140) { $t = $t.Substring(0, 140) }
    "  {0}:{1}: {2}" -f $_.Filename, $_.LineNumber, $t
  }
}

Show 'нарушения (имена/маркеры)' $nameHits
Show 'личные пути (проверить)' $pathHits
Show 'кандидаты флагов (проверить)' $flagCand

if (@($nameHits).Count -gt 0) { Write-Output 'РЕЗУЛЬТАТ: 1 (нарушения)'; exit 1 }
if ((@($pathHits).Count -gt 0) -or (@($flagCand).Count -gt 0)) { Write-Output 'РЕЗУЛЬТАТ: 2 (нужна ручная проверка кандидатов)'; exit 2 }
Write-Output 'РЕЗУЛЬТАТ: 0 (чисто)'