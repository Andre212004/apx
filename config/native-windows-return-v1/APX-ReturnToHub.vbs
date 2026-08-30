Option Explicit
Dim shell, command, status
Set shell = CreateObject("WScript.Shell")
command = "powershell.exe -NoLogo -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File """ & shell.ExpandEnvironmentStrings("%ProgramData%\APX\ReturnToHub\APX-ReturnToHub.ps1") & """"
Do
    status = shell.Run(command, 0, True)
    If status = 0 Then Exit Do
    WScript.Sleep 2000
Loop
