$ErrorActionPreference = "Stop"

# Explorer normally owns WIN+E.  Disable only that shell shortcut for this
# Windows user; the APX helper below then owns it.  The setting is read at the
# next sign-in, while WIN+SHIFT+E is also registered as a first-run fallback.
$advanced = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
$disabled = (Get-ItemProperty -Path $advanced -Name DisabledHotkeys -ErrorAction SilentlyContinue).DisabledHotkeys
if ($null -eq $disabled) { $disabled = "" }
if (-not $disabled.Contains("E")) {
    Set-ItemProperty -Path $advanced -Name DisabledHotkeys -Type String -Value ($disabled + "E")
}

Add-Type -TypeDefinition @"
using System;
using System.Diagnostics;
using System.Runtime.InteropServices;

public static class APXReturnToHubHotkey {
    private const int PrimaryId = 0x4150;
    private const int FallbackId = 0x4151;
    private const uint ModShift = 0x0004;
    private const uint ModWin = 0x0008;
    private const uint ModNoRepeat = 0x4000;
    private const uint VirtualKeyE = 0x45;
    private const uint WmHotkey = 0x0312;

    [StructLayout(LayoutKind.Sequential)]
    private struct Point { public int X; public int Y; }

    [StructLayout(LayoutKind.Sequential)]
    private struct Message {
        public IntPtr Window;
        public uint Id;
        public UIntPtr WParam;
        public IntPtr LParam;
        public uint Time;
        public Point Cursor;
        public uint Private;
    }

    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool RegisterHotKey(IntPtr window, int id, uint modifiers, uint key);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool UnregisterHotKey(IntPtr window, int id);

    [DllImport("user32.dll")]
    private static extern int GetMessage(out Message message, IntPtr window, uint minimum, uint maximum);

    private static void RebootToApx() {
        string shutdown = Environment.ExpandEnvironmentVariables(@"%WINDIR%\System32\shutdown.exe");
        Process.Start(new ProcessStartInfo {
            FileName = shutdown,
            Arguments = "/r /t 0 /d p:0:0 /c \"Regressar ao APX HUB\"",
            UseShellExecute = false,
            CreateNoWindow = true
        });
    }

    public static int Run() {
        bool primary = RegisterHotKey(IntPtr.Zero, PrimaryId, ModWin | ModNoRepeat, VirtualKeyE);
        bool fallback = RegisterHotKey(IntPtr.Zero, FallbackId, ModWin | ModShift | ModNoRepeat, VirtualKeyE);
        if (!primary && !fallback) return 2;
        try {
            Message message;
            while (GetMessage(out message, IntPtr.Zero, 0, 0) > 0) {
                ulong id = message.WParam.ToUInt64();
                if (message.Id == WmHotkey &&
                        (id == (ulong)PrimaryId || id == (ulong)FallbackId)) {
                    RebootToApx();
                    return 0;
                }
            }
            return 1;
        } finally {
            if (primary) UnregisterHotKey(IntPtr.Zero, PrimaryId);
            if (fallback) UnregisterHotKey(IntPtr.Zero, FallbackId);
        }
    }
}
"@

[void][APXReturnToHubHotkey]::Run()
