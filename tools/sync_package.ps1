<#
.SYNOPSIS
Sync package skills into a platform skills directory (e.g., Artex).

.DESCRIPTION
Copies package/skills/* into the target skills directory.
Platforms bind skills by DIRECTORY NAME, so directories are never renamed - only contents are updated.
With -IncludeLibrary also copies package/library/skills/*.

.EXAMPLE
powershell -NoProfile -ExecutionPolicy Bypass -File tools/sync_package.ps1 -SkillsTarget "C:\platform\skills"
powershell -NoProfile -ExecutionPolicy Bypass -File tools/sync_package.ps1 -SkillsTarget "..." -IncludeLibrary
powershell -NoProfile -ExecutionPolicy Bypass -File tools/sync_package.ps1 -SkillsTarget "..." -DryRun
#>
param(
  [string]$PackageDir,
  [Parameter(Mandatory = $true)][string]$SkillsTarget,
  [switch]$IncludeLibrary,
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$ScriptDir = $PSScriptRoot
if (-not $ScriptDir) { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
if (-not $ScriptDir) { $ScriptDir = (Get-Location).Path }
if (-not $PackageDir) { $PackageDir = Join-Path $ScriptDir '..\package' }
$PackageDir = (Resolve-Path $PackageDir).Path
if (-not (Test-Path $SkillsTarget)) { New-Item -ItemType Directory -Force -Path $SkillsTarget | Out-Null }

$sources = [ordered]@{ 'skills' = (Join-Path $PackageDir 'skills') }
if ($IncludeLibrary) { $sources['library'] = (Join-Path $PackageDir 'library\skills') }

$report = @()
foreach ($srcName in $sources.Keys) {
  $src = $sources[$srcName]
  if (-not (Test-Path $src)) { Write-Warning "skip (missing dir): $src"; continue }
  foreach ($skillDir in (Get-ChildItem $src -Directory)) {
    $name = $skillDir.Name
    $srcSkill = Join-Path $skillDir.FullName 'SKILL.md'
    if (-not (Test-Path $srcSkill)) { Write-Warning "skip (no SKILL.md): $name"; continue }
    $dst = Join-Path $SkillsTarget $name
    $status = 'add'
    if (Test-Path $dst) {
      $dstSkill = Join-Path $dst 'SKILL.md'
      if ((Test-Path $dstSkill) -and ((Get-FileHash $srcSkill).Hash -eq (Get-FileHash $dstSkill).Hash)) {
        $status = 'unchanged'
      } else { $status = 'update' }
    }
    if (($status -ne 'unchanged') -and (-not $DryRun)) {
      Copy-Item -Path $skillDir.FullName -Destination $SkillsTarget -Recurse -Force
    }
    $report += [pscustomobject]@{ Status = $status; Source = $srcName; Skill = $name }
  }
}

$report | Sort-Object Source, Skill | Format-Table -AutoSize | Out-String | Write-Output
$changed = @($report | Where-Object { $_.Status -ne 'unchanged' }).Count
Write-Output ("total: {0} skills, to change: {1} (DryRun={2})" -f $report.Count, $changed, [bool]$DryRun)