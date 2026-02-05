$content = Get-Content "json/thebfq.json" -Raw

# Replace "name" with "title"
$content = $content -replace '"name":', '"title":'

# Replace all IDs with lowercase letters (keep numbers)
$pattern = '"id":\s*"([^"]*)"'
$content = [System.Text.RegularExpressions.Regex]::Replace($content, $pattern, {
    param($m)
    $id = $m.Groups[1].Value
    $newId = ""
    foreach ($char in $id.ToCharArray()) {
        if ([char]::IsLetter($char)) {
            $newId += [char]::ToLower($char)
        } else {
            $newId += $char
        }
    }
    return '"id": "' + $newId + '"'
})

$content | Set-Content "json/thebfq.json"
Write-Host "Done - file updated with lowercase IDs and title attributes"
