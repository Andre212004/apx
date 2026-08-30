@echo off
setlocal EnableExtensions
set "APX_LOG=%ProgramData%\APX\Provisioning"
if not exist "%APX_LOG%" mkdir "%APX_LOG%"
del /f /q "%APX_LOG%\hardware.failed" "%APX_LOG%\hardware.complete" "%APX_LOG%\hardware.warning" 2>nul
"%SystemRoot%\System32\pnputil.exe" /add-driver "C:\APX\Drivers\Realtek8852AE\netrtwlane6.inf" /install >"%APX_LOG%\hardware.log" 2>&1
set "APX_PNP_EXIT=%ERRORLEVEL%"
if not "%APX_PNP_EXIT%"=="0" (
    "%SystemRoot%\System32\pnputil.exe" /enum-drivers /files >"%APX_LOG%\hardware-state.log" 2>&1
    "%SystemRoot%\System32\findstr.exe" /I /C:"netrtwlane6.inf" "%APX_LOG%\hardware-state.log" >nul
    if errorlevel 1 (
        echo Driver provisioning failed; pnputil exit=%APX_PNP_EXIT%>"%APX_LOG%\hardware.failed"
        exit /b 1
    )
    echo Driver package was already present; pnputil exit=%APX_PNP_EXIT%>"%APX_LOG%\hardware.warning"
)
echo Driver provisioning complete>"%APX_LOG%\hardware.complete"
exit /b 0
