param([string]$Path, [string]$Out)
$s = [System.IO.File]::ReadAllText($Path)
$lines = New-Object System.Collections.ArrayList
foreach ($m in [regex]::Matches($s, '\((?:[^()\\]|\\.)*\)\s*(Tj|TJ)')) {
    $t = $m.Value
    $t = $t -replace '^\(', '' -replace '\)\s*(Tj|TJ)$', ''
    $t = $t -replace '\\(\d{3})', '?'
    $t = $t -replace '\\(', '(' -replace '\\)', ')'
    [void]$lines.Add($t)
}
[System.IO.File]::WriteAllLines($Out, $lines)
Write-Output ("lines: " + $lines.Count)
