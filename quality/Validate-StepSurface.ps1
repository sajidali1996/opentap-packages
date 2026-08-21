param(
    [string]$LockPath = "quality/step_surface_lock.json"
)

$ErrorActionPreference = "Stop"

if ($PSScriptRoot -and $PSScriptRoot.Trim() -ne "") {
    $repoRoot = Split-Path -Parent $PSScriptRoot
}
else {
    $repoRoot = (Get-Location).Path
}

if ([System.IO.Path]::IsPathRooted($LockPath)) {
    $lockFullPath = $LockPath
}
else {
    $lockFullPath = Join-Path $repoRoot $LockPath
}

if (-not (Test-Path $lockFullPath)) {
    Write-Host "Lock file not found: $lockFullPath" -ForegroundColor Red
    exit 1
}

$lock = Get-Content -Path $lockFullPath -Raw | ConvertFrom-Json
$errors = New-Object System.Collections.Generic.List[string]

function Get-FileText {
    param([string]$RelativePath)

    $fullPath = Join-Path $repoRoot $RelativePath
    if (-not (Test-Path $fullPath)) {
        return $null
    }

    return Get-Content -Path $fullPath -Raw
}

function Assert-Contains {
    param(
        [string]$Text,
        [string]$Needle,
        [string]$ErrorMessage
    )

    if ($null -eq $Text -or -not $Text.Contains($Needle)) {
        [void]$errors.Add($ErrorMessage)
    }
}

foreach ($resource in $lock.resources) {
    $text = Get-FileText -RelativePath ([string]$resource.file)
    if ($null -eq $text) {
        [void]$errors.Add("Missing file: " + [string]$resource.file)
        continue
    }

    $classNeedle = "class " + [string]$resource.class + "(" + [string]$resource.baseType + "):"
    $displayNeedle = '"' + [string]$resource.displayName + '"'

    Assert-Contains -Text $text -Needle $classNeedle -ErrorMessage ("Resource class signature changed or missing: " + [string]$resource.class + " in " + [string]$resource.file)
    Assert-Contains -Text $text -Needle $displayNeedle -ErrorMessage ("Resource display name changed or missing: " + [string]$resource.displayName + " in " + [string]$resource.file)
}

foreach ($step in $lock.steps) {
    $text = Get-FileText -RelativePath ([string]$step.file)
    if ($null -eq $text) {
        [void]$errors.Add("Missing file: " + [string]$step.file)
        continue
    }

    $classNeedle = "class " + [string]$step.class + "(TestStep):"
    $displayNeedle = '"' + [string]$step.displayName + '"'
    $groupNeedle = '"' + ([string]$step.group).Replace('\', '\\') + '"'

    Assert-Contains -Text $text -Needle $classNeedle -ErrorMessage ("Step class changed or missing: " + [string]$step.class + " in " + [string]$step.file)
    Assert-Contains -Text $text -Needle $displayNeedle -ErrorMessage ("Step display name changed or missing: " + [string]$step.displayName + " in " + [string]$step.file)
    Assert-Contains -Text $text -Needle $groupNeedle -ErrorMessage ("Step group path changed or missing: " + [string]$step.group + " for " + [string]$step.class + " in " + [string]$step.file)
}

if ($errors.Count -gt 0) {
    Write-Host "Step surface compatibility check FAILED" -ForegroundColor Red
    foreach ($e in $errors) {
        Write-Host (" - " + $e) -ForegroundColor Red
    }
    exit 1
}

Write-Host "Step surface compatibility check PASSED" -ForegroundColor Green
Write-Host ("Resources validated: {0}" -f $lock.resources.Count)
Write-Host ("Steps validated: {0}" -f $lock.steps.Count)
exit 0
