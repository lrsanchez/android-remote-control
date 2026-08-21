$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Tools = Join-Path $Root 'tools'
$ScrcpyDir = Join-Path $Tools 'scrcpy-win64-v4.1'
$PlatformToolsDir = Join-Path $Tools 'platform-tools'
$PythonReq = Join-Path $Root 'requirements.txt'
$DesktopDir = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'
$ShortcutPath = Join-Path $DesktopDir 'Tablet Control Tray.lnk'

New-Item -ItemType Directory -Force -Path $Tools | Out-Null

$PythonCmd = 'python'
$PythonArgsPrefix = @()
if (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCmd = 'py'
    $PythonArgsPrefix = @('-3')
}

Write-Host 'Installing Python dependencies...'
& $PythonCmd @PythonArgsPrefix -m pip install -r $PythonReq

if (-not (Test-Path $ScrcpyDir)) {
    $scrcpyZip = Join-Path $env:TEMP 'scrcpy-win64-v4.1.zip'
    Invoke-WebRequest -Uri 'https://github.com/Genymobile/scrcpy/releases/download/v4.1/scrcpy-win64-v4.1.zip' -OutFile $scrcpyZip
    Expand-Archive -Path $scrcpyZip -DestinationPath $Tools -Force
}

if (-not (Test-Path $PlatformToolsDir)) {
    $adbZip = Join-Path $env:TEMP 'platform-tools-latest-windows.zip'
    Invoke-WebRequest -Uri 'https://dl.google.com/android/repository/platform-tools-latest-windows.zip' -OutFile $adbZip
    Expand-Archive -Path $adbZip -DestinationPath $Tools -Force
}

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = 'cmd.exe'
$Shortcut.Arguments = "/c \"$Root\run-tray.bat\""
$Shortcut.WorkingDirectory = $Root
$Shortcut.IconLocation = "$env:SystemRoot\System32\SHELL32.dll,220"
$Shortcut.Save()

Write-Host "Installed. Start menu shortcut created at: $ShortcutPath"
