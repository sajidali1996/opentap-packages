param(
    [string]$CsvPath = "C:\Program Files\OpenTAP\results\test.csv"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $CsvPath)) {
    Write-Host "CSV not found: $CsvPath" -ForegroundColor Red
    exit 1
}

$lastLine = Get-Content -Path $CsvPath | Where-Object { $_ -and $_.Trim() -ne "" } | Select-Object -Last 1
if (-not $lastLine) {
    Write-Host "CSV is empty: $CsvPath" -ForegroundColor Red
    exit 1
}

$values = $lastLine -split ',\s*'
$columns = @(
    'output_mode',
    'phase_u_voltage_v', 'phase_u_current_a', 'phase_u_frequency_hz', 'phase_u_active_power_w', 'phase_u_apparent_power_va', 'phase_u_power_factor', 'phase_u_crest_factor', 'phase_u_peak_current_a',
    'phase_v_voltage_v', 'phase_v_current_a', 'phase_v_frequency_hz', 'phase_v_active_power_w', 'phase_v_apparent_power_va', 'phase_v_power_factor', 'phase_v_crest_factor', 'phase_v_peak_current_a',
    'phase_w_voltage_v', 'phase_w_current_a', 'phase_w_frequency_hz', 'phase_w_active_power_w', 'phase_w_apparent_power_va', 'phase_w_power_factor', 'phase_w_crest_factor', 'phase_w_peak_current_a'
)

if ($values.Count -lt $columns.Count) {
    Write-Host "Unexpected GridSim Output row width. Expected at least $($columns.Count), got $($values.Count)." -ForegroundColor Red
    Write-Host "Row: $lastLine" -ForegroundColor Yellow
    exit 1
}

Write-Host "Latest GridSim Output row from: $CsvPath" -ForegroundColor Cyan
for ($i = 0; $i -lt $columns.Count; $i++) {
    Write-Host ("{0}={1}" -f $columns[$i], $values[$i])
}

$u = [double]$values[4]
$v = [double]$values[12]
$w = [double]$values[20]

Write-Host "" 
Write-Host ("Active power summary (W): U={0}, V={1}, W={2}" -f $u, $v, $w) -ForegroundColor Green

if (($u -lt -1000000) -or ($v -lt -1000000) -or ($w -lt -1000000)) {
    Write-Host "WARNING: Very large negative active power detected; this matches the old signed-24 decode bug fingerprint." -ForegroundColor Red
}
