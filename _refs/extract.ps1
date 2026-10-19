param([string]$Path, [string]$Out)
$b = [System.IO.File]::ReadAllBytes($Path)
$s = [System.Text.Encoding]::GetEncoding(28591).GetString($b)
$m = [regex]::Matches($s, "[\x20-\x7E]{30,}")
$t = ($m | ForEach-Object { $_.Value }) -join [char]10
[System.IO.File]::WriteAllText($Out, $t)
Write-Output ("chars: " + $t.Length)
