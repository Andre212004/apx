@echo off
setlocal EnableExtensions EnableDelayedExpansion
set "APX_STEP=initialization"
set "APX_EXPECTED=X:\Windows\System32\apx-expected.ini"
set "APX_LOG=X:\apx-native-windows-install-v2.log"
set "APX_DP_SCRIPT=X:\apx-diskpart-v2.txt"
set "APX_DP_OUTPUT=X:\apx-diskpart-v2.out"
set "APX_MOUNT_LIST=X:\apx-mountvol-v2.out"
set "APX_IMAGE_INFO=X:\apx-image-index-v2.out"
set "APX_LAST_COMMAND=initialization"
set "APX_LAST_EXIT=0"
set "APX_DIAGNOSTIC=none"

>"%APX_LOG%" echo APX native Windows installer v2 started.
call :load_expected || call :fatal APX-CONTRACT-01 expected-contract

set "APX_STEP=disk-identity"
call :find_disk || call :fatal APX-DISK-01 disk-identity

set "APX_STEP=partition-identities"
call :find_partition SETUP "c12a7328-f81f-11d2-ba4b-00a0c93ec93b" "APXWINSETUP" "9 GB" || call :fatal APX-PART-04 windows-setup
call :choose_letter SETUP W || call :fatal APX-LETTER-01 windows-setup
call :mount_partition !APX_PART_SETUP! !APX_LETTER_SETUP! SETUP "APXWINSETUP" || call :fatal APX-MOUNT-02 windows-setup
set "APX_MEDIA=!APX_LETTER_SETUP!:"
call :validate_contract "%APX_MEDIA%\APX\install-contract-v2.ini" || call :fatal APX-CONTRACT-02 setup-contract
call :find_partition EFI "c12a7328-f81f-11d2-ba4b-00a0c93ec93b" "APX_EFI" "1024 MB" || call :fatal APX-PART-01 apx-efi
call :choose_letter EFI S || call :fatal APX-LETTER-03 apx-efi
call :mount_partition !APX_PART_EFI! !APX_LETTER_EFI! EFI "APX_EFI" || call :fatal APX-MOUNT-03 apx-efi
set "APX_ESP=!APX_LETTER_EFI!:"
call :validate_contract "%APX_ESP%\EFI\APX\native-windows\install-contract-v2.ini" || call :fatal APX-CONTRACT-04 efi-contract
if not exist "%APX_ESP%\EFI\systemd\systemd-bootx64.efi" call :fatal APX-ESP-01 linux-boot-manager
if not exist "%APX_ESP%\EFI\APX\" call :fatal APX-ESP-02 apx-efi-tree
if exist "%APX_ESP%\EFI\Microsoft\Boot\bootmgfw.efi" call :fatal APX-ESP-03 stale-windows-boot
call :find_partition LINUX "ca7d7ccb-63ed-4c53-861c-1742536059cc" "-" "!APX_LINUX_SIZE_TEXT!" || call :fatal APX-PART-02 apx-linux
rem DiskPart truncates its tabular Label field to 11 characters. Locate the
rem unique Microsoft Basic Data candidate by authenticated disk, type and
rem size; mount_partition then verifies the complete 12-character label and
rem the byte-identical APX contract before any destructive command.
call :find_partition WINDOWS "ebd0a0a2-b9e5-4433-87c0-68b6b72699c7" "-" "!APX_WINDOWS_SIZE_TEXT!" || call :fatal APX-PART-03 windows-target

set "APX_STEP=mount-validated-volumes"
call :choose_letter WINDOWS C || call :fatal APX-LETTER-02 windows-target
call :mount_partition !APX_PART_WINDOWS! !APX_LETTER_WINDOWS! WINDOWS "APXWINTARGET" || call :fatal APX-MOUNT-01 windows-target

set "APX_TARGET=!APX_LETTER_WINDOWS!:"
call :validate_contract "%APX_TARGET%\APX\install-contract-v2.ini" || call :fatal APX-CONTRACT-03 target-contract
if not exist "%APX_MEDIA%\sources\install.swm" call :fatal APX-WIM-01 split-image-first
if not exist "%APX_MEDIA%\sources\install2.swm" call :fatal APX-WIM-02 split-image-second
if not exist "%APX_MEDIA%\sources\install3.swm" call :fatal APX-WIM-03 split-image-third
set "APX_SWM_COUNT=0"
for %%F in ("%APX_MEDIA%\sources\install*.swm") do if exist "%%~fF" set /A APX_SWM_COUNT+=1
if not "!APX_SWM_COUNT!"=="3" call :fatal APX-WIM-06 split-image-count

set "APX_STEP=image-index"
set "APX_LAST_COMMAND=dism-get-wim-info"
X:\Windows\System32\dism.exe /English /Get-WimInfo /WimFile:%APX_MEDIA%\sources\install.swm /Index:6 >"%APX_IMAGE_INFO%" 2>&1
set "APX_LAST_EXIT=!ERRORLEVEL!"
>>"%APX_LOG%" echo COMMAND !APX_LAST_COMMAND! exit=!APX_LAST_EXIT!
if not "!APX_LAST_EXIT!"=="0" call :fatal APX-WIM-04 image-metadata
type "%APX_IMAGE_INFO%" >>"%APX_LOG%"
call :file_has_key_value "%APX_IMAGE_INFO%" "Name" "Windows 11 Pro" || call :fatal APX-WIM-05 windows-11-pro-index-6

set "APX_STEP=format-authorized-target"
set "APX_AUTH_DISK=!APX_DISK!"
set "APX_AUTH_WINDOWS=!APX_PART_WINDOWS!"
call :find_disk || call :fatal APX-FORMAT-00 disk-revalidation
if not "!APX_DISK!"=="!APX_AUTH_DISK!" call :fatal APX-FORMAT-00 disk-changed
call :find_partition WINDOWS "ebd0a0a2-b9e5-4433-87c0-68b6b72699c7" "-" "!APX_WINDOWS_SIZE_TEXT!" || call :fatal APX-FORMAT-00 target-revalidation
if not "!APX_PART_WINDOWS!"=="!APX_AUTH_WINDOWS!" call :fatal APX-FORMAT-00 target-changed
call :validate_contract "%APX_TARGET%\APX\install-contract-v2.ini" || call :fatal APX-FORMAT-00 target-contract-revalidation
>"%APX_DP_SCRIPT%" echo select disk !APX_DISK!
>>"%APX_DP_SCRIPT%" echo select partition !APX_PART_WINDOWS!
>>"%APX_DP_SCRIPT%" echo format fs=ntfs quick label=APXWINTARGET
>>"%APX_DP_SCRIPT%" echo exit
set "APX_LAST_COMMAND=diskpart-format-windows-target"
X:\Windows\System32\diskpart.exe /s "%APX_DP_SCRIPT%" >>"%APX_LOG%" 2>&1
set "APX_LAST_EXIT=!ERRORLEVEL!"
>>"%APX_LOG%" echo COMMAND !APX_LAST_COMMAND! exit=!APX_LAST_EXIT!
if not "!APX_LAST_EXIT!"=="0" call :fatal APX-FORMAT-01 windows-target
md "%APX_TARGET%\APX" >>"%APX_LOG%" 2>&1
copy /B /Y "%APX_EXPECTED%" "%APX_TARGET%\APX\install-contract-v2.ini" >>"%APX_LOG%" 2>&1
if errorlevel 1 call :fatal APX-FORMAT-02 restore-target-contract
call :validate_contract "%APX_TARGET%\APX\install-contract-v2.ini" || call :fatal APX-FORMAT-03 formatted-target-contract
vol %APX_TARGET% >"%APX_DP_OUTPUT%" 2>&1
if errorlevel 1 call :fatal APX-FORMAT-04 formatted-target-volume
X:\Windows\System32\find.exe /I "APXWINTARGET" "%APX_DP_OUTPUT%" >nul || call :fatal APX-FORMAT-04 formatted-target-label

set "APX_STEP=apply-windows-11-pro"
set "APX_LAST_COMMAND=dism-apply-image"
X:\Windows\System32\dism.exe /Apply-Image /ImageFile:%APX_MEDIA%\sources\install.swm /SWMFile:%APX_MEDIA%\sources\install*.swm /Index:6 /ApplyDir:%APX_TARGET%\ /LogPath:%APX_MEDIA%\APX\dism-apply-v2.log /LogLevel:4 >>"%APX_LOG%" 2>&1
set "APX_LAST_EXIT=!ERRORLEVEL!"
>>"%APX_LOG%" echo COMMAND !APX_LAST_COMMAND! exit=!APX_LAST_EXIT! log=%APX_MEDIA%\APX\dism-apply-v2.log
if not "!APX_LAST_EXIT!"=="0" call :fatal APX-APPLY-01 dism-apply-image
if not exist "%APX_TARGET%\Windows\System32\winload.efi" call :fatal APX-APPLY-02 windows-loader
if not exist "%APX_TARGET%\Windows\System32\config\SOFTWARE" call :fatal APX-APPLY-03 windows-registry

set "APX_STEP=stage-apx-integration"
md "%APX_TARGET%\ProgramData\APX\ReturnToHub" >>"%APX_LOG%" 2>&1
md "%APX_TARGET%\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup" >>"%APX_LOG%" 2>&1
md "%APX_TARGET%\Windows\Setup\Scripts" >>"%APX_LOG%" 2>&1
md "%APX_TARGET%\APX\Drivers\Realtek8852AE" >>"%APX_LOG%" 2>&1
copy /B /Y "%APX_MEDIA%\APX\Payload\ReturnToHub\APX-ReturnToHub.ps1" "%APX_TARGET%\ProgramData\APX\ReturnToHub\APX-ReturnToHub.ps1" >>"%APX_LOG%" 2>&1 || call :fatal APX-PAYLOAD-01 return-powershell
copy /B /Y "%APX_MEDIA%\APX\Payload\ReturnToHub\README.txt" "%APX_TARGET%\ProgramData\APX\ReturnToHub\README.txt" >>"%APX_LOG%" 2>&1 || call :fatal APX-PAYLOAD-02 return-readme
copy /B /Y "%APX_MEDIA%\APX\Payload\ReturnToHub\APX-ReturnToHub.vbs" "%APX_TARGET%\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup\APX-ReturnToHub.vbs" >>"%APX_LOG%" 2>&1 || call :fatal APX-PAYLOAD-03 return-startup
copy /B /Y "%APX_MEDIA%\APX\Payload\ReturnToHub\APX-ProvisionHardware.cmd" "%APX_TARGET%\Windows\Setup\Scripts\SetupComplete.cmd" >>"%APX_LOG%" 2>&1 || call :fatal APX-PAYLOAD-04 setup-complete
xcopy /E /I /H /K /Y "%APX_MEDIA%\APX\Drivers\Realtek8852AE" "%APX_TARGET%\APX\Drivers\Realtek8852AE" >>"%APX_LOG%" 2>&1
if errorlevel 1 call :fatal APX-PAYLOAD-05 wifi-driver-copy
X:\Windows\System32\dism.exe /Image:%APX_TARGET%\ /Add-Driver /Driver:%APX_MEDIA%\APX\Drivers\Realtek8852AE\netrtwlane6.inf >>"%APX_LOG%" 2>&1
if errorlevel 1 call :fatal APX-DRIVER-01 wifi-driver-offline

set "APX_STEP=windows-boot-manager"
set "APX_LAST_COMMAND=bcdboot"
X:\Windows\System32\bcdboot.exe %APX_TARGET%\Windows /s %APX_ESP% /f UEFI /v >>"%APX_LOG%" 2>&1
set "APX_LAST_EXIT=!ERRORLEVEL!"
>>"%APX_LOG%" echo COMMAND !APX_LAST_COMMAND! exit=!APX_LAST_EXIT!
if not "!APX_LAST_EXIT!"=="0" call :fatal APX-BCD-01 bcdboot
if not exist "%APX_ESP%\EFI\Microsoft\Boot\bootmgfw.efi" call :fatal APX-BCD-02 bootmgfw
if not exist "%APX_ESP%\EFI\Microsoft\Boot\BCD" call :fatal APX-BCD-03 bcd-store
X:\Windows\System32\bcdedit.exe /store %APX_ESP%\EFI\Microsoft\Boot\BCD /enum {default} /v >"%APX_MEDIA%\APX\bcd-loader-v2.txt" 2>&1
if errorlevel 1 call :fatal APX-BCD-04 bcd-loader-enumeration
call :file_has_key_exact "%APX_MEDIA%\APX\bcd-loader-v2.txt" "device" "partition=%APX_TARGET%" || call :fatal APX-BCD-05 loader-device
call :file_has_key_exact "%APX_MEDIA%\APX\bcd-loader-v2.txt" "osdevice" "partition=%APX_TARGET%" || call :fatal APX-BCD-06 loader-osdevice
call :file_has_key_exact "%APX_MEDIA%\APX\bcd-loader-v2.txt" "path" "\Windows\system32\winload.efi" || call :fatal APX-BCD-07 loader-path
X:\Windows\System32\bcdedit.exe /sysstore %APX_ESP% >>"%APX_LOG%" 2>&1
if errorlevel 1 call :fatal APX-BCD-08 firmware-system-store
X:\Windows\System32\bcdedit.exe /set {bootmgr} device partition=%APX_ESP% >>"%APX_LOG%" 2>&1
if errorlevel 1 call :fatal APX-BCD-09 firmware-boot-device
X:\Windows\System32\bcdedit.exe /set {bootmgr} path \EFI\Microsoft\Boot\bootmgfw.efi >>"%APX_LOG%" 2>&1
if errorlevel 1 call :fatal APX-BCD-10 firmware-boot-path
X:\Windows\System32\bcdedit.exe /set {fwbootmgr} displayorder {bootmgr} /addlast >>"%APX_LOG%" 2>&1
if errorlevel 1 call :fatal APX-BCD-11 firmware-register
X:\Windows\System32\bcdedit.exe /enum {bootmgr} /v >"%APX_MEDIA%\APX\bcd-firmware-manager-v2.txt" 2>&1
if errorlevel 1 call :fatal APX-BCD-12 firmware-manager-enumeration
call :file_has_key_exact "%APX_MEDIA%\APX\bcd-firmware-manager-v2.txt" "device" "partition=%APX_ESP%" || call :fatal APX-BCD-13 firmware-manager-device
call :file_has_key_exact "%APX_MEDIA%\APX\bcd-firmware-manager-v2.txt" "path" "\EFI\Microsoft\Boot\bootmgfw.efi" || call :fatal APX-BCD-14 firmware-manager-path
X:\Windows\System32\bcdedit.exe /enum firmware /v >"%APX_MEDIA%\APX\bcd-firmware-v2.txt" 2>&1
if errorlevel 1 call :fatal APX-BCD-15 firmware-enumeration
X:\Windows\System32\find.exe /I "\EFI\Microsoft\Boot\bootmgfw.efi" "%APX_MEDIA%\APX\bcd-firmware-v2.txt" >nul || call :fatal APX-BCD-16 firmware-entry
if not exist "%APX_ESP%\EFI\systemd\systemd-bootx64.efi" call :fatal APX-BCD-17 linux-boot-preservation
if not exist "%APX_MEDIA%\sources\install.swm" call :fatal APX-BCD-18 setup-preservation

set "APX_STEP=success-record"
>"%APX_MEDIA%\APX\install-status-v2.ini" echo profile=apx-native-windows-install-status-v2
>>"%APX_MEDIA%\APX\install-status-v2.ini" echo generation=!APX_generation!
>>"%APX_MEDIA%\APX\install-status-v2.ini" echo status=boot-prepared
>>"%APX_MEDIA%\APX\install-status-v2.ini" echo image_index=6
>>"%APX_MEDIA%\APX\install-status-v2.ini" echo windows_partition_guid=!APX_windows_partition_guid!
>>"%APX_MEDIA%\APX\install-status-v2.ini" echo esp_partition_guid=!APX_efi_partition_guid!
>>"%APX_MEDIA%\APX\install-status-v2.ini" echo target_letter=!APX_LETTER_WINDOWS!:
>>"%APX_MEDIA%\APX\install-status-v2.ini" echo esp_letter=!APX_LETTER_EFI!:
copy /B /Y "%APX_MEDIA%\APX\install-status-v2.ini" "%APX_ESP%\EFI\APX\native-windows\install-status-v2.ini" >>"%APX_LOG%" 2>&1 || call :fatal APX-STATUS-01 efi-status-copy
X:\Windows\System32\fc.exe /B "%APX_MEDIA%\APX\install-status-v2.ini" "%APX_ESP%\EFI\APX\native-windows\install-status-v2.ini" >nul
if errorlevel 1 call :fatal APX-STATUS-02 efi-status-validation
copy /B /Y "%APX_LOG%" "%APX_MEDIA%\APX\install-log-v2.txt" >nul 2>&1
echo APX: Windows 11 Pro was applied and its UEFI boot was validated.
echo APX: returning to Linux so APX can perform the first controlled Windows boot.
X:\Windows\System32\wpeutil.exe reboot
exit /b 0

:load_expected
if not exist "%APX_EXPECTED%" exit /b 1
for /f "usebackq tokens=1,* delims==" %%A in ("%APX_EXPECTED%") do set "APX_%%A=%%B"
if not "!APX_profile!"=="apx-native-windows-install-contract-v2" exit /b 1
if not "!APX_disk_guid!"=="AC9FC0BD-2162-43A9-AAE6-3F654FF6F275" exit /b 1
if not "!APX_disk_bytes!"=="512110190592" exit /b 1
if not "!APX_efi_partition_guid!"=="9625F250-9ACC-453A-AE63-0C863ADE440F" exit /b 1
if not "!APX_efi_start_sector!"=="2048" exit /b 1
if not "!APX_efi_sector_count!"=="2097152" exit /b 1
if not "!APX_linux_partition_guid!"=="8835C8F0-F02F-4FC2-9035-5DBBC191DF9E" exit /b 1
if not "!APX_linux_start_sector!"=="2099200" exit /b 1
if not "!APX_windows_partition_guid!"=="099C31D8-313A-4ABA-B0E0-2B59502C9674" exit /b 1
if not "!APX_setup_partition_guid!"=="309BEBB6-5C32-4E21-9C92-6D758E51389D" exit /b 1
if not "!APX_setup_start_sector!"=="981340160" exit /b 1
if not "!APX_setup_sector_count!"=="18874368" exit /b 1
if not "!APX_image_index!"=="6" exit /b 1
if "!APX_size_gib!"=="80" if "!APX_windows_start_sector!:!APX_windows_sector_count!:!APX_linux_sector_count!"=="832442368:148897792:830343168" (
    set "APX_WINDOWS_SIZE_TEXT=71 GB"
    set "APX_LINUX_SIZE_TEXT=395 GB"
    exit /b 0
)
if "!APX_size_gib!"=="120" if "!APX_windows_start_sector!:!APX_windows_sector_count!:!APX_linux_sector_count!"=="748556288:232783872:746457088" (
    set "APX_WINDOWS_SIZE_TEXT=111 GB"
    set "APX_LINUX_SIZE_TEXT=355 GB"
    exit /b 0
)
if "!APX_size_gib!"=="160" if "!APX_windows_start_sector!:!APX_windows_sector_count!:!APX_linux_sector_count!"=="664670208:316669952:662571008" (
    set "APX_WINDOWS_SIZE_TEXT=151 GB"
    set "APX_LINUX_SIZE_TEXT=315 GB"
    exit /b 0
)
exit /b 1

:find_disk
set "APX_DISK_COUNT=0"
for /L %%D in (0,1,15) do (
    >"%APX_DP_SCRIPT%" echo select disk %%D
    >>"%APX_DP_SCRIPT%" echo uniqueid disk
    >>"%APX_DP_SCRIPT%" echo list disk
    >>"%APX_DP_SCRIPT%" echo exit
    X:\Windows\System32\diskpart.exe /s "%APX_DP_SCRIPT%" >"%APX_DP_OUTPUT%" 2>&1
    X:\Windows\System32\find.exe /I "!APX_disk_guid!" "%APX_DP_OUTPUT%" >nul
    if not errorlevel 1 (
        call :file_selected_size "%APX_DP_OUTPUT%" "476 GB"
        if not errorlevel 1 (
            set /A APX_DISK_COUNT+=1
            set "APX_DISK=%%D"
        )
    )
)
if not "!APX_DISK_COUNT!"=="1" exit /b 1
>>"%APX_LOG%" echo Exact GPT disk located as Disk !APX_DISK!.
exit /b 0

:find_partition
set "APX_ROLE=%~1"
set "APX_TYPE=%~2"
set "APX_LABEL=%~3"
set "APX_SIZE=%~4"
set "APX_PART_COUNT=0"
for /L %%P in (1,1,16) do (
    >"%APX_DP_SCRIPT%" echo select disk !APX_DISK!
    >>"%APX_DP_SCRIPT%" echo select partition %%P
    >>"%APX_DP_SCRIPT%" echo detail partition
    >>"%APX_DP_SCRIPT%" echo list partition
    >>"%APX_DP_SCRIPT%" echo exit
    X:\Windows\System32\diskpart.exe /s "%APX_DP_SCRIPT%" >"%APX_DP_OUTPUT%" 2>&1
    set "APX_PROBE_EXIT=!ERRORLEVEL!"
    set "APX_TYPE_MATCH=0"
    set "APX_SIZE_MATCH=0"
    set "APX_LABEL_MATCH=0"
    X:\Windows\System32\find.exe /I "!APX_TYPE!" "%APX_DP_OUTPUT%" >nul
    if not errorlevel 1 set "APX_TYPE_MATCH=1"
    call :file_selected_size "%APX_DP_OUTPUT%" "!APX_SIZE!"
    if not errorlevel 1 set "APX_SIZE_MATCH=1"
    if "!APX_LABEL!"=="-" (
        set "APX_LABEL_MATCH=not-required"
    ) else (
        X:\Windows\System32\find.exe /I "!APX_LABEL!" "%APX_DP_OUTPUT%" >nul
        if not errorlevel 1 set "APX_LABEL_MATCH=1"
    )
    >>"%APX_LOG%" echo PARTITION_PROBE role=!APX_ROLE! partition=%%P diskpart_exit=!APX_PROBE_EXIT! type_match=!APX_TYPE_MATCH! size_match=!APX_SIZE_MATCH! label_match=!APX_LABEL_MATCH!
    >>"%APX_LOG%" echo ----- diskpart role=!APX_ROLE! partition=%%P -----
    >>"%APX_LOG%" type "%APX_DP_OUTPUT%"
    if "!APX_TYPE_MATCH!:!APX_SIZE_MATCH!:!APX_LABEL_MATCH!"=="1:1:1" (
        set /A APX_PART_COUNT+=1
        set "APX_PART_!APX_ROLE!=%%P"
    )
    if "!APX_TYPE_MATCH!:!APX_SIZE_MATCH!:!APX_LABEL_MATCH!"=="1:1:not-required" (
        set /A APX_PART_COUNT+=1
        set "APX_PART_!APX_ROLE!=%%P"
    )
)
if not "!APX_PART_COUNT!"=="1" (
    set "APX_LAST_COMMAND=diskpart-partition-probe"
    set "APX_LAST_EXIT=1"
    set "APX_DIAGNOSTIC=role=!APX_ROLE! candidates=!APX_PART_COUNT! required_type=!APX_TYPE! required_size=!APX_SIZE! required_label=!APX_LABEL!"
    exit /b 1
)
if "!APX_LABEL!"=="-" (
    >>"%APX_LOG%" echo !APX_ROLE! located as unique partition !APX_PART_%APX_ROLE%! by GPT type and size; full volume identity is still untrusted.
) else (
    >>"%APX_LOG%" echo !APX_ROLE! located as unique partition !APX_PART_%APX_ROLE%! by GPT type, size and tabular label.
)
exit /b 0

:choose_letter
set "APX_LETTER_ROLE=%~1"
set "APX_LETTER_PREFERRED=%~2"
set "APX_LETTER_FOUND="
for %%L in (!APX_LETTER_PREFERRED! W C S R T U V Y Z Q P O N M L K J I H G F E D) do if not defined APX_LETTER_FOUND (
    vol %%L: >nul 2>&1
    if errorlevel 1 set "APX_LETTER_FOUND=%%L"
)
if not defined APX_LETTER_FOUND exit /b 1
set "APX_LETTER_!APX_LETTER_ROLE!=!APX_LETTER_FOUND!"
>>"%APX_LOG%" echo !APX_LETTER_ROLE! will use free temporary letter !APX_LETTER_FOUND!:.
exit /b 0

:mount_partition
if /I "%~3"=="WINDOWS" (
    call :mount_basic_partition %~1 %~2 %~3 %~4
) else (
    call :mount_named_volume %~2 %~3 %~4
)
if errorlevel 1 exit /b 1
>>"%APX_LOG%" echo %~3 mounted temporarily as %~2: after identity validation.
exit /b 0

:mount_basic_partition
set "APX_MOUNT_PART=%~1"
set "APX_MOUNT_LETTER=%~2"
set "APX_MOUNT_ROLE=%~3"
set "APX_MOUNT_LABEL=%~4"
>"%APX_DP_SCRIPT%" echo select disk !APX_DISK!
>>"%APX_DP_SCRIPT%" echo select partition !APX_MOUNT_PART!
>>"%APX_DP_SCRIPT%" echo assign letter=!APX_MOUNT_LETTER!
>>"%APX_DP_SCRIPT%" echo detail partition
>>"%APX_DP_SCRIPT%" echo exit
X:\Windows\System32\diskpart.exe /s "%APX_DP_SCRIPT%" >"%APX_DP_OUTPUT%" 2>&1
if errorlevel 1 exit /b 1
vol !APX_MOUNT_LETTER!: >"%APX_DP_OUTPUT%" 2>&1
if errorlevel 1 exit /b 1
X:\Windows\System32\find.exe /I "!APX_MOUNT_LABEL!" "%APX_DP_OUTPUT%" >nul
if errorlevel 1 (
    set "APX_LAST_COMMAND=verify-full-volume-label"
    set "APX_LAST_EXIT=1"
    set "APX_DIAGNOSTIC=role=!APX_MOUNT_ROLE! partition=!APX_MOUNT_PART! expected_label=!APX_MOUNT_LABEL!"
    >>"%APX_LOG%" type "%APX_DP_OUTPUT%"
    exit /b 1
)
>>"%APX_LOG%" echo FULL_VOLUME_LABEL role=!APX_MOUNT_ROLE! partition=!APX_MOUNT_PART! label=!APX_MOUNT_LABEL! match=1
exit /b 0

:mount_named_volume
set "APX_MOUNT_LETTER=%~1"
set "APX_MOUNT_ROLE=%~2"
set "APX_MOUNT_LABEL=%~3"
set "APX_VOLUME_COUNT=0"
set "APX_VOLUME_SELECTED="
X:\Windows\System32\mountvol.exe >"%APX_MOUNT_LIST%" 2>&1
if errorlevel 1 exit /b 1
for /f "usebackq tokens=*" %%V in ("%APX_MOUNT_LIST%") do (
    set "APX_VOLUME_CANDIDATE=%%V"
    if /I "!APX_VOLUME_CANDIDATE:~0,11!"=="\\?\Volume{" (
        X:\Windows\System32\mountvol.exe !APX_MOUNT_LETTER!: !APX_VOLUME_CANDIDATE! >"%APX_DP_OUTPUT%" 2>&1
        if not errorlevel 1 (
            vol !APX_MOUNT_LETTER!: >"%APX_DP_OUTPUT%" 2>&1
            if not errorlevel 1 (
                X:\Windows\System32\find.exe /I "!APX_MOUNT_LABEL!" "%APX_DP_OUTPUT%" >nul
                if not errorlevel 1 (
                    set /A APX_VOLUME_COUNT+=1
                    set "APX_VOLUME_SELECTED=!APX_VOLUME_CANDIDATE!"
                )
            )
            X:\Windows\System32\mountvol.exe !APX_MOUNT_LETTER!: /D >nul 2>&1
        )
    )
)
if not "!APX_VOLUME_COUNT!"=="1" exit /b 1
X:\Windows\System32\mountvol.exe !APX_MOUNT_LETTER!: !APX_VOLUME_SELECTED! >"%APX_DP_OUTPUT%" 2>&1
if errorlevel 1 exit /b 1
vol !APX_MOUNT_LETTER!: >"%APX_DP_OUTPUT%" 2>&1
if errorlevel 1 exit /b 1
X:\Windows\System32\find.exe /I "!APX_MOUNT_LABEL!" "%APX_DP_OUTPUT%" >nul || exit /b 1
X:\Windows\System32\mountvol.exe !APX_MOUNT_LETTER!: /L >"%APX_DP_OUTPUT%" 2>&1
if errorlevel 1 exit /b 1
X:\Windows\System32\find.exe /I "!APX_VOLUME_SELECTED!" "%APX_DP_OUTPUT%" >nul || exit /b 1
exit /b 0

:file_selected_size
set "APX_SEARCH_FOUND="
for /f "usebackq tokens=1,*" %%A in ("%~1") do if "%%A"=="*" (
    set "APX_SEARCH_LINE=%%B"
    if /I not "!APX_SEARCH_LINE:%~2=!"=="!APX_SEARCH_LINE!" set "APX_SEARCH_FOUND=1"
)
if defined APX_SEARCH_FOUND exit /b 0
exit /b 1

:file_has_key_value
set "APX_SEARCH_FOUND="
for /f "usebackq tokens=1,*" %%A in ("%~1") do if /I "%%A"=="%~2" (
    set "APX_SEARCH_LINE=%%B"
    if /I not "!APX_SEARCH_LINE:%~3=!"=="!APX_SEARCH_LINE!" set "APX_SEARCH_FOUND=1"
)
if defined APX_SEARCH_FOUND exit /b 0
exit /b 1

:file_has_key_exact
set "APX_SEARCH_FOUND="
for /f "usebackq tokens=1,*" %%A in ("%~1") do if /I "%%A"=="%~2" if /I "%%B"=="%~3" set "APX_SEARCH_FOUND=1"
if defined APX_SEARCH_FOUND exit /b 0
exit /b 1

:validate_contract
if not exist "%~1" exit /b 1
X:\Windows\System32\fc.exe /B "%APX_EXPECTED%" "%~1" >nul
exit /b %ERRORLEVEL%

:fatal
set "APX_ERROR=%~1"
set "APX_DETAIL=%~2"
set "APX_FATAL_ENTRY_EXIT=!ERRORLEVEL!"
if "!APX_LAST_EXIT!"=="0" set "APX_LAST_EXIT=!APX_FATAL_ENTRY_EXIT!"
if "!APX_LAST_EXIT!"=="0" set "APX_LAST_EXIT=1"
if not defined APX_LAST_COMMAND set "APX_LAST_COMMAND=unknown"
if not defined APX_DIAGNOSTIC set "APX_DIAGNOSTIC=none"
>>"%APX_LOG%" echo FAILED !APX_ERROR! at !APX_STEP!: !APX_DETAIL! command=!APX_LAST_COMMAND! exit=!APX_LAST_EXIT! diagnostic=!APX_DIAGNOSTIC!
echo.
echo APX Windows installation stopped safely: !APX_ERROR!
echo Stage: !APX_STEP! / !APX_DETAIL!
echo Command: !APX_LAST_COMMAND! / exit !APX_LAST_EXIT!
echo Diagnostic: !APX_DIAGNOSTIC!
echo Only an authenticated Windows target may have been changed. APX/Linux and setup are retained.
if defined APX_MEDIA if exist "%APX_MEDIA%\APX\" (
    >"%APX_MEDIA%\APX\install-status-v2.ini" echo profile=apx-native-windows-install-status-v2
    >>"%APX_MEDIA%\APX\install-status-v2.ini" echo generation=!APX_generation!
    >>"%APX_MEDIA%\APX\install-status-v2.ini" echo status=failed
    >>"%APX_MEDIA%\APX\install-status-v2.ini" echo error=!APX_ERROR!
    >>"%APX_MEDIA%\APX\install-status-v2.ini" echo step=!APX_STEP!
    >>"%APX_MEDIA%\APX\install-status-v2.ini" echo detail=!APX_DETAIL!
    >>"%APX_MEDIA%\APX\install-status-v2.ini" echo command=!APX_LAST_COMMAND!
    >>"%APX_MEDIA%\APX\install-status-v2.ini" echo exit_code=!APX_LAST_EXIT!
    >>"%APX_MEDIA%\APX\install-status-v2.ini" echo diagnostic=!APX_DIAGNOSTIC!
    copy /B /Y "%APX_LOG%" "%APX_MEDIA%\APX\install-log-v2.txt" >nul 2>&1
)
if defined APX_ESP if exist "%APX_ESP%\EFI\APX\native-windows\" (
    if defined APX_MEDIA if exist "%APX_MEDIA%\APX\install-status-v2.ini" copy /B /Y "%APX_MEDIA%\APX\install-status-v2.ini" "%APX_ESP%\EFI\APX\native-windows\install-status-v2.ini" >nul 2>&1
    copy /B /Y "%APX_LOG%" "%APX_ESP%\EFI\APX\native-windows\install-log-v2.txt" >nul 2>&1
)
echo.
echo Failure evidence was retained. Press any key to return to APX Linux.
pause >nul
X:\Windows\System32\wpeutil.exe reboot
:fatal_wait
goto fatal_wait
