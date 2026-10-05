<#
Nullovation City: folder links that open in File Explorer.

Browsers do not let a web page open File Explorer, so this teaches Windows one new
kind of link, nullovation-folder:, and a small helper that opens it. Run it once on
this PC: right-click this file and choose Run with PowerShell. No admin rights needed;
it only touches your own user account.

What the helper accepts: a folder or a file on a drive or a network share, nothing
else. A folder opens in File Explorer; a file opens its folder with the file selected.
It never runs or opens a file itself, so a link from any other website can do no more
than open a folder window.

Or run it from a normal PowerShell window (no admin needed), in the folder where you saved it:
  powershell -ExecutionPolicy Bypass -File .\nullovation-folder-links.ps1

To undo it: run this file again with -Uninstall, for example:
  powershell -ExecutionPolicy Bypass -File .\nullovation-folder-links.ps1 -Uninstall

It waits for Enter before closing, so the result stays on screen; add -NoPause to skip that.
#>
param([switch]$Uninstall, [switch]$NoPause)
$ErrorActionPreference = 'Stop'

function Finish([string]$message, [int]$code = 0) {
    if ($code -eq 0) { Write-Host $message -ForegroundColor Green } else { Write-Host $message -ForegroundColor Red }
    if (-not $NoPause) { Read-Host 'Press Enter to close' | Out-Null }
    exit $code
}

try {

$scheme  = 'nullovation-folder'
$key     = "HKCU:\Software\Classes\$scheme"
$dir     = Join-Path $env:LOCALAPPDATA 'Nullovation City'
$handler = Join-Path $dir 'open-folder.ps1'

if ($Uninstall) {
    if (Test-Path -LiteralPath $key) { Remove-Item -LiteralPath $key -Recurse -Force }
    if (Test-Path -LiteralPath $handler) { Remove-Item -LiteralPath $handler -Force }
    Finish 'Removed. Folder links open in the browser again.'
}

New-Item -ItemType Directory -Path $dir -Force | Out-Null
@'
param([string]$Link)
# Opens a Nullovation City folder link in File Explorer. Only paths on a drive (C:\...) or a
# network share (\\server\share\...) are accepted. A folder opens; a file opens its folder with
# the file selected. Nothing is ever run. Each click is noted in last-link.txt beside this file.
$log = Join-Path $PSScriptRoot 'last-link.txt'
function Note([string]$t) { try { Set-Content -LiteralPath $log -Value ((Get-Date -Format s) + "`r`n" + $t + "`r`nReceived: " + $Link) -Encoding UTF8 } catch { } }
function Say([string]$t) { try { (New-Object -ComObject WScript.Shell).Popup($t, 10, 'Nullovation City', 48) | Out-Null } catch { } }
$path = $Link -replace '^nullovation-folder:(//)?', ''
for ($k = 0; $k -lt 3 -and $path -match '%[0-9A-Fa-f]{2}'; $k++) {           # decoded until plain, even if the browser encoded it twice
    try { $path = [System.Uri]::UnescapeDataString($path) } catch { break }
}
$path = $path.Trim().Trim('"').Replace('/', '\')
if ($path.Length -gt 3) { $path = $path.TrimEnd('\') }
if ($path -notmatch '^(?:[A-Za-z]:\\|\\\\[^\\]+\\[^\\]+)') {
    Note ('Could not read it as a folder path: ' + $path)
    Say ('Nullovation City could not read this folder link as a path:' + "`n`n" + $path)
    exit 1
}
$explorer = Join-Path $env:SystemRoot 'explorer.exe'
if (Test-Path -LiteralPath $path -PathType Container) {
    Note ('Opened: ' + $path)
    Start-Process -FilePath $explorer -ArgumentList ('"{0}"' -f $path)
} elseif (Test-Path -LiteralPath $path -PathType Leaf) {
    Note ('Opened its folder, with the file selected: ' + $path)
    Start-Process -FilePath $explorer -ArgumentList ('/select,"{0}"' -f $path)
} else {
    Note ('Not found: ' + $path)
    Say ('This folder was not found:' + "`n`n" + $path)
    exit 1
}
Start-Sleep -Milliseconds 700                                                   # bring the new window to the front
try { (New-Object -ComObject WScript.Shell).AppActivate((Split-Path $path -Leaf)) | Out-Null } catch { }
'@ | Set-Content -LiteralPath $handler -Encoding UTF8

$ps = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
New-Item -Path "$key\shell\open\command" -Force | Out-Null
Set-ItemProperty -Path $key -Name '(default)' -Value 'URL:Nullovation City folder link'
New-ItemProperty -Path $key -Name 'URL Protocol' -Value '' -PropertyType String -Force | Out-Null
$command = '"{0}" -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "{1}" "%1"' -f $ps, $handler
Set-ItemProperty -Path "$key\shell\open\command" -Name '(default)' -Value $command

Write-Host 'The first time you click a folder link, your browser asks to open Windows PowerShell: that is this helper. Allow it.'
Finish 'Done. In Nullovation City, open Tools in the side bar and turn on Folder links open in File Explorer.'
} catch {
    Finish ('The setup did not finish: ' + $_.Exception.Message) 1
}
