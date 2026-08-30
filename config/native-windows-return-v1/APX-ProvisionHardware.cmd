@echo off
setlocal EnableExtensions
set "APX_LOG=%ProgramData%\APX\Provisioning"
if not exist "%APX_LOG%" mkdir "%APX_LOG%"
del /f /q "%APX_LOG%\hardware.failed" "%APX_LOG%\hardware.complete" 2>nul
"%SystemRoot%\System32\pnputil.exe" /add-driver "C:\APX\Drivers\Realtek8852AE\netrtwlane6.inf" /install >"%APX_LOG%\hardware.log" 2>&1
if errorlevel 1 (
    echo Driver provisioning failed>"%APX_LOG%\hardware.failed"
    exit /b 1
)
echo Driver provisioning complete>"%APX_LOG%\hardware.complete"
exit /b 0
