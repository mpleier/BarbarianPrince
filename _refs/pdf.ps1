param([string]$Path, [string]$Out)
$b = [System.IO.File]::ReadAllBytes($Path)
$s = [System.Text.Encoding]::GetEncoding(28591).GetString($b)
$acc = ""
foreach ($m in [regex]::Matches($s, 'stream\r?\n')) {
    $start = $m.Index + $m.Value.Length
    $end = $s.IndexOf('endstream', $start)
    if ($end -lt 0) { continue }
    if ($end - $start -le 2) { continue }
    $bytes = New-Object byte[] ($end - $start)
    for ($i = 0; $i -lt ($end - $start); $i++) { $bytes[$i] = $b[$start + $i] }
    for ($skip = 0; $skip -le 2; $skip++) {
        try {
            $sub = New-Object byte[] ($bytes.Length - $skip)
            for ($i = 0; $i -lt $sub.Length; $i++) { $sub[$i] = $bytes[$skip + $i] }
            $ms = New-Object System.IO.MemoryStream(, $sub)
            $ds = New-Object System.IO.Compression.DeflateStream($ms, [System.IO.Compression.CompressionMode]::Decompress)
            $sr = New-Object System.IO.StreamReader($ds, [System.Text.Encoding]::GetEncoding(28591))
            $txt = $sr.ReadToEnd()
            if ($txt.Length -gt 20) { $acc += $txt; break }
        } catch { }
    }
    $acc += "`n"
}
[System.IO.File]::WriteAllText($Out, $acc)
Write-Output ("chars: " + $acc.Length)
