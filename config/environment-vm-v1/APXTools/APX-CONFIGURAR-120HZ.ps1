$ErrorActionPreference = "Stop"

$reportDirectory = Join-Path $env:ProgramData "APX"
New-Item -ItemType Directory -Force -Path $reportDirectory | Out-Null
$report = Join-Path $reportDirectory "looking-glass-display.txt"

Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

public static class ApxDisplayMode {
    private const int ENUM_CURRENT_SETTINGS = -1;
    private const int CDS_UPDATEREGISTRY = 0x00000001;
    private const int DISP_CHANGE_SUCCESSFUL = 0;
    private const uint DM_BITSPERPEL = 0x00040000;
    private const uint DM_PELSWIDTH = 0x00080000;
    private const uint DM_PELSHEIGHT = 0x00100000;
    private const uint DM_DISPLAYFREQUENCY = 0x00400000;

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct DISPLAY_DEVICE {
        public int cb;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string DeviceName;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)] public string DeviceString;
        public uint StateFlags;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)] public string DeviceID;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)] public string DeviceKey;
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct DEVMODE {
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string dmDeviceName;
        public ushort dmSpecVersion, dmDriverVersion, dmSize, dmDriverExtra;
        public uint dmFields;
        public int dmPositionX, dmPositionY;
        public uint dmDisplayOrientation, dmDisplayFixedOutput;
        public short dmColor, dmDuplex, dmYResolution, dmTTOption, dmCollate;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string dmFormName;
        public ushort dmLogPixels;
        public uint dmBitsPerPel, dmPelsWidth, dmPelsHeight, dmDisplayFlags,
                    dmDisplayFrequency, dmICMMethod, dmICMIntent, dmMediaType,
                    dmDitherType, dmReserved1, dmReserved2, dmPanningWidth,
                    dmPanningHeight;
    }

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern bool EnumDisplayDevices(string device, uint index,
        ref DISPLAY_DEVICE display, uint flags);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern bool EnumDisplaySettings(string device, int mode,
        ref DEVMODE settings);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int ChangeDisplaySettingsEx(string device,
        ref DEVMODE settings, IntPtr window, uint flags, IntPtr parameter);

    public static string Configure() {
        string selected = null;
        string description = null;
        for (uint index = 0; ; ++index) {
            DISPLAY_DEVICE display = new DISPLAY_DEVICE();
            display.cb = Marshal.SizeOf(display);
            if (!EnumDisplayDevices(null, index, ref display, 0)) break;
            string identity = (display.DeviceString + " " + display.DeviceID + " " + display.DeviceKey);
            if (identity.IndexOf("Looking Glass", StringComparison.OrdinalIgnoreCase) >= 0 ||
                identity.IndexOf("Indirect Display", StringComparison.OrdinalIgnoreCase) >= 0) {
                selected = display.DeviceName;
                description = display.DeviceString;
                break;
            }
        }
        if (selected == null) throw new InvalidOperationException("o ecrã IDD Looking Glass não foi encontrado");

        DEVMODE current = new DEVMODE();
        current.dmSize = (ushort)Marshal.SizeOf(current);
        if (!EnumDisplaySettings(selected, ENUM_CURRENT_SETTINGS, ref current))
            throw new InvalidOperationException("não foi possível ler o modo atual do IDD");
        if (current.dmPelsWidth == 1920 && current.dmPelsHeight == 1080 && current.dmDisplayFrequency == 120)
            return description + ": 1920x1080 @ 120 Hz (já ativo)";

        DEVMODE chosen = new DEVMODE();
        bool supported = false;
        for (int mode = 0; ; ++mode) {
            DEVMODE candidate = new DEVMODE();
            candidate.dmSize = (ushort)Marshal.SizeOf(candidate);
            if (!EnumDisplaySettings(selected, mode, ref candidate)) break;
            if (candidate.dmPelsWidth == 1920 && candidate.dmPelsHeight == 1080 &&
                candidate.dmDisplayFrequency == 120 && candidate.dmBitsPerPel >= 32) {
                chosen = candidate;
                supported = true;
                break;
            }
        }
        if (!supported) throw new InvalidOperationException("o IDD não anunciou 1920x1080 a 120 Hz");
        chosen.dmFields = DM_BITSPERPEL | DM_PELSWIDTH | DM_PELSHEIGHT | DM_DISPLAYFREQUENCY;
        int result = ChangeDisplaySettingsEx(selected, ref chosen, IntPtr.Zero,
            CDS_UPDATEREGISTRY, IntPtr.Zero);
        if (result != DISP_CHANGE_SUCCESSFUL)
            throw new InvalidOperationException("Windows recusou o modo 120 Hz (código " + result + ")");
        return description + ": 1920x1080 @ 120 Hz (ativado)";
    }
}
'@

try {
    powercfg.exe /setactive SCHEME_MIN | Out-Null
    $displayResult = [ApxDisplayMode]::Configure()
    $gpu = Get-CimInstance Win32_VideoController |
        Select-Object Name, DriverVersion, CurrentHorizontalResolution,
            CurrentVerticalResolution, CurrentRefreshRate
    $service = Get-CimInstance Win32_Service |
        Where-Object { $_.Name -like "*looking*glass*" -or $_.DisplayName -like "*Looking Glass*" } |
        Select-Object Name, State, StartMode
    @(
        "APX Looking Glass acceptance"
        "Display: $displayResult"
        "Power: High performance"
        ""
        "GPU:"
        ($gpu | Format-Table -AutoSize | Out-String).Trim()
        ""
        "Service:"
        ($service | Format-Table -AutoSize | Out-String).Trim()
    ) | Set-Content -Encoding UTF8 -Path $report
    Write-Host "APX: $displayResult"
    Write-Host "APX: diagnóstico guardado em $report"
    exit 0
}
catch {
    "APX: $($_.Exception.Message)" | Set-Content -Encoding UTF8 -Path $report
    Write-Error "APX: $($_.Exception.Message). Consulte $report"
    exit 1
}
