@echo off
setlocal

fltmc >nul 2>&1
if errorlevel 1 (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

title APX - Ativar aceleracao nativa
echo.
echo APX: a instalar o ecra virtual Looking Glass...
start /wait "" "%~dp0looking-glass-idd-setup.exe" /S
if errorlevel 1 goto :failed

echo APX: a instalar o capturador Looking Glass...
start /wait "" "%~dp0looking-glass-host-setup.exe" /S
if errorlevel 1 goto :failed

echo APX: a preparar 1920x1080 a 120 Hz e o perfil de alto desempenho...
powercfg.exe /setactive SCHEME_MIN >nul 2>&1
reg.exe add "HKLM\Software\Microsoft\Windows\CurrentVersion\RunOnce" /v APXLookingGlass120Hz /t REG_SZ /d "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"%~dp0APX-CONFIGURAR-120HZ.ps1\"" /f >nul
if errorlevel 1 goto :failed

echo.
echo APX: instalacao concluida.
echo APX: no proximo inicio o APX confirma o IDD a 1920x1080 e 120 Hz.
echo APX: durante o reinicio a imagem pode ficar preta ate 90 segundos.
echo APX: no portatil, SUPER+E regressa ao HUB sem desligar fisicamente.
echo.
choice /C RN /N /M "Prima R para reiniciar agora ou N para reiniciar mais tarde: "
if errorlevel 2 exit /b 0
shutdown.exe /r /t 5 /c "APX: a reiniciar para concluir o modo Looking Glass"
exit /b 0

:failed
echo.
echo APX: a instalacao falhou. Nenhum reinicio foi agendado.
pause
exit /b 1
