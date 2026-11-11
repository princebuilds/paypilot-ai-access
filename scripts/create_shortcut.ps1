$desktop = [Environment]::GetFolderPath("Desktop")
$lnkPath = Join-Path $desktop "PayPilot AI ACCESS.lnk"
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($lnkPath)
$sc.TargetPath = "C:\PAYPAL\start.bat"
$sc.WorkingDirectory = "C:\PAYPAL"
$sc.Description = "Start PayPilot AI ACCESS Server"
$sc.Save()
Write-Host "Shortcut created at: $lnkPath"
