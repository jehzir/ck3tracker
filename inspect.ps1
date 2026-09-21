$base = 'C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\common'
$configs = @(
    @{ Folder = 'scripted_animations'; Priority = 'Low' },
    @{ Folder = 'scripted_character_templates'; Priority = 'Medium' },
    @{ Folder = 'scripted_costs'; Priority = 'High' },
    @{ Folder = 'scripted_guis'; Priority = 'Low' }
)

foreach ($cfg in $configs) {
    $folderPath = Join-Path $base $cfg.Folder
    if (Test-Path $folderPath) {
        $files = @(Get-ChildItem -Path $folderPath -Recurse -File | ForEach-Object {
            $relPath = $_.FullName.Substring($base.Length + 1).Replace('\', '/')
            [PSCustomObject]@{
                RelativePath = $relPath
                LastWriteTime = $_.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss zzz')
            }
        } | Sort-Object RelativePath)
        
        Write-Output "Folder: $($cfg.Folder) | Priority: $($cfg.Priority) | Total Files: $($files.Count)"
        foreach ($file in $files) {
            Write-Output " - Path: $($file.RelativePath) | LastWriteTime: $($file.LastWriteTime)"
        }
        Write-Output ""
    } else {
        Write-Output "Folder not found: $($cfg.Folder)"
    }
}
