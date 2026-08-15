pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import Quickshell.Wayland

ShellRoot {
    id: root

    property color cyan: "#55e6ff"
    property color cyanDim: "#246879"
    property color panel: "#e90a1014"
    property color card: "#f2162027"
    property color textMain: "#e8f7fa"
    property color textDim: "#8aa3aa"
    property var environmentIdentity: ({ name: "", display_name: "", role: "" })
    property string environmentSwitchError: ""
    property bool environmentSwitchPending: false
    property int environmentSwitchProgress: 0
    property var environmentCatalog: []
    property string selectedEnvironmentName: ""
    property string selectedEnvironmentGeneration: ""
    property bool environmentCreateOpen: false
    property bool environmentDeleteConfirm: false
    property int environmentDeleteFocusIndex: 0
    property string environmentDraftName: ""
    property string environmentDraftDescription: ""
    property string environmentDesktopPreset: "intermediate"
    property string environmentFeatureDrawer: ""
    property string environmentFeatureInfo: ""
    property var environmentSelectedModules: ({})
    readonly property var environmentModuleCatalog: [
        { key: "system", label: "Núcleo do sistema", detail: "Arranque, certificados e comandos essenciais.", programs: "BASE · base, ca-certificates, iproute2, less, nano", mib: 420, deps: [] },
        { key: "cli-aur", label: "Terminal e instalação", detail: "Terminal, ajuda, Git e compilação de pacotes AUR.", programs: "BASE · Alacritty, Foot, Git, man, sudo, base-devel", mib: 260, deps: ["system"] },
        { key: "graphical", label: "Ambiente gráfico", detail: "Janelas, bloqueio, menu de aplicações e barra APX.", programs: "BASE · Hyprland, Hyprlock, Rofi, QuickShell", mib: 520, deps: ["system"] },
        { key: "desktop-integration", label: "Integração do desktop", detail: "Notificações, portais, segredos e aplicações Flatpak.", programs: "BASE · Mako, Flatpak, Polkit, GNOME Keyring", mib: 170, deps: ["graphical"] },
        { key: "locale-input", label: "Português, fontes e teclado", detail: "Acentos, layout do teclado, fontes e diretórios pessoais.", programs: "BASE · Noto Fonts, xkeyboard-config, xdg-user-dirs", mib: 190, deps: ["system"] },
        { key: "network", label: "Wi-Fi e Internet", detail: "Acesso à Internet e controlo de redes pela APX.", programs: "BASE · integração APX, iproute2, iputils", mib: 70, deps: ["system"] },
        { key: "bluetooth", label: "Bluetooth", detail: "Ligar, emparelhar e esquecer dispositivos Bluetooth.", programs: "BASE · controlo Bluetooth mediado pela APX", mib: 35, deps: ["system"] },
        { key: "audio", label: "Som e microfone", detail: "Reprodução, gravação e controlos de volume.", programs: "BASE · PipeWire, WirePlumber", mib: 125, deps: ["system"] },
        { key: "graphics", label: "Aceleração gráfica e monitores", detail: "OpenGL/Vulkan e suporte para ecrãs internos e externos.", programs: "BASE · Mesa, Vulkan Radeon, NVIDIA HDMI/DisplayPort", mib: 390, deps: ["graphical"] },
        { key: "power", label: "Bateria e brilho", detail: "Estado da bateria, brilho do ecrã e teclado iluminado.", programs: "BASE · controlos de hardware mediados pela APX", mib: 30, deps: ["graphical"] },
        { key: "devices-storage", label: "USB, telemóvel e discos", detail: "Montagem assistida de discos, MTP, câmaras e partilhas SMB.", programs: "BASE · UDisks, udiskie, GVFS, MTP, SMB", mib: 120, deps: ["system"] },
        { key: "files", label: "Ficheiros, imagens e arquivos", detail: "Navegar em pastas, pré-visualizar imagens e abrir arquivos.", programs: "BASE · Thunar, File Roller, Ristretto, Tumbler", mib: 115, deps: ["desktop-integration", "devices-storage"] },
        { key: "web-documents", label: "Internet e documentos PDF", detail: "Navegação web e leitura de documentos PDF.", programs: "INSTALA · Brave, Evince", mib: 360, deps: ["desktop-integration", "network"] },
        { key: "multimedia", label: "Vídeo, áudio e codecs", detail: "Reproduzir formatos multimédia comuns.", programs: "INSTALA · MPV, FFmpeg, GStreamer codecs", mib: 240, deps: ["desktop-integration", "audio", "graphics"] },
        { key: "office", label: "Documentos e folhas de cálculo", detail: "Textos, apresentações, folhas de cálculo e correção ortográfica.", programs: "INSTALA · LibreOffice, Hunspell EN-GB", mib: 620, deps: ["desktop-integration", "locale-input"] },
        { key: "communication", label: "Câmara e videochamadas", detail: "Ferramentas de diagnóstico para webcam e vídeo.", programs: "INSTALA · v4l-utils", mib: 55, deps: ["desktop-integration", "network", "audio", "graphics"] },
        { key: "printing-scanning", label: "Impressoras e scanners", detail: "Configurar, imprimir e digitalizar documentos.", programs: "INSTALA · CUPS, SANE, Simple Scan, system-config-printer", mib: 145, deps: ["desktop-integration", "network", "devices-storage"] },
        { key: "development", label: "Programação e containers", detail: "Compilar software, desenvolver em várias linguagens e usar containers.", programs: "INSTALA · CMake, Ninja, Node.js, npm, Podman, pip, Rust", mib: 1150, deps: ["cli-aur"] },
        { key: "shortcuts", label: "Atalhos APX", detail: "Abrir rapidamente o controlo, calendário, bateria e Environments.", programs: "BASE · ponte de atalhos SUPER+A/B/D/E", mib: 8, deps: ["graphical"] }
    ]
    readonly property var environmentModuleGroups: [
        { key: "base", label: "1 · SISTEMA E AMBIENTE DE TRABALHO", description: "Terminal, janelas, idioma e integração do desktop", modules: ["system", "cli-aur", "graphical", "desktop-integration", "locale-input"] },
        { key: "hardware", label: "2 · INTERNET, SOM E DISPOSITIVOS", description: "Rede, Bluetooth, áudio, gráficos, bateria e USB", modules: ["network", "bluetooth", "audio", "graphics", "power", "devices-storage"] },
        { key: "daily", label: "3 · APLICAÇÕES DO DIA A DIA", description: "Ficheiros, browser, PDF, vídeo e codecs", modules: ["files", "web-documents", "multimedia"] },
        { key: "extras", label: "4 · TRABALHO E FERRAMENTAS AVANÇADAS", description: "Office, câmara, impressão, programação e containers", modules: ["office", "communication", "printing-scanning", "development"] },
        { key: "accessibility", label: "5 · ACESSIBILIDADE E ATALHOS", description: "Atalhos globais para abrir os menus APX", modules: ["shortcuts"] }
    ]
    property bool environmentKeyboardFocus: false
    property int environmentFocusIndex: -1
    property int environmentCreateFocusIndex: -1
    property bool environmentManagementBusy: false
    property var environmentManagementState: ({ phase: "idle", progress: 0, message: "" })
    property int environmentProgressReadFailures: 0
    property bool identityReady: false
    // Identity is normally Host-authorized, but a workload can be visible
    // before its active descriptor has finished publishing.  The Host-console
    // socket is mounted only in the official Hub, so it is a safe local role
    // proof during that startup window and never grants Host authority.
    property bool sessionKindReady: false
    property bool sessionHubProof: true
    readonly property bool isHub: identityReady
                                  ? environmentIdentity.role === "hub"
                                  : sessionHubProof
    readonly property string environmentClient: isHub
        ? "/home/.apx-host-bridge/environment-switch-client-v1.py"
        : "/run/apx/environment-switch-client-v1.py"
    readonly property string environmentLabel: isHub ? "HUB" : String(environmentIdentity.display_name || environmentIdentity.name || "ENVIRONMENT").toUpperCase()
    readonly property int environmentPopupHeight: !isHub ? 214
        : (environmentCreateOpen ? 540 + (environmentManagementBusy ? 42 : 0)
           : 216 + Math.max(1, Math.min(5, environmentCatalog.length)) * 66
             + (environmentDeleteConfirm ? 64 : 0) + (environmentManagementBusy ? 42 : 0))
    property string popupKind: ""
    property Item popupTarget: null
    property bool popupOpening: false
    readonly property int popupLeftMargin: {
        if (!popupTarget || !bar) return 8
        var targetRect = popupTarget.mapToItem(bar.contentItem, 0, 0)
        var targetCenter = targetRect.x + popupTarget.width / 2
        return Math.max(8, Math.min(bar.width - popup.implicitWidth - 8,
                                    Math.round(targetCenter - popup.implicitWidth / 2)))
    }
    property var hostState: ({})
    property string clockText: ""
    property string volumeText: "--"
    property int volumeValue: 0
    property bool volumeMuted: false
    property bool apxShortcutsEnabled: true
    property string batteryText: "--"
    property var hardwareProfile: ({ platform_profile: "unknown", gpu_profile: "unknown", requested_gpu_profile: "unknown", reboot_required: false })
    property bool hardwareBusy: false
    property bool hardwareConfirmOpen: false
    property bool hardwareApplied: false
    property string hardwareToken: ""
    property string hardwareTarget: ""
    property string hardwareMessage: ""
    property string hardwareStatusError: ""
    property string platformProfileError: ""
    property string gpuProfileError: ""
    property bool microphoneActive: false
    property int microphoneVolume: 0
    property bool microphoneMuted: false
    property string microphoneText: "--"
    property int displayBrightness: 50
    property int displayBrightnessPending: -1
    property int displayBrightnessInFlight: -1
    property int displayBrightnessLastSent: -1
    property int keyboardBrightness: 0
    property int keyboardBrightnessMax: 2
    property string hardwareControlError: ""
    property bool powerConfirmOpen: false
    property bool powerBusy: false
    property string powerAction: ""
    property string powerToken: ""
    property string powerMessage: ""
    property date calendarDate: new Date()
    property date currentDate: new Date()
    property string calendarView: "month"
    property var monthNames: ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
    property var weekNames: ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]
    property var calendarEvents: []
    property var calendarCategories: []
    property bool calendarEditor: false
    property string editingEventId: ""
    property bool categoryPickerOpen: false
    property bool newCategoryOpen: false
    property string newCategoryName: ""
    property string draftTitle: ""
    property string draftDate: ""
    property string draftTime: "09:00"
    property string draftCategory: ""
    property string draftNotes: ""
    property bool draftShared: false
    property bool draftActive: true
    property var draftReminders: []
    property string draftReminderAmount: "1"
    property string draftReminderUnit: "Horas"
    property string eventError: ""
    property bool controlsWifiOpen: false
    property bool controlsBluetoothOpen: false
    property bool controlsAudioOpen: false
    property bool controlsMicrophoneOpen: false
    property string wifiSelectedSsid: ""
    property string wifiPassword: ""
    property string wifiMessage: ""
    property bool wifiPasswordVisible: false
    property bool wifiSelectionTap: false
    property string wifiLastNetwork: ""
    property bool wifiManualOff: false
    property string wifiTogglePhase: ""
    property bool wifiOptimisticOverride: false
    property bool wifiOptimisticActive: false
    property string bluetoothMessage: ""
    property string bluetoothPowerPhase: ""
    property bool bluetoothPowerOverride: false
    property bool bluetoothPowerActive: false
    property string bluetoothDevicePendingAddress: ""
    property string bluetoothDevicePendingAction: ""
    property string bluetoothPairSessionId: ""
    property string bluetoothPairAddress: ""
    property string bluetoothPairName: ""
    property string bluetoothPairPhase: ""
    property string bluetoothPairChallenge: ""
    property string bluetoothPairPasskey: ""
    property string bluetoothPairPin: ""
    property string bluetoothPairResponsePin: ""
    property string bluetoothRemoveAddress: ""
    property string bluetoothRemoveName: ""
    property int menuTitleSize: 13
    property int menuBodySize: 10
    property int menuSmallSize: 9
    property int menuMetaSize: 8
    readonly property int environmentCreateModuleFocusBase: 6 + environmentModuleGroups.length
    readonly property int environmentCreateSubmitFocusIndex: environmentCreateModuleFocusBase + environmentModuleCatalog.length
    // Hyprland renders the display at 150%. Present the control centre at a
    // 125% physical compromise: readable on the internal panel while keeping
    // every common 16px icon aligned to an integer 20-device-pixel target.
    // Match the desktop scale exactly. Fractionally scaling the whole popup
    // forced SVG icons through an intermediate texture and softened corners.
    readonly property real controlCenterScale: 1
    property var modelStoreState: ({ state: "unknown", message: "A verificar o SSD do modelo…" })
    property bool modelStoreBusy: false
    property bool modelStoreConfirmDetach: false
    property string modelStoreError: ""
    property bool modelSwitchActive: false
    property string modelSwitchProfile: ""
    property string modelSwitchLabel: ""
    property int modelSwitchProgress: 0

    function two(value) { return value < 10 ? "0" + value : "" + value }

    function dateKey(date) {
        return date.getFullYear() + "-" + two(date.getMonth() + 1) + "-" + two(date.getDate())
    }

    function eventsForDate(date) {
        var key = dateKey(date)
        return calendarEvents.filter(function(event) { return event.date === key })
    }

    function sortedEventsForDate(date) {
        var events = eventsForDate(date).slice()
        events.sort(function(a, b) {
            return (a.time || "00:00").localeCompare(b.time || "00:00")
        })
        return events
    }

    function wifiIsKnown(name) {
        return (hostState.known_networks || []).indexOf(name) >= 0
    }

    function wifiIsOpen(name) {
        return (hostState.open_networks || []).indexOf(name) >= 0
    }

    function wifiSecurityLabel(name) {
        if (wifiIsOpen(name)) return "ABERTA"
        if (wifiIsKnown(name)) return "GUARDADA"
        return "PALAVRA-PASSE"
    }

    function wifiDetails(name) {
        var details = hostState.network_details || []
        for (var i = 0; i < details.length; ++i)
            if (details[i].ssid === name) return details[i]
        return ({ ssid: name, signal: 0, security: "unknown", known: false })
    }

    function wifiSignalBars(signal) {
        if (signal >= 75) return "▂▄▆█"
        if (signal >= 50) return "▂▄▆·"
        if (signal >= 25) return "▂▄··"
        return "▂···"
    }

    function wifiConnectivityLabel() {
        var state = hostState.network_connectivity || "unknown"
        if (state === "full") return "● INTERNET DISPONÍVEL"
        if (state === "portal") return "⚠ AUTENTICAÇÃO NECESSÁRIA"
        if (state === "limited") return "△ LIGAÇÃO LIMITADA"
        if (state === "none") return "○ SEM INTERNET"
        return "◌ A VERIFICAR INTERNET"
    }

    function wifiConnectivityColor() {
        var state = hostState.network_connectivity || "unknown"
        if (state === "full") return cyan
        if (state === "portal") return "#ffd09a"
        if (state === "limited" || state === "none") return "#ff91a4"
        return textDim
    }

    function beginWifiConnect(name) {
        wifiMessage = ""
        wifiSelectedSsid = name
        wifiPassword = ""
        wifiPasswordVisible = true
        if (!wifiIsKnown(name) && !wifiIsOpen(name))
            wifiPasswordInput.forceActiveFocus()
    }

    function cancelWifiPassword() {
        wifiPassword = ""
        wifiSelectedSsid = ""
        wifiPasswordVisible = false
    }

    function submitWifiPassword() {
        if (wifiIsKnown(wifiSelectedSsid) || wifiIsOpen(wifiSelectedSsid)) {
            wifiMessage = "A ligar a " + wifiSelectedSsid + "…"
            hostAction("wifi-connect", wifiSelectedSsid)
            return
        }
        if (wifiCredentialProcess.running || wifiPassword.length < 8) {
            wifiMessage = wifiPassword.length < 8 ? "A palavra-passe deve ter pelo menos 8 caracteres." : "Ligação em curso…"
            return
        }
        wifiMessage = "A ligar a " + wifiSelectedSsid + "…"
        wifiCredentialProcess.command = ["/run/apx/host-services-client-v3.py", "wifi-connect", wifiSelectedSsid, "--credential-stdin"]
        wifiCredentialProcess.running = true
    }

    function toggleWifiConnection() {
        if (wifiToggleProcess.running || wifiTogglePhase.length) return
        if (hostState.network_name) {
            wifiLastNetwork = hostState.network_name
            wifiManualOff = true
            wifiTogglePhase = "disconnecting"
            wifiOptimisticOverride = true
            wifiOptimisticActive = false
            wifiToggleProcess.command = ["/run/apx/host-services-ui-v3.py", "wifi-disconnect"]
            wifiToggleProcess.running = true
            return
        }
        var target = wifiLastNetwork
        if (!target.length) {
            var nearby = hostState.available_networks || []
            for (var i = 0; i < nearby.length; ++i) {
                if (wifiIsKnown(nearby[i])) {
                    target = nearby[i]
                    break
                }
            }
        }
        if (target.length) {
            wifiManualOff = false
            wifiTogglePhase = "connecting"
            wifiOptimisticOverride = true
            wifiOptimisticActive = true
            wifiToggleProcess.command = ["/run/apx/host-services-ui-v3.py", "wifi-connect", target]
            wifiToggleProcess.running = true
        } else {
            wifiManualOff = false
            hostAction("wifi-scan")
        }
    }

    function wifiDisplayActive() {
        return wifiOptimisticOverride ? wifiOptimisticActive : !!hostState.network_name
    }

    function bluetoothDisplayPowered() {
        return bluetoothPowerOverride ? bluetoothPowerActive : hostState.bluetooth_powered === true
    }

    function toggleBluetoothPower() {
        if (bluetoothPowerProcess.running || bluetoothPowerPhase.length) return
        var next = !bluetoothDisplayPowered()
        bluetoothPowerPhase = next ? "turning-on" : "turning-off"
        bluetoothPowerOverride = true
        bluetoothPowerActive = next
        bluetoothPowerProcess.command = ["/run/apx/host-services-ui-v3.py", "bluetooth-power", next ? "on" : "off"]
        bluetoothPowerProcess.running = true
    }

    function bluetoothDeviceAction(operation, device) {
        if (bluetoothDeviceActionProcess.running || bluetoothDevicePendingAddress.length) return
        bluetoothDevicePendingAddress = device.address
        bluetoothDevicePendingAction = operation
        bluetoothDeviceActionProcess.command = ["/run/apx/host-services-ui-v3.py", operation, device.address]
        bluetoothDeviceActionProcess.running = true
    }

    function openControlSection(section) {
        if (wifiPasswordVisible)
            cancelWifiPassword()
        var wasOpen = section === "wifi" ? controlsWifiOpen
                    : section === "bluetooth" ? controlsBluetoothOpen
                    : section === "microphone" ? controlsMicrophoneOpen
                    : controlsAudioOpen
        controlsWifiOpen = section === "wifi" && !wasOpen
        controlsBluetoothOpen = section === "bluetooth" && !wasOpen
        controlsAudioOpen = section === "audio" && !wasOpen
        controlsMicrophoneOpen = section === "microphone" && !wasOpen
        if (controlsAudioOpen)
            Qt.callLater(function() { volumeSlider.forceActiveFocus() })
        else if (controlsMicrophoneOpen)
            Qt.callLater(function() { microphoneSlider.forceActiveFocus() })
    }

    function controlsAllClosed() {
        return !controlsWifiOpen && !controlsBluetoothOpen && !controlsAudioOpen && !controlsMicrophoneOpen
    }

    function bluetoothConnectedDevices() {
        if (!bluetoothDisplayPowered()) return []
        return (hostState.bluetooth_devices || []).filter(function(device) {
            return device.paired === true && device.connected === true
                   && !(bluetoothDevicePendingAction === "bluetooth-disconnect" && bluetoothDevicePendingAddress === device.address)
        })
    }

    function bluetoothKnownDevices() {
        if (!bluetoothDisplayPowered()) return []
        return (hostState.bluetooth_devices || []).filter(function(device) {
            if (device.paired !== true) return false
            if (bluetoothDevicePendingAction === "bluetooth-disconnect" && bluetoothDevicePendingAddress === device.address) return true
            return device.connected !== true
        })
    }

    function bluetoothAvailableDevices() {
        if (!bluetoothDisplayPowered()) return []
        return (hostState.bluetooth_devices || []).filter(function(device) { return device.paired !== true })
    }

    function applyBluetoothPairResult(payload) {
        bluetoothPairSessionId = payload.session_id || bluetoothPairSessionId
        bluetoothPairPhase = payload.phase || "waiting"
        bluetoothPairChallenge = payload.challenge || ""
        bluetoothPairPasskey = payload.passkey === undefined || payload.passkey === null ? "" : String(payload.passkey)
        bluetoothMessage = payload.message || ""
        if (bluetoothPairPhase === "completed") {
            bluetoothMessage = bluetoothPairName + " emparelhado com sucesso."
            bluetoothPairPin = ""
            hostStatusProcess.running = true
        } else if (bluetoothPairPhase === "failed") {
            bluetoothMessage = payload.message || "Não foi possível emparelhar " + bluetoothPairName + "."
            bluetoothPairPin = ""
            hostStatusProcess.running = true
        }
    }

    function beginBluetoothPair(device) {
        if (bluetoothPairBeginProcess.running || bluetoothPairSessionId.length) return
        bluetoothMessage = "A iniciar o emparelhamento…"
        bluetoothPairAddress = device.address
        bluetoothPairName = device.name || device.address
        bluetoothPairPhase = "starting"
        bluetoothPairChallenge = ""
        bluetoothPairPasskey = ""
        bluetoothPairPin = ""
        bluetoothPairBeginProcess.command = ["/run/apx/host-services-client-v3.py", "bluetooth-pair", device.address]
        bluetoothPairBeginProcess.running = true
    }

    function respondBluetoothPair(accepted, pin) {
        if (!bluetoothPairSessionId.length || bluetoothPairRespondProcess.running) return
        bluetoothPairResponsePin = pin || ""
        var args = ["/run/apx/host-services-client-v3.py", "bluetooth-pair-respond", bluetoothPairSessionId,
                    "--accept", accepted ? "yes" : "no"]
        if (bluetoothPairResponsePin.length) args.push("--credential-stdin")
        bluetoothPairRespondProcess.command = args
        bluetoothPairRespondProcess.running = true
        bluetoothMessage = accepted ? "A confirmar…" : "A cancelar…"
    }

    function cancelBluetoothPairing() {
        if (bluetoothPairPhase === "needs-response") {
            respondBluetoothPair(false, "")
            return
        }
        bluetoothPairSessionId = ""
        bluetoothPairAddress = ""
        bluetoothPairName = ""
        bluetoothPairPhase = ""
        bluetoothPairChallenge = ""
        bluetoothPairPasskey = ""
        bluetoothPairPin = ""
        bluetoothMessage = "Emparelhamento cancelado."
    }

    function dismissBluetoothPairing() {
        bluetoothPairSessionId = ""
        bluetoothPairAddress = ""
        bluetoothPairName = ""
        bluetoothPairPhase = ""
        bluetoothPairChallenge = ""
        bluetoothPairPasskey = ""
        bluetoothPairPin = ""
    }

    function beginBluetoothRemove(device) {
        bluetoothRemoveAddress = device.address
        bluetoothRemoveName = device.name || device.address
        bluetoothMessage = ""
    }

    function confirmBluetoothRemove() {
        if (!bluetoothRemoveAddress.length || bluetoothRemoveProcess.running) return
        bluetoothRemoveProcess.command = ["/run/apx/host-services-client-v3.py", "bluetooth-remove", bluetoothRemoveAddress]
        bluetoothRemoveProcess.running = true
    }

    function beginEvent() {
        editingEventId = ""
        draftTitle = ""
        draftDate = dateKey(new Date())
        draftTime = "09:00"
        draftCategory = calendarCategories.length ? calendarCategories[0] : ""
        draftNotes = ""
        draftShared = false
        draftActive = true
        draftReminders = []
        draftReminderAmount = "1"
        draftReminderUnit = "Horas"
        eventError = ""
        categoryPickerOpen = false
        newCategoryOpen = false
        calendarEditor = true
    }

    function beginEditEvent(event) {
        editingEventId = event.id
        draftTitle = event.title || ""
        draftDate = event.date || dateKey(new Date())
        draftTime = event.time || "09:00"
        draftCategory = event.category || ""
        draftNotes = event.notes || ""
        draftShared = event.scope === "shared"
        draftActive = event.active !== false
        draftReminders = (event.reminders || []).slice()
        setReminderDraft(draftReminders.length ? draftReminders[0] : 60)
        eventError = ""
        categoryPickerOpen = false
        newCategoryOpen = false
        calendarEditor = true
    }

    function createCategory() {
        var name = newCategoryName.trim().toUpperCase()
        if (!name) return
        if (calendarCategories.indexOf(name) < 0)
            calendarCategories = calendarCategories.concat([name]).sort()
        draftCategory = name
        newCategoryName = ""
        newCategoryOpen = false
        categoryPickerOpen = false
        persistEvents()
    }

    function toggleReminder(minutes) {
        var reminders = draftReminders.slice()
        var index = reminders.indexOf(minutes)
        if (index >= 0) reminders.splice(index, 1)
        else reminders.push(minutes)
        draftReminders = reminders
    }

    function reminderMultiplier(unit) {
        if (unit === "Semanas") return 10080
        if (unit === "Dias") return 1440
        if (unit === "Horas") return 60
        return 1
    }

    function setReminderDraft(minutes) {
        if (minutes % 10080 === 0) {
            draftReminderAmount = "" + (minutes / 10080)
            draftReminderUnit = "Semanas"
        } else if (minutes % 1440 === 0) {
            draftReminderAmount = "" + (minutes / 1440)
            draftReminderUnit = "Dias"
        } else if (minutes % 60 === 0) {
            draftReminderAmount = "" + (minutes / 60)
            draftReminderUnit = "Horas"
        } else {
            draftReminderAmount = "" + minutes
            draftReminderUnit = "Minutos"
        }
    }

    function addDraftReminder() {
        var amount = parseInt(draftReminderAmount)
        if (!/^\d+$/.test(draftReminderAmount) || amount < 1) {
            eventError = "O lembrete deve ser um número inteiro positivo."
            return
        }
        var minutes = amount * reminderMultiplier(draftReminderUnit)
        if (draftReminders.indexOf(minutes) < 0) {
            var reminders = draftReminders.concat([minutes])
            reminders.sort(function(a, b) { return a - b })
            draftReminders = reminders
        }
        eventError = ""
    }

    function removeDraftReminder(minutes) {
        draftReminders = draftReminders.filter(function(value) { return value !== minutes })
    }

    function reminderLabel(minutes) {
        if (minutes % 10080 === 0) return (minutes / 10080) + " semana" + (minutes / 10080 === 1 ? "" : "s")
        if (minutes % 1440 === 0) return (minutes / 1440) + " dia" + (minutes / 1440 === 1 ? "" : "s")
        if (minutes % 60 === 0) return (minutes / 60) + " hora" + (minutes / 60 === 1 ? "" : "s")
        return minutes + " minuto" + (minutes === 1 ? "" : "s")
    }

    function persistEvents() {
        if (calendarSaveProcess.running) return
        var payload = { events: calendarEvents, categories: calendarCategories }
        calendarSaveProcess.command = ["/usr/bin/python3", "/home/apx/.config/quickshell/apx/calendar_store.py", "save", JSON.stringify(payload)]
        calendarSaveProcess.running = true
    }

    function saveDraftEvent() {
        if (!draftTitle.trim()) { eventError = "Indica um título."; return }
        if (!draftCategory.trim()) { eventError = "Escolhe ou cria uma categoria."; return }
        if (!/^\d{4}-\d{2}-\d{2}$/.test(draftDate)) { eventError = "Data inválida: usa AAAA-MM-DD."; return }
        if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(draftTime)) { eventError = "Hora inválida: usa HH:MM."; return }
        var parts = draftDate.split("-")
        var testDate = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]))
        if (dateKey(testDate) !== draftDate) { eventError = "Essa data não existe."; return }
        var event = {
            id: editingEventId || Date.now().toString(),
            title: draftTitle.trim(),
            date: draftDate,
            time: draftTime,
            category: draftCategory.trim(),
            notes: draftNotes.trim(),
            scope: draftShared ? "shared" : "environment",
            active: draftActive,
            reminders: draftReminders.slice()
        }
        if (editingEventId) {
            calendarEvents = calendarEvents.map(function(existing) {
                return existing.id === editingEventId ? event : existing
            })
        } else {
            calendarEvents = calendarEvents.concat([event])
        }
        if (calendarCategories.indexOf(event.category) < 0)
            calendarCategories = calendarCategories.concat([event.category]).sort()
        calendarDate = testDate
        editingEventId = ""
        calendarEditor = false
        persistEvents()
    }

    function toggleEvent(id) {
        var updated = calendarEvents.map(function(event) {
            if (event.id !== id) return event
            var copy = Object.assign({}, event)
            copy.active = !event.active
            return copy
        })
        calendarEvents = updated
        persistEvents()
    }

    function deleteEvent(id) {
        calendarEvents = calendarEvents.filter(function(event) { return event.id !== id })
        persistEvents()
    }

    function sameDay(a, b) {
        return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()
    }

    function monthDays() {
        var year = calendarDate.getFullYear()
        var month = calendarDate.getMonth()
        var first = new Date(year, month, 1)
        var mondayOffset = (first.getDay() + 6) % 7
        var days = new Date(year, month + 1, 0).getDate()
        var cells = []
        for (var i = 0; i < mondayOffset; ++i) cells.push(null)
        for (var day = 1; day <= days; ++day) cells.push(new Date(year, month, day))
        while (cells.length % 7 !== 0) cells.push(null)
        return cells
    }

    function weekDays() {
        var base = new Date(calendarDate.getFullYear(), calendarDate.getMonth(), calendarDate.getDate())
        var offset = (base.getDay() + 6) % 7
        var monday = new Date(base.getFullYear(), base.getMonth(), base.getDate() - offset)
        var days = []
        for (var i = 0; i < 7; ++i) days.push(new Date(monday.getFullYear(), monday.getMonth(), monday.getDate() + i))
        return days
    }

    function moveCalendar(direction) {
        var d = calendarDate
        if (calendarView === "day")
            calendarDate = new Date(d.getFullYear(), d.getMonth(), d.getDate() + direction)
        else if (calendarView === "year")
            calendarDate = new Date(d.getFullYear() + direction, d.getMonth(), 1)
        else
            calendarDate = new Date(d.getFullYear(), d.getMonth() + direction, 1)
    }

    function calendarTitle() {
        if (calendarView === "year") return "" + calendarDate.getFullYear()
        if (calendarView === "day")
            return two(calendarDate.getDate()) + " " + monthNames[calendarDate.getMonth()] + " " + calendarDate.getFullYear()
        return monthNames[calendarDate.getMonth()] + " " + calendarDate.getFullYear()
    }

    function closePopup() {
        popup.visible = false
        popupOpening = false
        popupOpenTimer.stop()
        popupKind = ""
        controlsWifiOpen = false
        controlsBluetoothOpen = false
        controlsAudioOpen = false
        controlsMicrophoneOpen = false
        cancelWifiPassword()
        environmentCreateOpen = false
        environmentDeleteConfirm = false
        environmentKeyboardFocus = false
    }

    function showPopup() {
        popupOpening = true
        popup.visible = true
        popupOpenTimer.restart()
    }

    function togglePopup(kind, target) {
        if (popupKind === kind && popup.visible) {
            popup.visible = false
            popupKind = ""
            if (kind === "environments") environmentKeyboardFocus = false
            return
        }
        popup.visible = false
        if (kind === "controls") {
            controlsWifiOpen = false
            controlsBluetoothOpen = false
            controlsAudioOpen = false
            controlsMicrophoneOpen = false
            cancelWifiPassword()
        }
        popupKind = kind
        popupTarget = target
        showPopup()
        if (kind === "controls")
            hostAction("wifi-scan")
        if (kind === "model" && !modelStoreStatusProcess.running)
            modelStoreStatusProcess.running = true
        if (kind === "environments" && root.isHub) {
            root.environmentCreateOpen = false
            root.environmentDeleteConfirm = false
            root.selectedEnvironmentName = ""
            root.selectedEnvironmentGeneration = ""
            root.environmentFocusIndex = -1
            if (!environmentCatalogProcess.running) environmentCatalogProcess.running = true
            if (!environmentManagementStatusProcess.running) environmentManagementStatusProcess.running = true
            focusEnvironmentMenuAfterOpen()
        }
    }

    function focusEnvironmentMenuAfterOpen() {
        Qt.callLater(function() {
            if (root.popupKind !== "environments" || !popup.visible) return
            root.environmentKeyboardFocus = true
            root.environmentFocusIndex = -1
            environmentMenu.forceActiveFocus()
        })
    }

    function environmentSelection() {
        for (var i = 0; i < environmentCatalog.length; ++i)
            if (environmentCatalog[i].name === selectedEnvironmentName) return environmentCatalog[i]
        return null
    }

    function environmentCategoryLabel(category) {
        var labels = {
            "development": "Desenvolvimento",
            "games": "Jogos e lazer",
            "private": "Privado",
            "study": "Estudo",
            "university": "Universidade",
            "work": "Trabalho",
            "general": "Uso geral"
        }
        return labels[String(category || "general")] || "Environment APX"
    }

    function environmentMeta(item) {
        if (!item || item.state === "empty") return "Cria o primeiro espaço para começar"
        return String(item.description || "Sem descrição")
    }

    function selectEnvironment(item) {
        if (!item || item.state !== "stopped" || environmentManagementBusy) return
        selectedEnvironmentName = item.name
        selectedEnvironmentGeneration = item.generation
        environmentDeleteConfirm = false
    }

    function resetEnvironmentFocus() {
        var selectedIndex = -1
        for (var i = 0; i < environmentCatalog.length; ++i)
            if (environmentCatalog[i].name === selectedEnvironmentName) selectedIndex = i
        if (selectedIndex >= 0) environmentFocusIndex = selectedIndex
        else if (environmentFocusIndex > environmentCatalog.length + 1) environmentFocusIndex = -1
    }

    function moveEnvironmentFocus(direction) {
        if (environmentManagementBusy) return
        var rows = environmentCatalog.length
        var indices = []
        for (var index = 0; index < rows; ++index)
            if (environmentCatalog[index].state === "stopped") indices.push(index)
        indices.push(rows)
        if (selectedEnvironmentName.length) indices.push(rows + 1)
        var position = indices.indexOf(environmentFocusIndex)
        if (position < 0) environmentFocusIndex = direction > 0 ? indices[0] : indices[indices.length - 1]
        else environmentFocusIndex = indices[(position + direction + indices.length) % indices.length]
        environmentDeleteConfirm = false
    }

    function moveEnvironmentActionFocus(direction) {
        var rows = environmentCatalog.length
        if (environmentFocusIndex === rows && direction > 0) environmentFocusIndex = rows + 1
        else if (environmentFocusIndex === rows + 1 && direction < 0) environmentFocusIndex = rows
        environmentDeleteConfirm = false
    }

    function activateEnvironmentFocus() {
        if (environmentManagementBusy) return
        if (environmentFocusIndex < environmentCatalog.length) {
            var item = environmentCatalog[environmentFocusIndex]
            if (!item || item.state !== "stopped") return
            if (selectedEnvironmentName === item.name) openSelectedEnvironment()
            else selectEnvironment(item)
            return
        }
        if (environmentFocusIndex === environmentCatalog.length) beginEnvironmentCreate()
        else requestEnvironmentDelete()
    }

    function deleteFocusedEnvironment() {
        if (environmentFocusIndex < environmentCatalog.length) {
            var item = environmentCatalog[environmentFocusIndex]
            if (!item || item.state !== "stopped") return
            if (selectedEnvironmentName !== item.name) selectEnvironment(item)
        }
        requestEnvironmentDelete()
    }

    function beginEnvironmentCreate() {
        environmentCreateOpen = true
        environmentDeleteConfirm = false
        environmentSwitchError = ""
        environmentDraftName = ""
        environmentDraftDescription = ""
        applyEnvironmentPreset("intermediate")
        environmentFeatureDrawer = ""
        environmentFeatureInfo = ""
        environmentCreateFocusIndex = -1
        environmentKeyboardFocus = true
        Qt.callLater(function() { environmentMenu.forceActiveFocus() })
    }

    function requestEnvironmentDelete() {
        if (!selectedEnvironmentName.length || environmentManagementBusy) return
        if (environmentDeleteConfirm) destroySelectedEnvironment()
        else {
            environmentDeleteFocusIndex = 0
            environmentDeleteConfirm = true
        }
    }

    function cancelEnvironmentDelete() {
        environmentDeleteConfirm = false
        environmentDeleteFocusIndex = 0
    }

    function cancelEnvironmentCreate() {
        environmentCreateOpen = false
        environmentDraftName = ""
        environmentDraftDescription = ""
        environmentSwitchError = ""
        environmentKeyboardFocus = true
        environmentFocusIndex = -1
        environmentCreateFocusIndex = -1
        environmentFeatureDrawer = ""
        environmentFeatureInfo = ""
        Qt.callLater(function() { environmentMenu.forceActiveFocus() })
    }

    function environmentModuleIndex(key) {
        for (var index = 0; index < environmentModuleCatalog.length; ++index)
            if (environmentModuleCatalog[index].key === key) return index
        return -1
    }

    function environmentCreateVisibleFocusIndices() {
        var indices = [0, 1, 2, 3, 4, 5]
        environmentModuleGroups.forEach(function(group, groupIndex) {
            indices.push(6 + groupIndex)
            if (environmentFeatureDrawer === group.key) group.modules.forEach(function(key) {
                var moduleIndex = environmentModuleIndex(key)
                if (moduleIndex >= 0) indices.push(environmentCreateModuleFocusBase + moduleIndex)
            })
        })
        indices.push(environmentCreateSubmitFocusIndex)
        return indices
    }

    function moveEnvironmentCreateFocus(direction) {
        var indices = environmentCreateVisibleFocusIndices()
        var position = indices.indexOf(environmentCreateFocusIndex)
        if (position < 0) environmentCreateFocusIndex = direction > 0 ? indices[0] : indices[indices.length - 1]
        else environmentCreateFocusIndex = indices[(position + direction + indices.length) % indices.length]
        environmentMenu.forceActiveFocus()
    }

    function moveEnvironmentCreateHorizontal(direction) {
        var focusIndex = environmentCreateFocusIndex
        if (focusIndex < 0) {
            environmentCreateFocusIndex = direction > 0 ? 3 : 5
        } else if (focusIndex >= 3 && focusIndex <= 5) {
            environmentCreateFocusIndex = 3 + ((focusIndex - 3 + direction + 3) % 3)
        } else if (focusIndex >= environmentCreateModuleFocusBase && focusIndex < environmentCreateSubmitFocusIndex) {
            var moduleIndex = focusIndex - environmentCreateModuleFocusBase
            for (var groupIndex = 0; groupIndex < environmentModuleGroups.length; ++groupIndex) {
                var modules = environmentModuleGroups[groupIndex].modules
                var position = modules.indexOf(environmentModuleCatalog[moduleIndex].key)
                if (position < 0) continue
                var neighbour = position + direction
                if (neighbour >= 0 && neighbour < modules.length
                        && Math.floor(neighbour / 2) === Math.floor(position / 2))
                    environmentCreateFocusIndex = environmentCreateModuleFocusBase + environmentModuleIndex(modules[neighbour])
                break
            }
        }
        environmentMenu.forceActiveFocus()
    }

    function moveEnvironmentCreateVertical(direction) {
        var focusIndex = environmentCreateFocusIndex
        if (focusIndex < 0) { moveEnvironmentCreateFocus(direction); return }
        if (focusIndex === 0) environmentCreateFocusIndex = direction > 0 ? 1 : environmentCreateSubmitFocusIndex
        else if (focusIndex === 1) environmentCreateFocusIndex = direction > 0 ? 2 : 0
        else if (focusIndex === 2) environmentCreateFocusIndex = direction > 0 ? 4 : 1
        else if (focusIndex >= 3 && focusIndex <= 5)
            environmentCreateFocusIndex = direction > 0 ? 6 : 2
        else if (focusIndex >= 6 && focusIndex <= 9) {
            var groupIndex = focusIndex - 6
            var group = environmentModuleGroups[groupIndex]
            if (direction > 0 && environmentFeatureDrawer === group.key && group.modules.length)
                environmentCreateFocusIndex = environmentCreateModuleFocusBase + environmentModuleIndex(group.modules[0])
            else if (direction > 0) environmentCreateFocusIndex = groupIndex < environmentModuleGroups.length - 1 ? focusIndex + 1 : environmentCreateSubmitFocusIndex
            else environmentCreateFocusIndex = groupIndex > 0 ? focusIndex - 1 : 4
        } else if (focusIndex >= environmentCreateModuleFocusBase && focusIndex < environmentCreateSubmitFocusIndex) {
            var module = environmentModuleCatalog[focusIndex - environmentCreateModuleFocusBase]
            for (var index = 0; index < environmentModuleGroups.length; ++index) {
                var groupModules = environmentModuleGroups[index].modules
                var position = groupModules.indexOf(module.key)
                if (position < 0) continue
                var verticalNeighbour = position + direction * 2
                if (verticalNeighbour >= 0 && verticalNeighbour < groupModules.length)
                    environmentCreateFocusIndex = environmentCreateModuleFocusBase + environmentModuleIndex(groupModules[verticalNeighbour])
                else if (direction < 0) environmentCreateFocusIndex = 6 + index
                else environmentCreateFocusIndex = index < environmentModuleGroups.length - 1 ? 7 + index : environmentCreateSubmitFocusIndex
                break
            }
        } else if (focusIndex === environmentCreateSubmitFocusIndex) environmentCreateFocusIndex = direction > 0 ? 0 : environmentModuleGroups.length + 5
        environmentMenu.forceActiveFocus()
    }

    function activateEnvironmentCreateFocus() {
        var focusIndex = environmentCreateFocusIndex
        if (focusIndex < 0) return
        if (focusIndex === 0) { cancelEnvironmentCreate(); return }
        if (focusIndex === 1) { environmentNameInput.forceActiveFocus(); return }
        if (focusIndex === 2) { environmentDescriptionInput.forceActiveFocus(); return }
        if (focusIndex >= 3 && focusIndex <= 5) {
            applyEnvironmentPreset(["basic", "intermediate", "complete"][focusIndex - 3])
            return
        }
        if (focusIndex >= 6 && focusIndex <= 9) {
            var group = environmentModuleGroups[focusIndex - 6]
            environmentFeatureDrawer = environmentFeatureDrawer === group.key ? "" : group.key
            environmentFeatureInfo = ""
            return
        }
        if (focusIndex >= environmentCreateModuleFocusBase && focusIndex < environmentCreateSubmitFocusIndex) {
            var moduleInfo = environmentModuleCatalog[focusIndex - environmentCreateModuleFocusBase]
            setEnvironmentModule(moduleInfo.key, environmentSelectedModules[moduleInfo.key] !== true)
            return
        }
        if (focusIndex === environmentCreateSubmitFocusIndex) createEnvironment(environmentNameInput.text, environmentDescriptionInput.text)
    }

    function handleEnvironmentCreateKey(event) {
        if (event.key === Qt.Key_Escape) cancelEnvironmentCreate()
        else if (event.key === Qt.Key_Up) moveEnvironmentCreateVertical(-1)
        else if (event.key === Qt.Key_Down) moveEnvironmentCreateVertical(1)
        else if (event.key === Qt.Key_Left) moveEnvironmentCreateHorizontal(-1)
        else if (event.key === Qt.Key_Right) moveEnvironmentCreateHorizontal(1)
        else if (event.key === Qt.Key_Backtab) moveEnvironmentCreateFocus(-1)
        else if (event.key === Qt.Key_Tab) moveEnvironmentCreateFocus(1)
        else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) activateEnvironmentCreateFocus()
        else return
        event.accepted = true
    }

    function environmentPresetKeys(preset) {
        if (preset === "basic") return ["system", "cli-aur"]
        if (preset === "complete") return environmentModuleCatalog.map(function(item) { return item.key })
        return environmentModuleCatalog.slice(0, 14).map(function(item) { return item.key }).concat(["shortcuts"])
    }

    function applyEnvironmentPreset(preset) {
        var next = {}
        environmentPresetKeys(preset).forEach(function(key) { next[key] = true })
        environmentDesktopPreset = preset
        environmentSelectedModules = next
    }

    function setEnvironmentModule(key, enabled) {
        var next = Object.assign({}, environmentSelectedModules)
        next[key] = enabled
        if (enabled) {
            var changed = true
            while (changed) {
                changed = false
                environmentModuleCatalog.forEach(function(item) {
                    if (next[item.key]) item.deps.forEach(function(dep) {
                        if (!next[dep]) { next[dep] = true; changed = true }
                    })
                })
            }
        } else {
            var removed = true
            while (removed) {
                removed = false
                environmentModuleCatalog.forEach(function(item) {
                    if (!next[item.key]) return
                    for (var index = 0; index < item.deps.length; ++index)
                        if (!next[item.deps[index]]) {
                            next[item.key] = false; removed = true; break
                        }
                })
            }
        }
        environmentSelectedModules = next
        environmentDesktopPreset = "custom"
    }

    function selectedEnvironmentModuleKeys() {
        return environmentModuleCatalog.filter(function(item) {
            return environmentSelectedModules[item.key] === true
        }).map(function(item) { return item.key })
    }

    function environmentEstimatedMib() {
        return environmentModuleCatalog.reduce(function(total, item) {
            return total + (environmentSelectedModules[item.key] ? item.mib : 0)
        }, 0)
    }

    function environmentModuleInfo(key) {
        for (var index = 0; index < environmentModuleCatalog.length; ++index)
            if (environmentModuleCatalog[index].key === key) return environmentModuleCatalog[index]
        return { key: key, label: key, mib: 0, deps: [] }
    }

    function openSelectedEnvironment() {
        if (!selectedEnvironmentName.length || environmentSwitchPending || environmentManagementBusy) return
        environmentSwitchError = ""
        environmentSwitchProgress = 8
        environmentSwitchPending = true
        environmentSwitchProcess.command = [root.environmentClient, "open", "--target", selectedEnvironmentName]
        environmentSwitchProcess.running = true
    }

    function returnToHub() {
        if (!sessionKindReady || environmentSwitchPending || environmentSwitchProcess.running) return
        environmentSwitchError = ""
        environmentSwitchProgress = 8
        environmentSwitchPending = true
        // Prefer the authenticated Host return. If startup has not published
        // identity yet, exiting this workload compositor is the bounded local
        // fallback; the existing Host supervisor then restores Hub.
        environmentSwitchProcess.command = identityReady
                ? [root.environmentClient, "return"]
                : ["/usr/bin/hyprctl", "eval", "hl.dsp.exit()"]
        environmentSwitchProcess.running = true
    }

    function createEnvironment(rawName, rawDescription) {
        var visibleName = rawName === undefined ? environmentDraftName : String(rawName)
        var visibleDescription = rawDescription === undefined
            ? environmentDraftDescription : String(rawDescription)
        var name = visibleName.trim().toLowerCase()
        try { name = name.normalize("NFD").replace(/[\u0300-\u036f]/g, "") }
        catch (error) {}
        name = name.replace(/[^a-z0-9]+/g, "-")
            .replace(/-+/g, "-").replace(/^-|-$/g, "")
        if (/^[0-9]/.test(name)) name = "env-" + name
        if (name.length > 27) name = name.slice(0, 27).replace(/-$/g, "")
        if (name === "hub") name = "hub-env"
        environmentDraftName = name
        if (!name.length) {
            environmentSwitchError = "Escreve um nome para o Environment."
            return
        }
        environmentSwitchError = ""
        environmentManagementBusy = true
        // The creation form must leave the scene as soon as the request is
        // accepted. Keeping it rendered behind the catalogue/progress view
        // causes both states to flash while the popup changes height.
        environmentCreateOpen = false
        environmentFeatureDrawer = ""
        environmentFeatureInfo = ""
        environmentCreateFocusIndex = -1
        environmentActionProcess.command = [root.environmentClient, "create", "--target", name,
                                            "--description", visibleDescription.trim(),
                                            "--preset", environmentDesktopPreset === "custom" ? "intermediate" : environmentDesktopPreset,
                                            "--modules", selectedEnvironmentModuleKeys().join(",")]
        environmentActionProcess.running = true
    }

    function destroySelectedEnvironment() {
        if (!selectedEnvironmentName.length || !selectedEnvironmentGeneration.length || environmentManagementBusy) return
        environmentSwitchError = ""
        environmentManagementBusy = true
        environmentActionProcess.command = [root.environmentClient, "destroy",
                                            "--target", selectedEnvironmentName,
                                            "--generation", selectedEnvironmentGeneration]
        environmentActionProcess.running = true
    }

    function modelStoreAction(mode, target) {
        if (modelStoreActionProcess.running || modelStoreBusy) return
        modelStoreBusy = true
        modelStoreError = ""
        modelStoreConfirmDetach = false
        if (mode === "model-select") {
            modelSwitchActive = true
            modelSwitchProfile = target
            modelSwitchLabel = target === "fast" ? "Qwen2.5-Coder 3B Fast" : (target === "balanced" ? "Qwen2.5-Coder 7B" : "Qwen3-Coder 30B")
            modelSwitchProgress = 2
        }
        modelStoreActionProcess.command = ["/home/apx/.local/libexec/apx-model-store-client-v1.py", mode]
        if (target !== undefined && target !== "")
            modelStoreActionProcess.command.push(target)
        modelStoreActionProcess.running = true
    }

    function hostAction(operation, target) {
        if (hostActionProcess.running)
            return
        var args = ["/run/apx/host-services-ui-v3.py", operation]
        if (target !== undefined && target !== "")
            args.push(target)
        hostActionProcess.command = args
        hostActionProcess.running = true
    }

    function localAction(args) {
        if (!localActionProcess.running) {
            localActionProcess.command = args
            localActionProcess.running = true
        }
    }

    function commitVolume(value) {
        var nextVolume = Math.round(value)
        // Keep the UI at the released position while wpctl confirms it.
        volumeValue = nextVolume
        if (!volumeMuted)
            volumeText = nextVolume + "%"
        localAction(["/usr/bin/wpctl", "set-volume", "-l", "1", "@DEFAULT_AUDIO_SINK@", nextVolume + "%"])
    }

    function commitMicrophoneVolume(value) {
        var nextVolume = Math.round(value)
        microphoneVolume = nextVolume
        if (!microphoneMuted)
            microphoneText = nextVolume + "%"
        localAction(["/usr/bin/wpctl", "set-volume", "-l", "1", "@DEFAULT_AUDIO_SOURCE@", nextVolume + "%"])
    }

    function toggleVolumeMute() {
        if (localActionProcess.running) return
        volumeMuted = !volumeMuted
        volumeText = volumeMuted ? "MUTE" : volumeValue + "%"
        localAction(["/usr/bin/wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"])
    }

    function toggleMicrophoneMute() {
        if (localActionProcess.running) return
        microphoneMuted = !microphoneMuted
        microphoneText = microphoneMuted ? "MUTE" : microphoneVolume + "%"
        localAction(["/usr/bin/wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "toggle"])
    }

    function applyHardwareControls(state) {
        if (state.display_brightness !== undefined && displayBrightnessPending < 0
                && !displayBrightnessProcess.running && !displayBrightnessSlider.pressed)
            displayBrightness = Number(state.display_brightness)
        if (state.keyboard_brightness !== undefined)
            keyboardBrightness = Number(state.keyboard_brightness)
        if (state.keyboard_brightness_max !== undefined)
            keyboardBrightnessMax = Number(state.keyboard_brightness_max)
    }

    function previewDisplayBrightness(value) {
        displayBrightness = Math.max(5, Math.min(100, Math.round(value)))
        displayBrightnessPending = displayBrightness
        if (!displayBrightnessProcess.running && !displayBrightnessDebounce.running)
            displayBrightnessDebounce.start()
    }

    function dispatchDisplayBrightness() {
        if (displayBrightnessProcess.running || displayBrightnessPending < 5) return
        if (displayBrightnessPending === displayBrightnessLastSent) {
            displayBrightnessPending = -1
            return
        }
        hardwareControlError = ""
        displayBrightnessInFlight = displayBrightnessPending
        displayBrightnessLastSent = displayBrightnessPending
        displayBrightnessPending = -1
        displayBrightnessProcess.command = ["/home/apx/.local/libexec/apx-system-power-client-v1.py",
                                            "display-set", String(displayBrightnessInFlight)]
        displayBrightnessProcess.running = true
    }

    function commitDisplayBrightness(value) {
        previewDisplayBrightness(value)
        displayBrightnessDebounce.stop()
        dispatchDisplayBrightness()
    }

    function stepDisplayBrightness(delta) {
        commitDisplayBrightness(displayBrightness + delta)
    }

    function cycleKeyboardBrightness() {
        if (keyboardBrightnessProcess.running) return
        hardwareControlError = ""
        keyboardBrightnessProcess.running = true
    }

    function stepVolume(delta) {
        commitVolume(Math.max(0, Math.min(100, volumeValue + delta)))
    }

    function beginPower(action) {
        if (powerBusy) return
        powerBusy = true
        powerAction = action
        powerToken = ""
        powerMessage = "A verificar o Host..."
        powerConfirmOpen = true
        powerPrepareProcess.command = ["/home/apx/.local/libexec/apx-system-power-client-v1.py", "prepare", action]
        powerPrepareProcess.running = true
    }

    function loadHardwareProfile() {
        if (!hardwareProfileProcess.running)
            hardwareProfileProcess.running = true
    }

    function platformLabel(profile) {
        if (profile === "low-power") return "SILENCIOSO"
        if (profile === "balanced") return "NORMAL"
        if (profile === "performance") return "PERFORMANCE"
        return "INDISPONÍVEL"
    }

    function gpuLabel(profile) {
        if (profile === "hybrid") return "HÍBRIDO"
        if (profile === "nvidia") return "NVIDIA"
        return "INDISPONÍVEL"
    }

    function setPlatformProfile(profile) {
        if (hardwareBusy) return
        hardwareBusy = true
        platformProfileError = ""
        hardwareMessage = "A aplicar modo " + platformLabel(profile) + "..."
        platformProfileProcess.command = ["/home/apx/.local/libexec/apx-system-power-client-v1.py", "platform-set", profile]
        platformProfileProcess.running = true
    }

    function beginGpuProfile(profile) {
        if (hardwareBusy) return
        hardwareBusy = true
        gpuProfileError = ""
        hardwareApplied = false
        hardwareToken = ""
        hardwareTarget = profile
        hardwareMessage = "A verificar o modo de GPU..."
        hardwareConfirmOpen = true
        gpuPrepareProcess.command = ["/home/apx/.local/libexec/apx-system-power-client-v1.py", "gpu-prepare", profile]
        gpuPrepareProcess.running = true
    }

    function cancelGpuProfile() {
        if (hardwareBusy) return
        if (!hardwareToken.length || hardwareApplied) {
            hardwareConfirmOpen = false
            hardwareApplied = false
            hardwareMessage = ""
            return
        }
        hardwareBusy = true
        gpuCancelProcess.running = true
    }

    function confirmGpuProfile() {
        if (hardwareBusy || !hardwareToken.length) return
        hardwareBusy = true
        hardwareMessage = "A preparar o firmware Lenovo..."
        gpuConfirmProcess.running = true
    }

    function rebootForGpuProfile() {
        hardwareConfirmOpen = false
        hardwareApplied = false
        popupKind = "controls"
        beginPower("reboot")
    }

    function cancelPower() {
        if (powerBusy) return
        if (!powerToken.length) {
            powerConfirmOpen = false
            powerMessage = ""
            return
        }
        powerBusy = true
        powerCancelProcess.running = true
    }

    function confirmPower() {
        if (powerBusy || !powerToken.length) return
        powerBusy = true
        if (powerAction === "suspend") {
            powerMessage = "A bloquear o ecrã e suspender..."
            if (!lockProcess.running) lockProcess.running = true
            suspendLockDelay.restart()
        } else {
            powerMessage = "A fechar o Environment de forma segura..."
            powerConfirmProcess.running = true
        }
    }

    function updateClock() {
        var now = new Date()
        var wasFollowingToday = sameDay(calendarDate, currentDate)
        var dayChanged = !sameDay(currentDate, now)
        currentDate = now
        // Advance the selected day at midnight only while the user was
        // already following today; preserve dates chosen for browsing.
        if (dayChanged && wasFollowingToday)
            calendarDate = new Date(now.getFullYear(), now.getMonth(), now.getDate())
        function two(value) { return value < 10 ? "0" + value : "" + value }
        clockText = two(now.getDate()) + "/" + two(now.getMonth() + 1) + "/" + now.getFullYear()
                    + " | " + two(now.getHours()) + ":" + two(now.getMinutes())
    }

    Process {
        id: hostStatusProcess
        command: ["/run/apx/host-services-ui-v3.py", "status"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.hostState = JSON.parse(text)
                    if (root.hostState.network_name) {
                        root.wifiLastNetwork = root.hostState.network_name
                        root.wifiManualOff = false
                    }
                    if (root.wifiTogglePhase === "disconnecting" && !root.hostState.network_name
                            || root.wifiTogglePhase === "connecting" && root.hostState.network_name) {
                        root.wifiTogglePhase = ""
                        root.wifiOptimisticOverride = false
                    }
                    if (root.bluetoothPowerPhase.length
                            && root.hostState.bluetooth_powered === root.bluetoothPowerActive) {
                        root.bluetoothPowerPhase = ""
                        root.bluetoothPowerOverride = false
                    }
                    if (root.bluetoothDevicePendingAddress.length && !bluetoothDeviceActionProcess.running) {
                        root.bluetoothDevicePendingAddress = ""
                        root.bluetoothDevicePendingAction = ""
                    }
                }
                catch (error) { root.hostState = ({ network_name: "host?", bluetooth_powered: false }) }
            }
        }
    }

    Process {
        id: hostActionProcess
        onExited: hostStatusProcess.running = true
    }

    Process {
        id: wifiToggleProcess
        stderr: StdioCollector { onStreamFinished: if (text.trim().length) root.wifiMessage = text.trim() }
        onExited: (exitCode, exitStatus) => {
            if (exitCode !== 0) {
                root.wifiTogglePhase = ""
                root.wifiOptimisticOverride = false
                if (!root.wifiMessage.length) root.wifiMessage = "Não foi possível alterar a ligação Wi-Fi."
            }
            hostStatusProcess.running = true
        }
    }

    Process {
        id: bluetoothPowerProcess
        stderr: StdioCollector { onStreamFinished: if (text.trim().length) root.bluetoothMessage = text.trim() }
        onExited: (exitCode, exitStatus) => {
            if (exitCode !== 0) {
                root.bluetoothPowerPhase = ""
                root.bluetoothPowerOverride = false
                if (!root.bluetoothMessage.length) root.bluetoothMessage = "Não foi possível alterar o Bluetooth."
            }
            hostStatusProcess.running = true
        }
    }

    Process {
        id: bluetoothDeviceActionProcess
        stderr: StdioCollector { onStreamFinished: if (text.trim().length) root.bluetoothMessage = text.trim() }
        onExited: (exitCode, exitStatus) => {
            if (exitCode !== 0) {
                root.bluetoothDevicePendingAddress = ""
                root.bluetoothDevicePendingAction = ""
                if (!root.bluetoothMessage.length) root.bluetoothMessage = "Não foi possível alterar o dispositivo."
            }
            hostStatusProcess.running = true
        }
    }

    Process {
        id: bluetoothScanProcess
        command: ["/run/apx/host-services-client-v3.py", "bluetooth-scan"]
        stderr: StdioCollector { onStreamFinished: if (text.trim().length) root.bluetoothMessage = text.trim() }
        onStarted: root.bluetoothMessage = "A procurar dispositivos…"
        onExited: (exitCode, exitStatus) => {
            root.bluetoothMessage = exitCode === 0 ? "Pesquisa concluída." : (root.bluetoothMessage || "Não foi possível procurar dispositivos.")
            hostStatusProcess.running = true
        }
    }

    Process {
        id: bluetoothPairBeginProcess
        stdout: StdioCollector {
            onStreamFinished: {
                try { root.applyBluetoothPairResult(JSON.parse(text)) }
                catch (error) { root.bluetoothPairPhase = "failed"; root.bluetoothMessage = "Resposta de emparelhamento inválida." }
            }
        }
        stderr: StdioCollector { onStreamFinished: if (text.trim().length) root.bluetoothMessage = text.trim() }
        onExited: (exitCode, exitStatus) => {
            if (exitCode !== 0) root.bluetoothPairPhase = "failed"
        }
    }

    Process {
        id: bluetoothPairStatusProcess
        stdout: StdioCollector {
            onStreamFinished: {
                try { root.applyBluetoothPairResult(JSON.parse(text)) }
                catch (error) { root.bluetoothPairPhase = "failed"; root.bluetoothMessage = "Não foi possível atualizar o emparelhamento." }
            }
        }
        stderr: StdioCollector { onStreamFinished: if (text.trim().length) root.bluetoothMessage = text.trim() }
        onExited: (exitCode, exitStatus) => { if (exitCode !== 0) root.bluetoothPairPhase = "failed" }
    }

    Process {
        id: bluetoothPairRespondProcess
        stdinEnabled: true
        onStarted: {
            if (root.bluetoothPairResponsePin.length) write(root.bluetoothPairResponsePin + "\n")
            root.bluetoothPairResponsePin = ""
            root.bluetoothPairPin = ""
        }
        stdout: StdioCollector {
            onStreamFinished: {
                try { root.applyBluetoothPairResult(JSON.parse(text)) }
                catch (error) { root.bluetoothPairPhase = "failed"; root.bluetoothMessage = "Não foi possível confirmar o emparelhamento." }
            }
        }
        stderr: StdioCollector { onStreamFinished: if (text.trim().length) root.bluetoothMessage = text.trim() }
        onExited: (exitCode, exitStatus) => { if (exitCode !== 0) root.bluetoothPairPhase = "failed" }
    }

    Process {
        id: bluetoothRemoveProcess
        stderr: StdioCollector { onStreamFinished: if (text.trim().length) root.bluetoothMessage = text.trim() }
        onExited: (exitCode, exitStatus) => {
            root.bluetoothMessage = exitCode === 0 ? root.bluetoothRemoveName + " foi esquecido." : (root.bluetoothMessage || "Não foi possível esquecer o dispositivo.")
            root.bluetoothRemoveAddress = ""
            root.bluetoothRemoveName = ""
            hostStatusProcess.running = true
        }
    }

    Process {
        id: wifiCredentialProcess
        stdinEnabled: true
        stderr: StdioCollector {
            onStreamFinished: if (text.trim().length) root.wifiMessage = text.trim()
        }
        onStarted: {
            write(root.wifiPassword + "\n")
            root.wifiPassword = ""
        }
        onExited: (exitCode, exitStatus) => {
            if (exitCode === 0) {
                root.wifiMessage = "Ligação efetuada."
                root.wifiPasswordVisible = false
                root.wifiSelectedSsid = ""
            } else if (!root.wifiMessage.length) {
                root.wifiMessage = "Não foi possível estabelecer a ligação."
            }
            hostStatusProcess.running = true
        }
    }

    Process {
        id: localActionProcess
        onExited: {
            volumeProcess.running = true
            microphoneProcess.running = true
            batteryProcess.running = true
            audioStateProcess.running = true
        }
    }

    Process { id: lockProcess; command: ["/home/apx/.local/bin/apx-detached-launch", "/usr/bin/hyprlock"] }
    Timer {
        id: suspendLockDelay
        interval: 500
        repeat: false
        onTriggered: powerConfirmProcess.running = true
    }

    Process {
        id: volumeProcess
        command: ["/usr/bin/wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"]
        stdout: StdioCollector {
            onStreamFinished: {
                var match = text.match(/Volume:\s+([0-9.]+)/)
                if (match) root.volumeValue = Math.round(parseFloat(match[1]) * 100)
                root.volumeMuted = text.indexOf("MUTED") >= 0
                root.volumeText = match ? (root.volumeMuted ? "MUTE" : root.volumeValue + "%") : "--"
            }
        }
    }

    Process {
        id: microphoneProcess
        command: ["/usr/bin/wpctl", "get-volume", "@DEFAULT_AUDIO_SOURCE@"]
        stdout: StdioCollector {
            onStreamFinished: {
                var match = text.match(/Volume:\s+([0-9.]+)/)
                if (match) root.microphoneVolume = Math.round(parseFloat(match[1]) * 100)
                root.microphoneMuted = text.indexOf("MUTED") >= 0
                root.microphoneText = match ? (root.microphoneMuted ? "MUTE" : root.microphoneVolume + "%") : "--"
            }
        }
    }

    Process {
        id: batteryProcess
        command: ["/usr/bin/bash", "-lc", "for f in /sys/class/power_supply/BAT*/capacity; do test -r \"$f\" && { tr -d '\\n' < \"$f\"; printf '%%'; exit; }; done; printf -- '--'"]
        stdout: StdioCollector { onStreamFinished: root.batteryText = text.trim() }
    }

    Process {
        id: hardwareProfileProcess
        command: ["/home/apx/.local/libexec/apx-system-power-client-v1.py", "hardware-status"]
        stderr: StdioCollector { onStreamFinished: root.hardwareStatusError = text.trim() }
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.hardwareProfile = JSON.parse(text)
                    root.applyHardwareControls(root.hardwareProfile)
                    root.hardwareStatusError = ""
                } catch (error) {
                    root.hardwareMessage = root.hardwareStatusError.length
                            ? root.hardwareStatusError : "Perfis do Host indisponíveis."
                }
            }
        }
    }

    Process {
        id: platformProfileProcess
        stderr: StdioCollector { onStreamFinished: root.platformProfileError = text.trim() }
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.hardwareProfile = JSON.parse(text)
                    root.applyHardwareControls(root.hardwareProfile)
                    root.hardwareMessage = "Modo " + root.platformLabel(root.hardwareProfile.platform_profile) + " ativo."
                } catch (error) {
                    root.hardwareMessage = root.platformProfileError.length
                            ? root.platformProfileError : "O Host recusou o modo de energia."
                }
            }
        }
        onExited: root.hardwareBusy = false
    }

    Process {
        id: gpuPrepareProcess
        stderr: StdioCollector { onStreamFinished: root.gpuProfileError = text.trim() }
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    var result = JSON.parse(text)
                    root.hardwareToken = result.token || ""
                    root.hardwareMessage = "Mudar para " + root.gpuLabel(result.profile)
                            + " exige reinício. O Environment será fechado e o caminho físico do ecrã poderá mudar."
                } catch (error) {
                    root.hardwareToken = ""
                    root.hardwareMessage = root.gpuProfileError.length
                            ? root.gpuProfileError : "O Host recusou a alteração de GPU."
                }
            }
        }
        onExited: root.hardwareBusy = false
    }

    Process {
        id: gpuConfirmProcess
        command: ["/home/apx/.local/libexec/apx-system-power-client-v1.py", "gpu-confirm", "--token-stdin"]
        stdinEnabled: true
        onStarted: gpuConfirmProcess.write(root.hardwareToken + "\n")
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.hardwareProfile = JSON.parse(text)
                    root.applyHardwareControls(root.hardwareProfile)
                    root.hardwareToken = ""
                    root.hardwareApplied = true
                    root.hardwareMessage = "Perfil " + root.gpuLabel(root.hardwareTarget)
                            + " preparado. Reinicie agora ou mais tarde para o aplicar."
                } catch (error) {
                    root.hardwareMessage = "Não foi possível preparar o perfil de GPU."
                }
            }
        }
        onExited: root.hardwareBusy = false
    }

    Process {
        id: gpuCancelProcess
        command: ["/home/apx/.local/libexec/apx-system-power-client-v1.py", "gpu-cancel", "--token-stdin"]
        stdinEnabled: true
        onStarted: gpuCancelProcess.write(root.hardwareToken + "\n")
        onExited: {
            root.hardwareBusy = false
            root.hardwareToken = ""
            root.hardwareConfirmOpen = false
            root.hardwareMessage = ""
        }
    }

    Process {
        id: displayBrightnessProcess
        stderr: StdioCollector { onStreamFinished: root.hardwareControlError = text.trim() }
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.applyHardwareControls(JSON.parse(text))
                    root.hardwareControlError = ""
                } catch (error) {
                    if (!root.hardwareControlError.length)
                        root.hardwareControlError = "Não foi possível alterar o brilho do ecrã."
                }
            }
        }
        onExited: {
            root.displayBrightnessInFlight = -1
            if (root.displayBrightnessPending >= 5)
                displayBrightnessDebounce.restart()
        }
    }

    Process {
        id: keyboardBrightnessProcess
        command: ["/home/apx/.local/libexec/apx-system-power-client-v1.py", "keyboard-cycle"]
        stderr: StdioCollector { onStreamFinished: root.hardwareControlError = text.trim() }
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.applyHardwareControls(JSON.parse(text))
                    root.hardwareControlError = ""
                } catch (error) {
                    if (!root.hardwareControlError.length)
                        root.hardwareControlError = "Não foi possível alterar a luz do teclado."
                }
            }
        }
    }

    Process {
        id: legionBrightnessKeysProcess
        command: ["/usr/lib/apx/apx-legion-brightness-keys-v1.py"]
        running: true
    }

    Process {
        id: calendarLoadProcess
        command: ["/usr/bin/python3", "/home/apx/.config/quickshell/apx/calendar_store.py", "load"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    var payload = JSON.parse(text)
                    root.calendarEvents = payload.events || []
                    root.calendarCategories = payload.categories || []
                } catch (error) {
                    root.calendarEvents = []
                    root.calendarCategories = []
                }
            }
        }
    }

    Process { id: calendarSaveProcess }

    Process {
        id: environmentIdentityProcess
        command: ["/run/apx/environment-switch-client-v1.py", "identity"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.environmentIdentity = JSON.parse(text)
                    root.identityReady = true
                } catch (error) {
                    root.identityReady = false
                }
            }
        }
    }
    Process {
        id: sessionKindProcess
        command: ["/usr/bin/test", "-S", "/run/apx/host-console-v1.sock"]
        running: true
        onExited: function(exitCode) {
            root.sessionHubProof = exitCode === 0
            root.sessionKindReady = true
        }
    }
    Process {
        id: environmentSwitchProcess
        stderr: StdioCollector {
            onStreamFinished: root.environmentSwitchError = text.trim()
        }
        onExited: function(exitCode) {
            if (exitCode !== 0) {
                root.environmentSwitchPending = false
                if (!root.environmentSwitchError.length)
                    root.environmentSwitchError = "O Host recusou a transição. Tenta novamente."
            }
        }
    }
    Process {
        id: environmentCatalogProcess
        command: [root.environmentClient, "catalog"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    var items = JSON.parse(text)
                    root.environmentCatalog = items
                    var selected = root.environmentSelection()
                    if (!selected) {
                        root.selectedEnvironmentName = ""
                        root.selectedEnvironmentGeneration = ""
                    }
                    root.resetEnvironmentFocus()
                } catch (error) {
                    root.environmentSwitchError = "Não foi possível atualizar os Environments."
                }
            }
        }
        stderr: StdioCollector { onStreamFinished: if (text.trim().length) root.environmentSwitchError = text.trim() }
    }
    Process {
        id: environmentManagementStatusProcess
        command: [root.environmentClient, "management-status"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    var state = JSON.parse(text)
                    root.environmentManagementState = state
                    root.environmentProgressReadFailures = 0
                    root.environmentManagementBusy = state.busy === true
                    if (state.phase === "complete") {
                        root.environmentSwitchError = ""
                        if (state.action === "destroy" && root.selectedEnvironmentName === state.target) {
                            root.selectedEnvironmentName = ""
                            root.selectedEnvironmentGeneration = ""
                        }
                        root.environmentCreateOpen = false
                        root.environmentDeleteConfirm = false
                        root.environmentDraftName = ""
                        root.environmentDraftDescription = ""
                        if (!environmentCatalogProcess.running) environmentCatalogProcess.running = true
                    } else if (state.phase === "failed") {
                        root.environmentSwitchError = state.message || "A operação falhou."
                    }
                } catch (error) {
                    root.environmentProgressReadFailures += 1
                    if (root.environmentProgressReadFailures < 5) {
                        environmentManagementStatusRetryTimer.restart()
                    } else {
                        root.environmentSwitchError = "Não foi possível ler o progresso."
                        root.environmentManagementBusy = false
                    }
                }
            }
        }
    }
    Timer {
        id: environmentManagementStatusRetryTimer
        interval: 350
        repeat: false
        onTriggered: if (!environmentManagementStatusProcess.running) environmentManagementStatusProcess.running = true
    }
    Process {
        id: environmentActionProcess
        stderr: StdioCollector { onStreamFinished: if (text.trim().length) root.environmentSwitchError = text.trim() }
        onExited: function(exitCode) {
            if (exitCode !== 0) root.environmentManagementBusy = false
            if (!environmentManagementStatusProcess.running) environmentManagementStatusProcess.running = true
        }
    }
    Process { id: environmentFilesProcess; command: ["/usr/bin/thunar"] }
    Process { id: environmentAppsProcess; command: ["/usr/bin/rofi", "-show", "drun"] }
    Process { id: updateUiProcess; command: ["/home/apx/.local/bin/apx-detached-launch", "/usr/bin/kitty", "--title", "APX Atualizações", "/run/apx/coordinated-update-client-v1.py", "ui"] }
    Process {
        id: hostConsoleProcess
        command: ["/home/apx/.local/bin/apx-host-console-open"]
    }
    Process {
        id: hostExitProcess
        command: ["/usr/bin/hyprctl", "dispatch", "hl.dsp.exit()"]
    }
    Process {
        id: shortcutStateProcess
        command: ["/home/apx/.local/bin/apx-shortcuts-v1", "status"]
        stdout: StdioCollector { onStreamFinished: root.apxShortcutsEnabled = text.trim() !== "disabled" }
    }
    Process {
        id: shortcutApplyProcess
        stdout: StdioCollector { onStreamFinished: root.apxShortcutsEnabled = text.trim() !== "disabled" }
        onExited: if (!shortcutStateProcess.running) shortcutStateProcess.running = true
    }
    Process {
        id: modelStoreStatusProcess
        command: ["/home/apx/.local/libexec/apx-model-store-client-v1.py", "status"]
        stdout: StdioCollector { onStreamFinished: { try { var nextState = JSON.parse(text); root.modelStoreState = nextState; root.modelStoreError = ""; if (nextState.model_transition === true) { root.modelSwitchActive = true; root.modelSwitchProfile = nextState.transition_profile || ""; root.modelSwitchLabel = nextState.transition_model || "Novo modelo"; root.modelSwitchProgress = nextState.transition_progress || 1 } else if (!modelStoreActionProcess.running) { root.modelSwitchActive = false; root.modelSwitchProgress = 0 } } catch (error) { root.modelStoreError = "Não foi possível ler o estado do modelo." } } }
        stderr: StdioCollector { onStreamFinished: if (text.trim().length) root.modelStoreError = text.trim() }
    }
    Process {
        id: modelStoreActionProcess
        stdout: StdioCollector { onStreamFinished: { try { root.modelStoreState = JSON.parse(text); root.modelStoreError = "" } catch (error) { root.modelStoreError = "Resposta inválida do Host." } } }
        stderr: StdioCollector { onStreamFinished: if (text.trim().length) root.modelStoreError = text.trim() }
        onExited: { root.modelStoreBusy = false; root.modelSwitchActive = false; root.modelSwitchProgress = 0; if (!modelStoreStatusProcess.running) modelStoreStatusProcess.running = true }
    }
    IpcHandler {
        target: "host"

        function openTerminal(): void {
            if (!hostConsoleProcess.running)
                hostConsoleProcess.running = true
        }

        function openEnvironments(): void {
            root.environmentKeyboardFocus = false
            root.togglePopup("environments", environmentButton)
        }

        function refreshModel(): void {
            if (!modelStoreStatusProcess.running && !modelStoreActionProcess.running)
                modelStoreStatusProcess.running = true
        }

        function modelStatus(): string {
            return JSON.stringify(root.modelStoreState)
        }

        function popupStatus(): string {
            return JSON.stringify({ kind: root.popupKind, visible: popup.visible,
                                    width: popup.implicitWidth, height: popup.implicitHeight,
                                    environment_error: root.environmentSwitchError,
                                    environment_form_name: environmentNameInput.text,
                                    environment_description_length: environmentDescriptionInput.text.length })
        }

        function toggleControls(): void {
            root.togglePopup("controls", controlCenterButton)
        }

        function toggleCalendar(): void {
            root.togglePopup("calendar", calendarButton)
        }

        function toggleModel(): void {
            if (root.isHub)
                root.togglePopup("model", modelStoreButton)
        }

        function toggleBattery(): void {
            root.togglePopup("battery", batteryButton)
        }

        function openControls(): void {
            root.popupKind = "controls"
            root.popupTarget = controlCenterButton
            root.showPopup()
        }

        function openWifiControls(): void {
            openControls()
            root.controlsWifiOpen = true
            root.controlsBluetoothOpen = false
            root.controlsAudioOpen = false
            root.controlsMicrophoneOpen = false
        }

        function openBluetoothControls(): void {
            openControls()
            root.controlsWifiOpen = false
            root.controlsBluetoothOpen = true
            root.controlsAudioOpen = false
            root.controlsMicrophoneOpen = false
        }

        function openVolumeControls(): void {
            openControls()
            root.controlsWifiOpen = false
            root.controlsBluetoothOpen = false
            root.controlsAudioOpen = true
            root.controlsMicrophoneOpen = false
            Qt.callLater(function() { volumeSlider.forceActiveFocus() })
        }

        function openMicrophoneControls(): void {
            openControls()
            root.controlsWifiOpen = false
            root.controlsBluetoothOpen = false
            root.controlsAudioOpen = false
            root.controlsMicrophoneOpen = true
            Qt.callLater(function() { microphoneSlider.forceActiveFocus() })
        }

        function openCalendar(): void {
            root.popupKind = "calendar"
            root.popupTarget = calendarButton
            root.showPopup()
        }

        function brightnessUp(): void { root.stepDisplayBrightness(5) }
        function brightnessDown(): void { root.stepDisplayBrightness(-5) }
        function volumeUp(): void { root.stepVolume(5) }
        function volumeDown(): void { root.stepVolume(-5) }
        function volumeMute(): void { root.toggleVolumeMute() }
        function microphoneMute(): void { root.toggleMicrophoneMute() }
    }
    Process {
        id: audioStateProcess
        command: ["/run/apx/audio-state-client-v1.py", "get"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    var state = JSON.parse(text)
                    root.microphoneActive = state.microphone_active === true
                } catch (error) {
                    root.microphoneActive = false
                    root.microphoneText = "--"
                }
            }
        }
    }
    Process {
        id: powerPrepareProcess
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    var result = JSON.parse(text)
                    root.powerBusy = false
                    if (result.prepared) {
                        root.powerToken = result.token
                        root.powerMessage = (result.action === "reboot" ? "REINICIAR" :
                                            result.action === "suspend" ? "SUSPENDER" : "DESLIGAR")
                                            + (result.action === "suspend"
                                               ? " a máquina física? O Environment continuará aberto."
                                               : " a máquina física? O Environment atual será fechado.")
                        if (result.reboot_required) root.powerMessage += " A atualização pede reinício."
                    } else {
                        root.powerToken = ""
                        root.powerMessage = "AÇÃO BLOQUEADA :: " + (result.blockers || []).join(" | ")
                    }
                } catch (error) {
                    root.powerBusy = false
                    root.powerToken = ""
                    root.powerMessage = "Não foi possível consultar o Host."
                }
            }
        }
    }
    Process {
        id: powerConfirmProcess
        command: ["/home/apx/.local/libexec/apx-system-power-client-v1.py", "confirm", "--token-stdin"]
        stdinEnabled: true
        onStarted: powerConfirmProcess.write(root.powerToken + "\n")
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    var result = JSON.parse(text)
                    root.powerMessage = result.accepted ? "PEDIDO ACEITE PELO HOST" : "PEDIDO RECUSADO"
                } catch (error) { root.powerMessage = "O Host recusou a ação." }
            }
        }
        onExited: root.powerBusy = false
    }
    Process {
        id: powerCancelProcess
        command: ["/home/apx/.local/libexec/apx-system-power-client-v1.py", "cancel", "--token-stdin"]
        stdinEnabled: true
        onStarted: powerCancelProcess.write(root.powerToken + "\n")
        onExited: {
            root.powerBusy = false
            root.powerToken = ""
            root.powerMessage = ""
            root.powerConfirmOpen = false
        }
    }

    Component.onCompleted: {
        calendarLoadProcess.running = true
        shortcutApplyProcess.command = ["/home/apx/.local/bin/apx-shortcuts-v1", "apply"]
        shortcutApplyProcess.running = true
    }

    Timer {
        id: displayBrightnessDebounce
        interval: 20
        repeat: false
        onTriggered: root.dispatchDisplayBrightness()
    }

    Timer {
        interval: 1000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: root.updateClock()
    }

    Timer {
        interval: 10000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            if (!hostStatusProcess.running) hostStatusProcess.running = true
            if (!volumeProcess.running) volumeProcess.running = true
            if (!microphoneProcess.running) microphoneProcess.running = true
            if (!batteryProcess.running) batteryProcess.running = true
            if (root.isHub && !hardwareProfileProcess.running) hardwareProfileProcess.running = true
        }
    }
    Timer {
        interval: root.modelStoreBusy ? 500 : 5000; running: root.isHub; repeat: true; triggeredOnStart: true
        onTriggered: if (root.isHub && !modelStoreStatusProcess.running) modelStoreStatusProcess.running = true
    }

    Timer {
        interval: 250; running: !root.identityReady; repeat: true; triggeredOnStart: true
        onTriggered: if (!environmentIdentityProcess.running) environmentIdentityProcess.running = true
    }

    Timer {
        interval: 350
        running: root.environmentManagementBusy
        repeat: true
        onTriggered: if (!environmentManagementStatusProcess.running) environmentManagementStatusProcess.running = true
    }

    Timer {
        interval: 120
        running: root.environmentSwitchPending
        repeat: true
        onTriggered: root.environmentSwitchProgress = Math.min(86, root.environmentSwitchProgress + 2)
    }

    Timer {
        interval: 1000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: if (!audioStateProcess.running) audioStateProcess.running = true
    }

    Timer {
        interval: 500
        repeat: true
        running: root.bluetoothPairSessionId.length > 0
                 && root.bluetoothPairPhase !== "needs-response"
                 && root.bluetoothPairPhase !== "completed"
                 && root.bluetoothPairPhase !== "failed"
        onTriggered: {
            if (!bluetoothPairStatusProcess.running && !bluetoothPairBeginProcess.running && !bluetoothPairRespondProcess.running) {
                bluetoothPairStatusProcess.command = ["/run/apx/host-services-client-v3.py", "bluetooth-pair-status", root.bluetoothPairSessionId]
                bluetoothPairStatusProcess.running = true
            }
        }
    }

    Timer {
        interval: 400
        repeat: true
        running: root.wifiTogglePhase.length > 0
                 || root.bluetoothPowerPhase.length > 0
                 || root.bluetoothDevicePendingAddress.length > 0
        onTriggered: if (!hostStatusProcess.running) hostStatusProcess.running = true
    }

    component BarButton: Rectangle {
        id: button
        property string label: ""
        property string alternateLabel: ""
        property bool alternateActive: false
        signal activated()
        implicitWidth: Math.max(buttonText.implicitWidth, alternateButtonText.implicitWidth) + 22
        implicitHeight: 32
        scale: mouse.pressed ? 0.96 : 1
        radius: 7
        color: mouse.containsMouse ? root.cyanDim : "transparent"
        border.width: mouse.containsMouse ? 1 : 0
        border.color: root.cyan
        Behavior on scale { NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }
        Text {
            id: buttonText
            anchors.centerIn: parent
            text: button.label
            opacity: button.alternateActive ? 0 : 1
            scale: button.alternateActive ? 0.72 : 1
            color: mouse.containsMouse ? root.cyan : root.textMain
            font.family: "Adwaita Mono"
            font.pixelSize: 13
            font.bold: true
            Behavior on opacity { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
            Behavior on scale { NumberAnimation { duration: 180; easing.type: Easing.OutBack } }
        }
        Text {
            id: alternateButtonText
            anchors.centerIn: parent
            text: button.alternateLabel
            opacity: button.alternateActive ? 1 : 0
            scale: button.alternateActive ? 1 : 0.72
            color: mouse.containsMouse ? root.cyan : root.textMain
            font.family: "Adwaita Mono"
            font.pixelSize: 13
            font.bold: true
            Behavior on opacity { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
            Behavior on scale { NumberAnimation { duration: 180; easing.type: Easing.OutBack } }
        }
        MouseArea {
            id: mouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: button.activated()
        }
    }

    component BounceMouseArea: MouseArea {
        id: bounceMouse

        NumberAnimation {
            id: bounceDown
            target: bounceMouse.parent
            property: "scale"
            to: 0.96
            duration: 40
            easing.type: Easing.OutCubic
        }

        NumberAnimation {
            id: bounceUp
            target: bounceMouse.parent
            property: "scale"
            to: 1
            duration: 70
            easing.type: Easing.OutCubic
        }

        onPressed: bounceDown.restart()
        onReleased: bounceUp.restart()
        onCanceled: bounceUp.restart()
    }

    component MenuButton: Rectangle {
        id: menuButton
        property string label: ""
        property bool accent: false
        property bool keyboardFocused: false
        signal activated()
        width: parent ? parent.width : 250
        height: 34
        opacity: enabled ? 1 : 0.42
        radius: 6
        color: keyboardFocused ? "#244b55" : (menuMouse.containsMouse ? root.cyanDim : (accent ? "#1c3941" : "#101920"))
        border.width: accent || keyboardFocused ? 1 : 0
        border.color: keyboardFocused ? "#a6f3ff" : root.cyan
        Text {
            anchors.left: parent.left
            anchors.leftMargin: 11
            anchors.verticalCenter: parent.verticalCenter
            text: menuButton.label
            color: menuButton.accent ? root.cyan : root.textMain
            font.family: "Adwaita Mono"
            font.pixelSize: root.menuBodySize
        }
        BounceMouseArea {
            id: menuMouse
            anchors.fill: parent
            enabled: menuButton.enabled
            hoverEnabled: true
            cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
            onClicked: menuButton.activated()
        }
    }

    component EventField: Rectangle {
        id: field
        property alias text: input.text
        property string placeholder: ""
        width: parent ? parent.width : 300
        height: 34
        radius: 6
        color: "#101920"
        border.width: input.activeFocus ? 1 : 0
        border.color: root.cyan
        TextInput {
            id: input
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: 10
            verticalAlignment: TextInput.AlignVCenter
            color: root.textMain
            selectionColor: root.cyanDim
            font.family: "Adwaita Mono"
            font.pixelSize: 12
            clip: true
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: field.placeholder
                visible: !input.text.length && !input.activeFocus
                color: root.textDim
                font: input.font
            }
        }
    }

    component EventToggle: Rectangle {
        id: toggle
        property string label: ""
        property bool checked: false
        property bool keyboardFocused: false
        signal activated()
        height: 30
        radius: 6
        color: keyboardFocused ? "#1d4650" : (checked ? root.cyanDim : "#101920")
        border.width: checked || keyboardFocused ? 1 : 0
        border.color: keyboardFocused ? "#a6f3ff" : root.cyan
        Text {
            anchors.left: parent.left
            anchors.leftMargin: 12
            anchors.verticalCenter: parent.verticalCenter
            text: (toggle.checked ? "[✓] " : "[ ] ") + toggle.label
            color: toggle.checked ? root.cyan : root.textDim
            font.family: "Adwaita Mono"
            font.pixelSize: 10
            font.bold: true
        }
        BounceMouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: toggle.activated() }
    }

    component PresetCard: Rectangle {
        id: presetCard
        property string title: ""
        property string description: ""
        property string additions: ""
        property bool selected: false
        property bool keyboardFocused: false
        signal activated()
        radius: 8
        color: keyboardFocused ? "#244b55" : (presetMouse.containsMouse ? "#203b46" : (selected ? "#1c3941" : "#101920"))
        border.width: selected || keyboardFocused ? 1 : 0
        border.color: keyboardFocused ? "#a6f3ff" : root.cyan
        Column {
            anchors.fill: parent; anchors.margins: 9; spacing: 3
            Text { width: parent.width; text: presetCard.title; color: presetCard.selected ? root.cyan : root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true }
            Text { width: parent.width; text: presetCard.description; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize; wrapMode: Text.WordWrap; maximumLineCount: 2; elide: Text.ElideRight }
            Text { width: parent.width; text: presetCard.additions; color: presetCard.selected ? root.cyan : root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize; font.bold: true; elide: Text.ElideRight }
        }
        BounceMouseArea { id: presetMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: presetCard.activated() }
    }

    component FeatureCard: Rectangle {
        id: featureCard
        property string label: ""
        property string detail: ""
        property string programs: ""
        property bool checked: false
        property bool keyboardFocused: false
        property bool infoVisible: false
        signal activated()
        signal infoRequested()
        height: infoVisible ? 72 : 34
        radius: 7
        color: keyboardFocused ? "#1d4650" : (featureMouse.containsMouse ? "#18313a" : (checked ? "#142c34" : "#101920"))
        border.width: checked || keyboardFocused ? 1 : 0
        border.color: keyboardFocused ? "#a6f3ff" : root.cyanDim
        Rectangle {
            anchors.left: parent.left; anchors.leftMargin: 10; anchors.top: parent.top; anchors.topMargin: 8
            width: 18; height: 18; radius: 5
            color: featureCard.checked ? root.cyanDim : "#182731"
            border.width: 1; border.color: featureCard.checked ? root.cyan : "#52656d"
            Text { anchors.centerIn: parent; text: featureCard.checked ? "✓" : ""; color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: 11; font.bold: true }
        }
        Text { anchors.left: parent.left; anchors.leftMargin: 36; anchors.right: parent.right; anchors.rightMargin: 10; anchors.top: parent.top; anchors.topMargin: 9; text: featureCard.label; color: featureCard.checked ? root.cyan : root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; font.bold: true; elide: Text.ElideRight }
        Text { visible: featureCard.infoVisible; anchors.left: parent.left; anchors.leftMargin: 10; anchors.right: parent.right; anchors.rightMargin: 10; anchors.top: parent.top; anchors.topMargin: 31; text: featureCard.detail; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize; elide: Text.ElideRight }
        Text { visible: featureCard.infoVisible; anchors.left: parent.left; anchors.leftMargin: 10; anchors.right: parent.right; anchors.rightMargin: 10; anchors.bottom: parent.bottom; anchors.bottomMargin: 8; text: featureCard.programs; color: featureCard.programs.indexOf("INSTALA") === 0 ? root.cyan : "#73929a"; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize; font.bold: true; elide: Text.ElideRight }
        BounceMouseArea { id: featureMouse; anchors.fill: parent; acceptedButtons: Qt.LeftButton; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: featureCard.activated() }
        MouseArea { anchors.fill: parent; acceptedButtons: Qt.RightButton; cursorShape: Qt.WhatsThisCursor; onClicked: featureCard.infoRequested() }
    }

    component WifiSecurityIcon: Item {
        id: securityIcon
        property bool open: false
        width: 14
        height: 14

        Rectangle {
            visible: !securityIcon.open
            x: 2; y: 6; width: 10; height: 7; radius: 1
            color: root.textDim
        }
        Rectangle {
            visible: !securityIcon.open
            x: 4; y: 1; width: 6; height: 8; radius: 3
            color: "transparent"
            border.width: 2
            border.color: root.textDim
        }
        Rectangle {
            visible: securityIcon.open
            anchors.centerIn: parent
            width: 9; height: 9; radius: 5
            color: "transparent"
            border.width: 2
            border.color: root.textDim
        }
    }

    component ControlIcon: Item {
        property url source
        property color tint: root.cyan

        ToolButton {
            anchors.fill: parent
            padding: 0
            focusPolicy: Qt.NoFocus
            hoverEnabled: false
            display: AbstractButton.IconOnly
            icon.source: parent.source
            icon.color: parent.tint
            icon.width: Math.max(18, width)
            icon.height: Math.max(18, height)
            background: Item {}
        }
    }

    PanelWindow {
        id: bar
        anchors { top: true; left: true; right: true }
        implicitHeight: 46
        exclusiveZone: 46
        color: "transparent"

        Rectangle {
            anchors.fill: parent
            anchors.topMargin: 5
            anchors.bottomMargin: 5
            radius: 9
            color: root.panel
            border.width: 1
            border.color: "#26343a"

            MouseArea {
                anchors.fill: parent
                enabled: popup.visible
                onClicked: root.closePopup()
            }

            Row {
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                spacing: 4
                BarButton {
                    id: calendarButton
                    label: "[ " + root.clockText + " ]"
                    onActivated: root.togglePopup("calendar", this)
                }
            }

            BarButton {
                id: environmentButton
                anchors.centerIn: parent
                label: root.isHub ? "[ HUB · ENVIRONMENTS ]" : "[ " + root.environmentLabel + " · VOLTAR AO HUB ]"
                onActivated: {
                    root.environmentKeyboardFocus = false
                    root.togglePopup("environments", this)
                }
            }

            Row {
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                spacing: 2
                BarButton {
                    id: modelStoreButton
                    visible: root.isHub
                    label: root.modelStoreState.state === "active" ? "[ IA ON ]" : (root.modelStoreState.state === "safe-to-remove" ? "[ SSD OK ]" : "[ IA OFF ]")
                    onActivated: root.togglePopup("model", this)
                }
                BarButton {
                    visible: root.microphoneActive
                    label: "[ MIC ATIVO ]"
                }
                BarButton {
                    id: batteryButton
                    label: "[ BAT " + root.batteryText + " ]"
                    onActivated: root.togglePopup("battery", this)
                }
                BarButton {
                    id: controlCenterButton
                    label: "[|]"
                    alternateLabel: "[A]"
                    alternateActive: popup.visible && root.popupKind === "controls"
                    onActivated: root.togglePopup("controls", this)
                }
            }
        }
    }

    PanelWindow {
        id: environmentTransitionOverlay
        visible: root.environmentSwitchPending
        anchors { top: true; bottom: true; left: true; right: true }
        exclusiveZone: 0
        color: "#fa070c10"

        Column {
            anchors.centerIn: parent
            width: Math.min(520, parent.width - 80)
            spacing: 18
            Text { width: parent.width; horizontalAlignment: Text.AlignHCenter; text: "APX ENVIRONMENTS"; color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: 18; font.bold: true }
            Text { width: parent.width; horizontalAlignment: Text.AlignHCenter; text: root.isHub ? "A ABRIR " + root.selectedEnvironmentName.toUpperCase() : "A REGRESSAR AO HUB"; color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: 14; font.bold: true }
            Rectangle {
                width: parent.width; height: 8; radius: 4; color: "#263941"
                Rectangle { width: parent.width * root.environmentSwitchProgress / 100; height: parent.height; radius: 4; color: root.cyan; Behavior on width { NumberAnimation { duration: 110 } } }
            }
            Text { width: parent.width; horizontalAlignment: Text.AlignHCenter; text: "A preparar a tua sessão…"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize }
        }
    }

    Timer {
        id: popupOpenTimer
        interval: 180
        repeat: false
        onTriggered: root.popupOpening = false
    }

    PanelWindow {
        id: popup
        anchors { top: true; left: true }
        margins { top: 6; left: root.popupLeftMargin }
        exclusiveZone: 0
        aboveWindows: true
        focusable: visible
        WlrLayershell.keyboardFocus: visible ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.None
        implicitWidth: root.popupKind === "calendar" ? 480
                                                     : (root.popupKind === "environments" ? (root.environmentCreateOpen ? 620 : 430)
                                                        : (root.popupKind === "controls" ? 340 * root.controlCenterScale : 300))
        implicitHeight: root.popupKind === "calendar"
                        ? (root.calendarEditor ? 500
                           : (root.calendarView === "day"
                              ? 185 + Math.min(4, root.eventsForDate(root.calendarDate).length) * 50
                              : 390 + Math.min(4, root.eventsForDate(root.calendarDate).length) * 44))
                                                       : (root.popupKind === "controls"
                                                          ? (root.controlsAllClosed() ? (root.isHub ? 440 : 394) * root.controlCenterScale
                                                             : ((root.controlsAudioOpen || root.controlsMicrophoneOpen) ? 232
                                                                : (root.controlsBluetoothOpen ? 320 : 480)) * root.controlCenterScale)
                                                          : (root.popupKind === "model" ? 370 : (root.popupKind === "environments" ? root.environmentPopupHeight : 330)))
        visible: false
        color: "transparent"
        // A layer-shell surface can accept both pointer and keyboard input
        // even when opened by an IPC shortcut, which avoids the xdg_popup
        // input-serial limitation of PopupWindow.

        Shortcut {
            sequence: "Escape"
            enabled: popup.visible && !root.wifiPasswordVisible
            onActivated: root.closePopup()
        }

        Rectangle {
            id: popupBackground
            anchors.left: parent.left
            anchors.top: parent.top
            width: root.popupKind === "controls" ? parent.width / root.controlCenterScale : parent.width
            height: root.popupKind === "controls" ? parent.height / root.controlCenterScale : parent.height
            scale: (root.popupKind === "controls" ? root.controlCenterScale : 1) * (root.popupOpening ? 0.94 : 1)
            opacity: root.popupOpening ? 0 : 1
            transformOrigin: Item.TopLeft
            Behavior on scale { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
            Behavior on opacity { NumberAnimation { duration: 130; easing.type: Easing.OutCubic } }
            radius: 10
            color: root.card
            border.width: 1
            border.color: root.cyanDim

            TapHandler {
                acceptedButtons: Qt.LeftButton
                onTapped: function(eventPoint) {
                    if (root.popupKind !== "controls" || !root.wifiPasswordVisible)
                        return
                    var corner = wifiPasswordCard.mapToItem(popupBackground, 0, 0)
                    var insidePassword = eventPoint.position.x >= corner.x
                                      && eventPoint.position.x <= corner.x + wifiPasswordCard.width
                                      && eventPoint.position.y >= corner.y
                                      && eventPoint.position.y <= corner.y + wifiPasswordCard.height
                    if (!insidePassword) {
                        Qt.callLater(function() {
                            if (!root.wifiSelectionTap)
                                root.cancelWifiPassword()
                            root.wifiSelectionTap = false
                        })
                    }
                }
            }

            Flickable {
                anchors.fill: parent
                anchors.margins: 10
                contentWidth: width
                contentHeight: menuContent.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: ScrollBar {
                    policy: menuContent.implicitHeight > popupBackground.height - 20
                            ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff
                }

                Column {
                    id: menuContent
                    width: parent.width
                    spacing: 5

                    Column {
                        width: parent.width
                        spacing: 5
                        visible: root.popupKind === "calendar" && !root.calendarEditor

                        Row {
                            width: parent.width
                            spacing: 4
                            Rectangle {
                                    width: 32; height: 28; radius: 6; color: previousMouse.containsMouse ? root.cyanDim : "#101920"
                                Text { anchors.centerIn: parent; text: "‹"; color: root.cyan; font.pixelSize: 22 }
                                BounceMouseArea { id: previousMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.moveCalendar(-1) }
                            }
                            Text {
                                width: parent.width - 72; height: 28; text: root.calendarTitle(); color: root.textMain
                                horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                                font.family: "Adwaita Mono"; font.pixelSize: root.menuTitleSize; font.bold: true
                            }
                            Rectangle {
                                    width: 32; height: 28; radius: 6; color: nextMouse.containsMouse ? root.cyanDim : "#101920"
                                Text { anchors.centerIn: parent; text: "›"; color: root.cyan; font.pixelSize: 22 }
                                BounceMouseArea { id: nextMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.moveCalendar(1) }
                            }
                        }

                        Row {
                            width: parent.width
                            spacing: 5
                            Repeater {
                                model: [{ key: "day", label: "DIA" }, { key: "month", label: "MÊS" }, { key: "year", label: "ANO" }]
                                Rectangle {
                                    required property var modelData
                                    width: (menuContent.width - 10) / 3; height: 25; radius: 6
                                    color: root.calendarView === modelData.key ? "#15343d" : "#080d11"
                                    border.width: root.calendarView === modelData.key ? 1 : 0; border.color: root.cyan
                                    Text { anchors.centerIn: parent; text: modelData.label; color: root.calendarView === modelData.key ? root.cyan : root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true }
                                    BounceMouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.calendarView = modelData.key }
                                }
                            }
                        }

                        Grid {
                            width: parent.width; columns: 7; rowSpacing: 1; columnSpacing: 3
                            visible: root.calendarView === "month"
                            Repeater {
                                model: root.weekNames
                                Text {
                                    required property string modelData
                                    width: (menuContent.width - 18) / 7; height: 18; text: modelData
                                    color: root.textDim; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                                    font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true
                                }
                            }
                            Repeater {
                                model: root.monthDays()
                                Rectangle {
                                    required property var modelData
                                    property bool today: modelData !== null && root.sameDay(modelData, root.currentDate)
                                    property bool selected: modelData !== null && root.sameDay(modelData, root.calendarDate)
                                    width: (menuContent.width - 18) / 7; height: 30; radius: 6
                                    color: selected ? "#15343d" : (dayMouse.containsMouse && modelData !== null ? "#20313a" : "transparent")
                                    border.width: selected ? 2 : 0; border.color: root.cyan
                                    Rectangle {
                                        visible: parent.today && !parent.selected
                                        anchors.fill: parent; anchors.margins: parent.selected ? 4 : 2
                                        radius: 4; color: "transparent"
                                        border.width: 1; border.color: "#ffb15a"
                                    }
                                    Text {
                                        anchors.centerIn: parent
                                        text: modelData === null ? "" : modelData.getDate()
                                        color: parent.selected ? root.cyan : (parent.today ? "#ffc36b" : root.textMain)
                                        font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize
                                        font.bold: parent.today || parent.selected
                                    }
                                    Rectangle {
                                        visible: modelData !== null && root.eventsForDate(modelData).length > 0
                                        anchors.bottom: parent.bottom; anchors.bottomMargin: 3; anchors.horizontalCenter: parent.horizontalCenter
                                        width: 4; height: 4; radius: 2; color: root.cyan
                                    }
                                    BounceMouseArea {
                                        id: dayMouse; anchors.fill: parent; enabled: modelData !== null; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                        onClicked: root.calendarDate = new Date(modelData.getFullYear(), modelData.getMonth(), modelData.getDate())
                                    }
                                }
                            }
                        }

                        Grid {
                            width: parent.width; columns: 3; rowSpacing: 4; columnSpacing: 4
                            visible: root.calendarView === "year"
                            Repeater {
                                model: root.monthNames
                                Rectangle {
                                    required property string modelData
                                    required property int index
                                    property bool currentMonth: index === root.currentDate.getMonth() && root.calendarDate.getFullYear() === root.currentDate.getFullYear()
                                    width: (menuContent.width - 8) / 3; height: 44; radius: 7
                                    color: currentMonth ? root.cyanDim : (monthMouse.containsMouse ? "#20313a" : "#101920")
                                    border.width: currentMonth ? 1 : 0; border.color: root.cyan
                                    Text { anchors.centerIn: parent; text: modelData.slice(0, 3); color: parent.currentMonth ? root.cyan : root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true }
                                    BounceMouseArea {
                                        id: monthMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                        onClicked: { root.calendarDate = new Date(root.calendarDate.getFullYear(), index, 1); root.calendarView = "month" }
                                    }
                                }
                            }
                        }

                        Column {
                            width: parent.width
                            spacing: 6
                            visible: root.calendarView === "day"

                            Text {
                                visible: root.eventsForDate(root.calendarDate).length === 0
                                text: "-- nenhum evento planeado para este dia --"
                                color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize
                            }
                            ListView {
                                id: dayTimeline
                                width: parent.width
                                height: Math.min(4, count) * 50
                                spacing: 3
                                clip: true
                                interactive: count > 4
                                model: root.sortedEventsForDate(root.calendarDate)
                                ScrollBar.vertical: ScrollBar {
                                    policy: dayTimeline.count > 4 ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
                                }
                                delegate: Item {
                                    required property var modelData
                                    width: dayTimeline.width
                                    height: 47

                                    Text {
                                        width: 52; anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter
                                        text: modelData.time
                                        color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true
                                        horizontalAlignment: Text.AlignRight
                                    }
                                    Rectangle {
                                        anchors.left: parent.left; anchors.leftMargin: 65
                                        anchors.top: parent.top; anchors.bottom: parent.bottom
                                        width: 1; color: root.cyanDim
                                    }
                                    Rectangle {
                                        anchors.left: parent.left; anchors.leftMargin: 61
                                        anchors.verticalCenter: parent.verticalCenter
                                        width: 9; height: 9; radius: 5; color: root.cyan
                                    }
                                    Rectangle {
                                        anchors.left: parent.left; anchors.leftMargin: 80
                                        anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
                                        height: 44; radius: 7; color: "#101920"
                                        Text {
                                            anchors.left: parent.left; anchors.leftMargin: 11; anchors.top: parent.top; anchors.topMargin: 7
                                            width: parent.width - 112
                                            text: modelData.title
                                            elide: Text.ElideRight; color: root.textMain
                                            font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true
                                        }
                                        Text {
                                            anchors.left: parent.left; anchors.leftMargin: 11; anchors.bottom: parent.bottom; anchors.bottomMargin: 6
                                            width: parent.width - 112
                                            text: modelData.category + (modelData.notes ? " · " + modelData.notes : "")
                                            elide: Text.ElideRight; color: root.textDim
                                            font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize
                                        }
                                        Rectangle {
                                            id: timelineEdit
                                            anchors.right: timelineRemove.left; anchors.rightMargin: 5; anchors.verticalCenter: parent.verticalCenter
                                            width: 54; height: 28; radius: 5; color: timelineEditMouse.containsMouse ? root.cyanDim : "#18242b"
                                            Text { anchors.centerIn: parent; text: "EDITAR"; color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true }
                                            BounceMouseArea { id: timelineEditMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.beginEditEvent(modelData) }
                                        }
                                        Rectangle {
                                            id: timelineRemove
                                            anchors.right: parent.right; anchors.rightMargin: 7; anchors.verticalCenter: parent.verticalCenter
                                            width: 28; height: 28; radius: 5; color: timelineRemoveMouse.containsMouse ? "#743541" : "#18242b"
                                            Text { anchors.centerIn: parent; text: "×"; color: "#ff91a4"; font.pixelSize: 16 }
                                            BounceMouseArea { id: timelineRemoveMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.deleteEvent(modelData.id) }
                                        }
                                    }
                                }
                            }
                        }

                        Row {
                            width: parent.width
                            spacing: 6
                            Rectangle {
                                width: (parent.width - 6) / 2; height: 34; radius: 6; color: todayMouse.containsMouse ? root.cyanDim : "#101920"
                                Text { anchors.centerIn: parent; text: "[ HOJE ]"; color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true }
                                BounceMouseArea { id: todayMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.calendarDate = new Date(root.currentDate.getFullYear(), root.currentDate.getMonth(), root.currentDate.getDate()) }
                            }
                            Rectangle {
                                width: (parent.width - 6) / 2; height: 34; radius: 6; color: addMouse.containsMouse ? root.cyanDim : "#101920"
                                Text { anchors.centerIn: parent; text: "[ + ] NOVO EVENTO"; color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true }
                                BounceMouseArea { id: addMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.beginEvent() }
                            }
                        }

                        Text {
                            visible: root.calendarView !== "day"
                            text: "EVENTOS : " + root.dateKey(root.calendarDate)
                            color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true
                        }
                        Text {
                            visible: root.calendarView !== "day" && root.eventsForDate(root.calendarDate).length === 0
                            text: "-- nenhum evento neste dia --"
                            color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize
                        }
                        ListView {
                            id: dayEventList
                            width: parent.width
                            height: root.calendarView === "day" ? 0 : Math.min(4, count) * 46
                            visible: root.calendarView !== "day"
                            spacing: 4
                            clip: true
                            interactive: count > 4
                            model: root.eventsForDate(root.calendarDate)
                            ScrollBar.vertical: ScrollBar {
                                policy: dayEventList.count > 4 ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
                            }
                            delegate: Rectangle {
                                required property var modelData
                                width: menuContent.width; height: 42; radius: 6
                                color: "#101920"; opacity: modelData.active ? 1 : 0.55
                                Rectangle { width: 4; height: parent.height; radius: 2; color: root.cyan }
                                Text {
                                    anchors.left: parent.left; anchors.leftMargin: 12; anchors.verticalCenter: parent.verticalCenter
                                    width: parent.width - 108
                                    text: modelData.time + "  " + modelData.title + "  [" + modelData.category + "]"
                                    elide: Text.ElideRight; color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize
                                }
                                Rectangle {
                                    id: editEvent
                                    anchors.right: removeEvent.left; anchors.rightMargin: 5; anchors.verticalCenter: parent.verticalCenter
                                    width: 54; height: 28; radius: 5; color: editMouse.containsMouse ? root.cyanDim : "#18242b"
                                    Text { anchors.centerIn: parent; text: "EDITAR"; color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true }
                                    BounceMouseArea { id: editMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.beginEditEvent(modelData) }
                                }
                                Rectangle {
                                    id: removeEvent
                                    anchors.right: parent.right; anchors.rightMargin: 6; anchors.verticalCenter: parent.verticalCenter
                                    width: 28; height: 28; radius: 5; color: removeMouse.containsMouse ? "#743541" : "#18242b"
                                    Text { anchors.centerIn: parent; text: "×"; color: "#ff91a4"; font.pixelSize: 16 }
                                    BounceMouseArea { id: removeMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.deleteEvent(modelData.id) }
                                }
                            }
                        }
                    }

                    Column {
                        width: parent.width
                        spacing: 6
                        visible: root.popupKind === "calendar" && root.calendarEditor

                        Row {
                            width: parent.width
                            Text {
                                width: parent.width - 42; height: 30; verticalAlignment: Text.AlignVCenter
                                text: root.editingEventId ? "[ EDITAR EVENTO ]" : "[ + ] NOVO EVENTO"
                                color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuTitleSize; font.bold: true
                            }
                            Rectangle {
                                width: 34; height: 30; radius: 6; color: cancelTopMouse.containsMouse ? "#743541" : "#101920"
                                Text { anchors.centerIn: parent; text: "×"; color: "#ff91a4"; font.pixelSize: 18 }
                                BounceMouseArea { id: cancelTopMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.calendarEditor = false }
                            }
                        }
                        Text { text: "TÍTULO"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize }
                        EventField { text: root.draftTitle; placeholder: "Nome do evento"; onTextChanged: root.draftTitle = text }

                        Row {
                            width: parent.width; spacing: 6
                            Column {
                                width: (parent.parent.width - 6) * 0.62; spacing: 4
                                Text { text: "DATA (AAAA-MM-DD)"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize }
                                EventField { width: parent.width; text: root.draftDate; placeholder: "2026-08-02"; onTextChanged: root.draftDate = text }
                            }
                            Column {
                                width: (parent.parent.width - 6) * 0.38; spacing: 4
                                Text { text: "HORA"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize }
                                EventField { width: parent.width; text: root.draftTime; placeholder: "09:00"; onTextChanged: root.draftTime = text }
                            }
                        }

                        Text { text: "CATEGORIA"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize }
                        Rectangle {
                            width: parent.width; height: 34; radius: 6
                            color: categoryButtonMouse.containsMouse ? root.cyanDim : "#101920"
                            border.width: root.categoryPickerOpen ? 1 : 0; border.color: root.cyan
                            Text {
                                anchors.left: parent.left; anchors.leftMargin: 10; anchors.verticalCenter: parent.verticalCenter
                                text: root.draftCategory || "ESCOLHER CATEGORIA"
                                color: root.draftCategory ? root.textMain : root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize
                            }
                            Text { anchors.right: parent.right; anchors.rightMargin: 10; anchors.verticalCenter: parent.verticalCenter; text: root.categoryPickerOpen ? "▴" : "▾"; color: root.cyan }
                            BounceMouseArea { id: categoryButtonMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.categoryPickerOpen = !root.categoryPickerOpen }
                        }
                        Column {
                            width: parent.width; spacing: 4; visible: root.categoryPickerOpen
                            Text {
                                visible: root.calendarCategories.length === 0
                                text: "-- ainda não existem categorias --"
                                color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize
                            }
                            ListView {
                                width: parent.width
                                height: Math.min(4, count) * 30
                                spacing: 3; clip: true; interactive: count > 4
                                model: root.calendarCategories
                                delegate: Rectangle {
                                    required property string modelData
                                    width: ListView.view.width; height: 27; radius: 5
                                    color: root.draftCategory === modelData ? root.cyanDim : "#101920"
                                    Text { anchors.left: parent.left; anchors.leftMargin: 10; anchors.verticalCenter: parent.verticalCenter; text: modelData; color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize }
                                    BounceMouseArea {
                                        anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                                        onClicked: { root.draftCategory = modelData; root.categoryPickerOpen = false }
                                    }
                                }
                            }
                            Rectangle {
                                width: parent.width; height: 30; radius: 5; color: newCategoryMouse.containsMouse ? root.cyanDim : "#101920"
                                Text { anchors.centerIn: parent; text: "[ + ] CRIAR NOVA CATEGORIA"; color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true }
                                BounceMouseArea { id: newCategoryMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.newCategoryOpen = true }
                            }
                        }
                        Row {
                            width: parent.width; spacing: 6; visible: root.newCategoryOpen
                            EventField { width: parent.width - 86; text: root.newCategoryName; placeholder: "NOME DA CATEGORIA"; onTextChanged: root.newCategoryName = text }
                            Rectangle {
                                width: 80; height: 34; radius: 6; color: createCategoryMouse.containsMouse ? "#317f91" : root.cyanDim
                                Text { anchors.centerIn: parent; text: "CRIAR"; color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true }
                                BounceMouseArea { id: createCategoryMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.createCategory() }
                            }
                        }

                        Text { text: "NOTAS (OPCIONAL)"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize }
                        EventField { text: root.draftNotes; placeholder: "Local, descrição, ligação…"; onTextChanged: root.draftNotes = text }

                        Text { text: "PARTILHA"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize }
                        EventToggle {
                            width: parent.width
                            label: root.draftShared ? "Partilhar entre Environments" : "Não Partilhar entre Environments"
                            checked: root.draftShared
                            onActivated: root.draftShared = !root.draftShared
                        }

                        Text { text: "AVISAR ANTES"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize }
                        Row {
                            width: parent.width; spacing: 5
                            EventField {
                                width: 58
                                text: root.draftReminderAmount
                                placeholder: "1"
                                onTextChanged: root.draftReminderAmount = text.replace(/[^0-9]/g, "")
                            }
                            Repeater {
                                model: ["Minutos", "Horas", "Dias", "Semanas"]
                                Rectangle {
                                    required property string modelData
                                    width: (menuContent.width - 73) / 4; height: 34; radius: 5
                                    color: root.draftReminderUnit === modelData ? root.cyanDim : "#101920"
                                    border.width: root.draftReminderUnit === modelData ? 1 : 0; border.color: root.cyan
                                    Text {
                                        anchors.centerIn: parent; text: modelData
                                        color: root.draftReminderUnit === modelData ? root.cyan : root.textDim
                                        font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true
                                    }
                                    BounceMouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.draftReminderUnit = modelData }
                                }
                            }
                        }
                        Rectangle {
                            width: parent.width; height: 34; radius: 6
                            color: addReminderMouse.containsMouse ? "#317f91" : root.cyanDim
                            border.width: 1; border.color: root.cyan
                            Text {
                                anchors.centerIn: parent
                                text: "[ + ] ADICIONAR LEMBRETE"
                                color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true
                            }
                            BounceMouseArea {
                                id: addReminderMouse
                                anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                onClicked: root.addDraftReminder()
                            }
                        }
                        Text {
                            visible: root.draftReminders.length === 0
                            text: "-- sem lembretes adicionados --"
                            color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize
                        }
                        Flow {
                            width: parent.width
                            spacing: 5
                            Repeater {
                                model: root.draftReminders
                                Rectangle {
                                    required property int modelData
                                    height: 30
                                    width: reminderText.implicitWidth + 42
                                    radius: 6; color: "#101920"
                                    border.width: 1; border.color: root.cyanDim
                                    Text {
                                        id: reminderText
                                        anchors.left: parent.left; anchors.leftMargin: 10; anchors.verticalCenter: parent.verticalCenter
                                        text: root.reminderLabel(modelData)
                                        color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize
                                    }
                                    Text {
                                        anchors.right: parent.right; anchors.rightMargin: 9; anchors.verticalCenter: parent.verticalCenter
                                        text: "×"; color: "#ff91a4"; font.pixelSize: root.menuTitleSize
                                    }
                                    BounceMouseArea {
                                        anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                                        onClicked: root.removeDraftReminder(modelData)
                                    }
                                }
                            }
                        }

                        Text {
                            visible: root.eventError.length > 0
                            text: root.eventError; color: "#ff91a4"; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true
                        }
                        Row {
                            width: parent.width; spacing: 6
                            Rectangle {
                                width: (parent.width - 6) / 2; height: 36; radius: 6; color: cancelMouse.containsMouse ? "#293840" : "#101920"
                                Text { anchors.centerIn: parent; text: "CANCELAR"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize }
                                BounceMouseArea { id: cancelMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.calendarEditor = false }
                            }
                            Rectangle {
                                width: (parent.width - 6) / 2; height: 36; radius: 6; color: saveMouse.containsMouse ? "#317f91" : root.cyanDim
                                border.width: 1; border.color: root.cyan
                                Text { anchors.centerIn: parent; text: root.editingEventId ? "GUARDAR ALTERAÇÕES" : "GUARDAR EVENTO"; color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true }
                                BounceMouseArea { id: saveMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.saveDraftEvent() }
                            }
                        }
                    }

                Text {
                    visible: root.popupKind !== "calendar"
                    text: root.popupKind === "controls" ? "CENTRO DE CONTROLO" : (root.popupKind === "model" ? "MODELO LOCAL" : (root.popupKind === "environments" ? "ENVIRONMENTS" : "[ " + root.popupKind.toUpperCase() + " CONTROL ]"))
                    color: root.cyan
                    font.family: "Adwaita Mono"
                    font.pixelSize: root.menuTitleSize
                    font.bold: true
                }
                Rectangle { visible: root.popupKind !== "calendar" && root.popupKind !== "controls"; width: parent.width; height: 1; color: root.cyanDim }

                Column {
                    width: parent.width; spacing: 10; visible: root.popupKind === "model"
                    Rectangle {
                        width: parent.width; height: 76; radius: 9; color: "#13252c"; border.width: 1; border.color: root.modelStoreState.state === "active" ? root.cyan : "#31505d"
                        Text { anchors.left: parent.left; anchors.leftMargin: 12; anchors.top: parent.top; anchors.topMargin: 11; text: root.modelStoreState.model || "Qwen2.5-Coder 3B Fast"; color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true }
                        Text { anchors.left: parent.left; anchors.leftMargin: 12; anchors.bottom: parent.bottom; anchors.bottomMargin: 11; text: root.modelStoreState.state === "active" ? "● MODELO ATIVO · SSD RO" : (root.modelStoreState.state === "model-stopped" ? "○ MODELO OFF · SSD MONTADO" : (root.modelStoreState.state === "safe-to-remove" ? "● PODE REMOVER O SSD" : "○ SSD AUSENTE")); color: root.modelStoreState.state === "active" ? root.cyan : root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; font.bold: true }
                    }
                    Text { width: parent.width; text: "SELECIONAR MODELO"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize; font.bold: true }
                    Row {
                        id: modelSelectorRow
                        property real cellWidth: (width - 8) / 3
                        width: parent.width; height: 38; spacing: 4
                        Repeater {
                            model: root.modelStoreState.models || []
                            delegate: MenuButton {
                                required property var modelData
                                width: modelSelectorRow.cellWidth; height: modelSelectorRow.height
                                label: (root.modelStoreState.selected_profile === modelData.profile ? "● " : "") + (modelData.profile === "fast" ? "3B FAST" : (modelData.profile === "balanced" ? "7B" : "30B"))
                                accent: root.modelStoreState.selected_profile === modelData.profile
                                onActivated: if (!root.modelStoreBusy && root.modelStoreState.mounted === true && root.modelStoreState.selected_profile !== modelData.profile) root.modelStoreAction("model-select", modelData.profile)
                            }
                        }
                    }
                    Rectangle {
                        width: parent.width; height: 48; radius: 7; color: root.modelSwitchActive ? "#101f25" : "transparent"; border.width: root.modelSwitchActive ? 1 : 0; border.color: root.cyanDim
                        Text { visible: !root.modelSwitchActive; anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter; text: root.modelStoreState.model_detail || ""; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize }
                        Text { visible: root.modelSwitchActive; anchors.left: parent.left; anchors.leftMargin: 9; anchors.right: parent.right; anchors.rightMargin: 9; anchors.top: parent.top; anchors.topMargin: 7; text: "A LIGAR AO NOVO MODELO · " + root.modelSwitchProgress + "%"; color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; font.bold: true }
                        Text { visible: root.modelSwitchActive; anchors.left: parent.left; anchors.leftMargin: 9; anchors.right: parent.right; anchors.rightMargin: 9; anchors.top: parent.top; anchors.topMargin: 23; elide: Text.ElideRight; text: root.modelSwitchLabel; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize }
                        Rectangle { visible: root.modelSwitchActive; anchors.left: parent.left; anchors.leftMargin: 9; anchors.right: parent.right; anchors.rightMargin: 9; anchors.bottom: parent.bottom; anchors.bottomMargin: 5; height: 4; radius: 2; color: "#263941"; Rectangle { width: parent.width * Math.max(0, Math.min(100, root.modelSwitchProgress)) / 100; height: parent.height; radius: 2; color: root.cyan } }
                    }
                    Text { width: parent.width; wrapMode: Text.WordWrap; text: root.modelStoreError.length ? root.modelStoreError : (root.modelStoreState.message || "A verificar…"); color: root.modelStoreError.length ? "#ff91a4" : root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize }
                    Row {
                        width: parent.width; height: 42; spacing: 6
                        MenuButton { width: (parent.width - 6) / 2; height: parent.height; label: root.modelStoreState.server_active ? "DESATIVAR MODELO" : "ATIVAR MODELO"; accent: true; onActivated: if (!root.modelStoreBusy && root.modelStoreState.mounted === true) root.modelStoreAction(root.modelStoreState.server_active ? "model-stop" : "model-start") }
                        MenuButton { width: (parent.width - 6) / 2; height: parent.height; label: root.modelStoreState.mounted ? (root.modelStoreConfirmDetach ? "CONFIRMAR DESMONTAR" : "DESMONTAR SSD") : "MONTAR SSD"; onActivated: { if (!root.modelStoreBusy && root.modelStoreState.device_present === true) { if (!root.modelStoreState.mounted) root.modelStoreAction("storage-activate"); else if (root.modelStoreConfirmDetach) root.modelStoreAction("safe-detach"); else root.modelStoreConfirmDetach = true } } }
                    }
                    Text { visible: root.modelStoreConfirmDetach; width: parent.width; wrapMode: Text.WordWrap; text: "Segundo toque: para a IA, sincroniza, desmonta e fecha a cifra."; color: "#ffd09a"; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize }
                }

                Column {
                    id: environmentMenu
                    width: parent.width; spacing: 8
                    visible: root.popupKind === "environments"
                    focus: visible
                    Keys.onPressed: function(event) {
                        if (root.environmentCreateOpen) {
                            root.handleEnvironmentCreateKey(event)
                            return
                        }
                        if (!root.isHub) return
                        if (root.environmentDeleteConfirm) {
                            if (event.key === Qt.Key_Left) {
                                root.environmentDeleteFocusIndex = 0
                            } else if (event.key === Qt.Key_Right) {
                                root.environmentDeleteFocusIndex = 1
                            } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                                if (root.environmentDeleteFocusIndex === 0) root.cancelEnvironmentDelete()
                                else root.destroySelectedEnvironment()
                            } else if (event.key === Qt.Key_Escape) {
                                root.cancelEnvironmentDelete()
                            } else {
                                return
                            }
                            event.accepted = true
                            return
                        }
                        if (event.key === Qt.Key_Up) {
                            root.moveEnvironmentFocus(-1)
                            event.accepted = true
                        } else if (event.key === Qt.Key_Down) {
                            root.moveEnvironmentFocus(1)
                            event.accepted = true
                        } else if (event.key === Qt.Key_Left) {
                            root.moveEnvironmentActionFocus(-1)
                            event.accepted = true
                        } else if (event.key === Qt.Key_Right) {
                            root.moveEnvironmentActionFocus(1)
                            event.accepted = true
                        } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                            root.activateEnvironmentFocus()
                            event.accepted = true
                        } else if (event.key === Qt.Key_Delete) {
                            root.deleteFocusedEnvironment()
                            event.accepted = true
                        } else if (event.key === Qt.Key_Escape) {
                            root.closePopup()
                            event.accepted = true
                        }
                    }
                    Rectangle {
                        width: parent.width; height: 62; radius: 9; color: "#13252c"; border.width: 1; border.color: "#31505d"
                        Rectangle { anchors.left: parent.left; anchors.leftMargin: 12; anchors.verticalCenter: parent.verticalCenter; width: 9; height: 9; radius: 5; color: root.cyan }
                        Column {
                            anchors.left: parent.left; anchors.leftMargin: 34; anchors.right: activeEnvironmentBadge.left; anchors.rightMargin: 12; anchors.verticalCenter: parent.verticalCenter; spacing: 3
                            Text { width: parent.width; text: root.environmentLabel; color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuTitleSize; font.bold: true; elide: Text.ElideRight }
                            Text { width: parent.width; text: root.isHub ? "Centro de gestão e segurança" : "Environment isolado em execução"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize; elide: Text.ElideRight }
                        }
                        Rectangle {
                            id: activeEnvironmentBadge
                            anchors.right: parent.right; anchors.rightMargin: 10; anchors.verticalCenter: parent.verticalCenter
                            width: 58; height: 24; radius: 12; color: "#173b42"
                            Text { anchors.centerIn: parent; text: "ATIVO"; color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; font.bold: true }
                        }
                    }

                    Column {
                        width: parent.width; spacing: 7
                        visible: root.isHub && !root.environmentCreateOpen
                        Row {
                            width: parent.width; height: 24
                            Text { width: parent.width * 0.72; anchors.verticalCenter: parent.verticalCenter; text: "Os teus Environments"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize; font.bold: true }
                            Text { width: parent.width * 0.28; anchors.verticalCenter: parent.verticalCenter; horizontalAlignment: Text.AlignRight; text: root.environmentCatalog.length + (root.environmentCatalog.length === 1 ? " ENVIRONMENT" : " ENVIRONMENTS"); color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize }
                        }
                        Repeater {
                            model: root.environmentCatalog.length ? root.environmentCatalog : [{ name: "", display_name: "Ainda não tens Environments", state: "empty", generation: "", category: "general" }]
                            Rectangle {
                                required property var modelData
                                required property int index
                                width: parent ? parent.width : 400; height: 59; radius: 9
                                property bool selected: modelData.name.length > 0 && root.selectedEnvironmentName === modelData.name
                                property bool keyboardFocused: modelData.state === "stopped" && root.environmentKeyboardFocus && root.environmentFocusIndex === index
                                color: keyboardFocused ? "#1d4650" : (selected ? "#17363e" : (environmentChoiceMouse.containsMouse ? "#172a31" : "#111d23"))
                                border.width: 1; border.color: keyboardFocused ? "#a6f3ff" : (selected ? root.cyan : "#263941")
                                Rectangle { anchors.left: parent.left; anchors.leftMargin: 12; anchors.verticalCenter: parent.verticalCenter; width: 8; height: 8; radius: 4; color: modelData.state === "stopped" ? (parent.selected ? root.cyan : "#5d7b82") : "#79505a" }
                                Column {
                                    anchors.left: parent.left; anchors.leftMargin: 32; anchors.right: environmentRowStatus.left; anchors.rightMargin: 12; anchors.verticalCenter: parent.verticalCenter; spacing: 3
                                    Text { width: parent.width; text: String(modelData.display_name || modelData.name); color: modelData.state === "empty" ? root.textDim : root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true; elide: Text.ElideRight }
                                    Text { width: parent.width; text: root.environmentMeta(modelData); color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; elide: Text.ElideRight }
                                }
                                Text { id: environmentRowStatus; anchors.right: parent.right; anchors.rightMargin: 12; anchors.verticalCenter: parent.verticalCenter; text: modelData.state === "stopped" ? (parent.selected ? "SELECIONADO" : "PRONTO") : (modelData.state === "empty" ? "" : "INDISPONÍVEL"); color: parent.selected ? root.cyan : root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; font.bold: true }
                                BounceMouseArea {
                                    id: environmentChoiceMouse
                                    anchors.fill: parent
                                    enabled: modelData.state === "stopped" && !root.environmentManagementBusy
                                    hoverEnabled: true
                                    cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                                    onClicked: {
                                        root.environmentKeyboardFocus = true
                                        root.environmentFocusIndex = index
                                        root.selectEnvironment(modelData)
                                        Qt.callLater(function() { environmentMenu.forceActiveFocus() })
                                    }
                                    onDoubleClicked: { root.environmentFocusIndex = index; root.selectEnvironment(modelData); root.openSelectedEnvironment() }
                                }
                            }
                        }

                        Row {
                            width: parent.width; height: 42; spacing: 6
                            MenuButton { width: (parent.width - 6) / 2; height: parent.height; label: "CRIAR ENVIRONMENT"; keyboardFocused: root.environmentKeyboardFocus && root.environmentFocusIndex === root.environmentCatalog.length; onActivated: { root.environmentFocusIndex = root.environmentCatalog.length; root.beginEnvironmentCreate() } }
                            MenuButton { width: (parent.width - 6) / 2; height: parent.height; label: "APAGAR"; keyboardFocused: root.environmentKeyboardFocus && root.environmentFocusIndex === root.environmentCatalog.length + 1; enabled: root.selectedEnvironmentName.length > 0 && !root.environmentManagementBusy; onActivated: { root.environmentFocusIndex = root.environmentCatalog.length + 1; root.requestEnvironmentDelete() } }
                        }

                        Rectangle {
                            visible: root.environmentDeleteConfirm
                            width: parent.width; height: visible ? 57 : 0; radius: 8; color: "#29181d"; border.width: 1; border.color: "#7d3947"
                            Column { anchors.left: parent.left; anchors.leftMargin: 10; anchors.verticalCenter: parent.verticalCenter; width: parent.width - 162; spacing: 2
                                Text { width: parent.width; text: "Apagar " + root.selectedEnvironmentName + "?"; color: "#ffb2bf"; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; font.bold: true; elide: Text.ElideRight }
                                Text { width: parent.width; text: "Os dados não poderão ser recuperados."; color: "#b98992"; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; elide: Text.ElideRight }
                            }
                            Row { anchors.right: parent.right; anchors.rightMargin: 8; anchors.verticalCenter: parent.verticalCenter; spacing: 5
                                Rectangle { width: 62; height: 31; radius: 6; color: root.environmentDeleteFocusIndex === 0 ? "#244b55" : "#21161a"; border.width: root.environmentDeleteFocusIndex === 0 ? 1 : 0; border.color: "#a6f3ff"
                                    Text { anchors.centerIn: parent; text: "CANCELAR"; color: root.environmentDeleteFocusIndex === 0 ? root.textMain : root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; font.bold: true }
                                    BounceMouseArea { id: cancelDeleteMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: { root.environmentDeleteFocusIndex = 0; root.cancelEnvironmentDelete() } }
                                }
                                Rectangle { width: 70; height: 31; radius: 6; color: root.environmentDeleteFocusIndex === 1 ? "#8a4050" : "#21161a"; border.width: root.environmentDeleteFocusIndex === 1 ? 1 : 0; border.color: "#ffd3da"
                                    Text { anchors.centerIn: parent; text: "APAGAR"; color: root.environmentDeleteFocusIndex === 1 ? "#ffd3da" : root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; font.bold: true }
                                    BounceMouseArea { id: confirmDeleteMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: { root.environmentDeleteFocusIndex = 1; root.destroySelectedEnvironment() } }
                                }
                            }
                        }
                    }

                    Column {
                        width: parent.width; spacing: 9
                        visible: root.isHub && root.environmentCreateOpen
                        Row {
                            width: parent.width; height: 32; spacing: 8
                            Rectangle {
                                width: 92; height: parent.height; radius: 6
                                color: root.environmentCreateFocusIndex === 0 ? "#1d4650" : (environmentBackMouse.containsMouse ? root.cyanDim : "#101920")
                                border.width: root.environmentCreateFocusIndex === 0 ? 1 : 0
                                border.color: "#a6f3ff"
                                Text { anchors.centerIn: parent; text: "‹  VOLTAR"; color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; font.bold: true }
                                BounceMouseArea { id: environmentBackMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: { root.environmentCreateFocusIndex = 0; root.cancelEnvironmentCreate() } }
                            }
                            Text { width: parent.width - 100; anchors.verticalCenter: parent.verticalCenter; text: "NOVO ENVIRONMENT"; color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true }
                        }
                        Rectangle {
                            width: parent.width; height: 42; radius: 7; color: "#0b151a"; border.width: 1; border.color: environmentNameInput.activeFocus || root.environmentCreateFocusIndex === 1 ? root.cyan : "#31505d"
                            TextInput {
                                id: environmentNameInput; anchors.fill: parent; anchors.leftMargin: 11; anchors.rightMargin: 11; verticalAlignment: TextInput.AlignVCenter
                                text: root.environmentDraftName; onTextChanged: root.environmentDraftName = text; maximumLength: 27
                                color: root.textMain; selectionColor: root.cyanDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize
                                onActiveFocusChanged: if (activeFocus) root.environmentCreateFocusIndex = 1
                                onAccepted: { root.environmentCreateFocusIndex = 2; environmentDescriptionInput.forceActiveFocus() }
                                Keys.priority: Keys.BeforeItem
                                Keys.onPressed: function(event) {
                                    if (event.key === Qt.Key_Tab) {
                                        root.environmentCreateFocusIndex = 2
                                        environmentDescriptionInput.forceActiveFocus()
                                        event.accepted = true
                                    } else if (event.key === Qt.Key_Backtab) {
                                        root.environmentCreateFocusIndex = 0
                                        environmentMenu.forceActiveFocus()
                                        event.accepted = true
                                    }
                                }
                            }
                            Text { anchors.left: parent.left; anchors.leftMargin: 11; anchors.verticalCenter: parent.verticalCenter; visible: !environmentNameInput.text.length; text: "nome-do-environment"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize }
                        }
                        Rectangle {
                            width: parent.width; height: 42; radius: 7; color: "#0b151a"; border.width: 1; border.color: environmentDescriptionInput.activeFocus || root.environmentCreateFocusIndex === 2 ? root.cyan : "#31505d"
                            TextInput {
                                id: environmentDescriptionInput; anchors.fill: parent; anchors.leftMargin: 11; anchors.rightMargin: 11; verticalAlignment: TextInput.AlignVCenter
                                text: root.environmentDraftDescription; onTextChanged: root.environmentDraftDescription = text; maximumLength: 120
                                color: root.textMain; selectionColor: root.cyanDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize
                                onActiveFocusChanged: if (activeFocus) root.environmentCreateFocusIndex = 2
                                onAccepted: { root.environmentCreateFocusIndex = 3; environmentMenu.forceActiveFocus() }
                                Keys.priority: Keys.BeforeItem
                                Keys.onPressed: function(event) {
                                    if (event.key === Qt.Key_Backtab) {
                                        root.environmentCreateFocusIndex = 1
                                        environmentNameInput.forceActiveFocus()
                                        event.accepted = true
                                    } else if (event.key === Qt.Key_Tab) {
                                        root.environmentCreateFocusIndex = 3
                                        environmentMenu.forceActiveFocus()
                                        event.accepted = true
                                    }
                                }
                            }
                            Text { anchors.left: parent.left; anchors.leftMargin: 11; anchors.verticalCenter: parent.verticalCenter; visible: !environmentDescriptionInput.text.length; text: "Descrição (opcional)"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize }
                        }
                        Text { width: parent.width; text: "ESCOLHE UM PONTO DE PARTIDA"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize; font.bold: true }
                        Row {
                            width: parent.width; height: 78; spacing: 6
                            PresetCard { width: (parent.width - 12) / 3; height: parent.height; title: "BÁSICO · BASE APX"; description: "Desktop APX sem aplicações adicionais."; additions: "EXTRAS · NENHUM"; selected: root.environmentDesktopPreset === "basic"; keyboardFocused: root.environmentCreateFocusIndex === 3; onActivated: { root.environmentCreateFocusIndex = 3; root.applyEnvironmentPreset("basic") } }
                            PresetCard { width: (parent.width - 12) / 3; height: parent.height; title: "INTERMÉDIO · DIA A DIA"; description: "Base APX, Internet, ficheiros e multimédia."; additions: "+ BRAVE · PDF · MPV"; selected: root.environmentDesktopPreset === "intermediate"; keyboardFocused: root.environmentCreateFocusIndex === 4; onActivated: { root.environmentCreateFocusIndex = 4; root.applyEnvironmentPreset("intermediate") } }
                            PresetCard { width: (parent.width - 12) / 3; height: parent.height; title: "COMPLETO · TRABALHO"; description: "Tudo do Intermédio, Office, periféricos e programação."; additions: "+ LIBREOFFICE · DEV · IMPRESSÃO"; selected: root.environmentDesktopPreset === "complete"; keyboardFocused: root.environmentCreateFocusIndex === 5; onActivated: { root.environmentCreateFocusIndex = 5; root.applyEnvironmentPreset("complete") } }
                        }
                        Row {
                            width: parent.width; height: 20
                            Text { width: parent.width * 0.65; text: "FUNCIONALIDADES"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize; font.bold: true }
                            Text { width: parent.width * 0.35; horizontalAlignment: Text.AlignRight; text: root.selectedEnvironmentModuleKeys().length + "/18  ·  ~" + root.environmentEstimatedMib() + " MiB"; color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize; font.bold: true }
                        }
                        Column {
                            width: parent.width; spacing: 5
                            Repeater {
                                model: root.environmentModuleGroups
                                Column {
                                    id: featureGroup
                                    required property var modelData
                                    required property int index
                                    width: parent ? parent.width : 660; spacing: 4
                                    Rectangle {
                                        width: parent.width; height: 34; radius: 7
                                        property bool keyboardFocused: root.environmentCreateFocusIndex === 6 + index
                                        color: keyboardFocused ? "#1d4650" : (featureDrawerMouse.containsMouse ? "#20343d" : "#13252c")
                                        border.width: keyboardFocused || root.environmentFeatureDrawer === modelData.key ? 1 : 0
                                        border.color: keyboardFocused ? "#a6f3ff" : root.cyanDim
                                        Text { anchors.left: parent.left; anchors.leftMargin: 11; anchors.right: parent.right; anchors.rightMargin: 34; anchors.verticalCenter: parent.verticalCenter; text: modelData.label; color: root.environmentFeatureDrawer === modelData.key ? root.cyan : root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; font.bold: true; elide: Text.ElideRight }
                                        Text { anchors.right: parent.right; anchors.rightMargin: 11; anchors.verticalCenter: parent.verticalCenter; text: root.environmentFeatureDrawer === modelData.key ? "▴" : "▾"; color: root.textDim; font.pixelSize: 14 }
                                        BounceMouseArea { id: featureDrawerMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: { root.environmentCreateFocusIndex = 6 + featureGroup.index; root.environmentFeatureDrawer = root.environmentFeatureDrawer === modelData.key ? "" : modelData.key; root.environmentFeatureInfo = "" } }
                                    }
                                    Grid {
                                        visible: root.environmentFeatureDrawer === modelData.key
                                        width: parent.width; height: visible ? implicitHeight : 0
                                        columns: 2; columnSpacing: 6; rowSpacing: 4
                                        Repeater {
                                            model: modelData.modules
                                            FeatureCard {
                                                required property string modelData
                                                property var moduleInfo: root.environmentModuleInfo(modelData)
                                                width: (environmentMenu.width - 6) / 2
                                                label: moduleInfo.label
                                                detail: moduleInfo.detail
                                                programs: moduleInfo.programs
                                                checked: root.environmentSelectedModules[moduleInfo.key] === true
                                                infoVisible: root.environmentFeatureInfo === moduleInfo.key
                                                keyboardFocused: root.environmentCreateFocusIndex === root.environmentCreateModuleFocusBase + root.environmentModuleIndex(moduleInfo.key)
                                                onActivated: { root.environmentCreateFocusIndex = root.environmentCreateModuleFocusBase + root.environmentModuleIndex(moduleInfo.key); root.setEnvironmentModule(moduleInfo.key, !checked) }
                                                onInfoRequested: { root.environmentCreateFocusIndex = root.environmentCreateModuleFocusBase + root.environmentModuleIndex(moduleInfo.key); root.environmentFeatureInfo = infoVisible ? "" : moduleInfo.key }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        Text { width: parent.width; text: "A palavra-passe de sudo será herdada do HUB. Dependências são ativadas automaticamente."; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; wrapMode: Text.WordWrap }
                        MenuButton { width: parent.width; height: 42; label: root.environmentManagementBusy ? "A CRIAR…" : "CRIAR ENVIRONMENT"; accent: true; keyboardFocused: root.environmentCreateFocusIndex === root.environmentCreateSubmitFocusIndex; enabled: !root.environmentManagementBusy; onActivated: { root.environmentCreateFocusIndex = root.environmentCreateSubmitFocusIndex; root.createEnvironment(environmentNameInput.text, environmentDescriptionInput.text) } }
                    }

                    Rectangle {
                        visible: root.environmentManagementBusy
                        width: parent.width; height: visible ? 34 : 0; radius: 7; color: "#101f25"
                        Text { anchors.left: parent.left; anchors.leftMargin: 9; anchors.top: parent.top; anchors.topMargin: 5; text: root.environmentManagementState.message || "A preparar…"; color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize; font.bold: true }
                        Rectangle { anchors.left: parent.left; anchors.leftMargin: 9; anchors.right: parent.right; anchors.rightMargin: 9; anchors.bottom: parent.bottom; anchors.bottomMargin: 6; height: 4; radius: 2; color: "#263941"; Rectangle { width: parent.width * Math.max(2, Math.min(100, root.environmentManagementState.progress || 2)) / 100; height: parent.height; radius: 2; color: root.cyan } }
                    }

                    MenuButton {
                        visible: !root.isHub
                        width: parent.width; height: visible ? 46 : 0; label: root.environmentSwitchPending ? "A REGRESSAR…" : "VOLTAR AO HUB"; accent: true
                        enabled: root.sessionKindReady && !root.environmentSwitchPending
                        onActivated: root.returnToHub()
                    }
                    Text { visible: !root.isHub; width: parent.width; horizontalAlignment: Text.AlignHCenter; text: "O Environment será fechado em segurança antes da troca."; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize }
                    Text { visible: root.environmentSwitchError.length > 0; width: parent.width; wrapMode: Text.WordWrap; text: root.environmentSwitchError; color: "#ff91a4"; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize; font.bold: true }
                }

                    Column {
                    width: parent.width
                    spacing: 5
                    visible: root.popupKind === "controls"

                    Row {
                        visible: root.controlsAllClosed() && !root.powerConfirmOpen
                        width: parent.width
                        height: visible ? 82 : 0
                        spacing: 6

                        Rectangle {
                            width: (parent.width - 6) / 2; height: parent.height; radius: 11
                            color: wifiSummaryMouse.containsMouse ? "#20323c" : "#182731"
                            border.width: 1; border.color: root.wifiDisplayActive() ? "#31505d" : "#263b45"

                            Rectangle {
                                id: wifiPowerButton
                                z: 3
                                anchors.left: parent.left; anchors.leftMargin: 11; anchors.top: parent.top; anchors.topMargin: 10
                                width: 28; height: 28; radius: 8
                                color: wifiPowerMouse.containsMouse ? root.cyanDim : (root.wifiDisplayActive() ? "#173f49" : "#202d34")
                                ControlIcon {
                                    anchors.centerIn: parent; width: 16; height: 16
                                    source: root.wifiDisplayActive()
                                            ? "file:///usr/share/icons/Adwaita/symbolic/status/network-wireless-signal-excellent-symbolic.svg"
                                            : "file:///usr/share/icons/Adwaita/symbolic/status/network-wireless-offline-symbolic.svg"
                                    tint: root.wifiDisplayActive() ? root.cyan : root.textDim
                                    SequentialAnimation on opacity {
                                        running: root.wifiTogglePhase === "connecting"; loops: Animation.Infinite
                                        NumberAnimation { to: 0.35; duration: 380 }
                                        NumberAnimation { to: 1; duration: 380 }
                                    }
                                }
                                BounceMouseArea { id: wifiPowerMouse; anchors.fill: parent; enabled: !wifiToggleProcess.running && !root.wifiTogglePhase.length; hoverEnabled: true; cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor; onClicked: root.toggleWifiConnection() }
                            }
                            Rectangle {
                                anchors.right: parent.right; anchors.rightMargin: 11; anchors.top: parent.top; anchors.topMargin: 12
                                width: 6; height: 6; radius: 3
                                color: root.wifiDisplayActive() ? "#55dfa1" : "#53656c"
                            }
                            Text {
                                anchors.left: parent.left; anchors.leftMargin: 11; anchors.bottom: wifiSummaryState.top; anchors.bottomMargin: 3
                                text: "Wi-Fi"; color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true
                            }
                            Text {
                                id: wifiSummaryState
                                anchors.left: parent.left; anchors.leftMargin: 11; anchors.right: parent.right; anchors.rightMargin: 10
                                anchors.bottom: parent.bottom; anchors.bottomMargin: 9
                                text: root.wifiTogglePhase === "connecting" ? "A ligar…" : (root.hostState.network_name || "Sem ligação"); elide: Text.ElideRight
                                color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize
                            }
                            BounceMouseArea { id: wifiSummaryMouse; anchors.fill: parent; z: 1; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.openControlSection("wifi") }
                        }

                        Rectangle {
                            width: (parent.width - 6) / 2; height: parent.height; radius: 11
                            color: bluetoothSummaryMouse.containsMouse ? "#20323c" : "#182731"
                            border.width: 1; border.color: root.bluetoothDisplayPowered() ? "#31505d" : "#263b45"

                            Rectangle {
                                id: bluetoothPowerButton
                                z: 3
                                anchors.left: parent.left; anchors.leftMargin: 11; anchors.top: parent.top; anchors.topMargin: 10
                                width: 28; height: 28; radius: 8
                                color: bluetoothPowerSummaryMouse.containsMouse ? root.cyanDim : (root.bluetoothDisplayPowered() ? "#173f49" : "#202d34")
                                ControlIcon {
                                    anchors.centerIn: parent; width: 16; height: 16
                                    source: "file:///usr/share/icons/Adwaita/symbolic/devices/bluetooth-symbolic.svg"
                                    tint: root.bluetoothDisplayPowered() ? root.cyan : root.textDim
                                    SequentialAnimation on opacity {
                                        running: root.bluetoothPowerPhase === "turning-on"; loops: Animation.Infinite
                                        NumberAnimation { to: 0.35; duration: 380 }
                                        NumberAnimation { to: 1; duration: 380 }
                                    }
                                }
                                BounceMouseArea { id: bluetoothPowerSummaryMouse; anchors.fill: parent; enabled: !bluetoothPowerProcess.running && !root.bluetoothPowerPhase.length; hoverEnabled: true; cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor; onClicked: root.toggleBluetoothPower() }
                            }
                            Rectangle {
                                anchors.right: parent.right; anchors.rightMargin: 11; anchors.top: parent.top; anchors.topMargin: 12
                                width: 6; height: 6; radius: 3
                                color: root.bluetoothDisplayPowered() ? "#55dfa1" : "#53656c"
                            }
                            Text {
                                anchors.left: parent.left; anchors.leftMargin: 11; anchors.bottom: bluetoothSummaryState.top; anchors.bottomMargin: 3
                                text: "Bluetooth"; color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true
                            }
                            Text {
                                id: bluetoothSummaryState
                                anchors.left: parent.left; anchors.leftMargin: 11; anchors.bottom: parent.bottom; anchors.bottomMargin: 9
                                text: root.bluetoothPowerPhase === "turning-on" ? "A ligar…" : (root.bluetoothDisplayPowered() ? "Ligado" : "Desligado")
                                color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize
                            }
                            BounceMouseArea { id: bluetoothSummaryMouse; anchors.fill: parent; z: 1; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.openControlSection("bluetooth") }
                        }
                    }

                    Rectangle {
                        visible: root.controlsWifiOpen
                        width: parent.width; height: visible ? 44 : 0; radius: 11
                        color: "#182731"
                        border.width: 1; border.color: "#31505d"
                        Rectangle {
                            anchors.left: parent.left; anchors.leftMargin: 8; anchors.verticalCenter: parent.verticalCenter
                            width: 62; height: 28; radius: 8
                            color: wifiHeaderMouse.containsMouse ? root.cyanDim : "#101920"
                            Text { anchors.centerIn: parent; text: "‹ Voltar"; color: wifiHeaderMouse.containsMouse ? "#ffffff" : root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; font.bold: true }
                            BounceMouseArea { id: wifiHeaderMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.openControlSection("wifi") }
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter; anchors.verticalCenter: parent.verticalCenter
                            text: "Wi-Fi"
                            color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true
                        }
                        Text {
                            anchors.right: parent.right; anchors.rightMargin: 11; anchors.verticalCenter: parent.verticalCenter
                            text: root.wifiTogglePhase === "connecting" ? "A LIGAR…" : (root.wifiDisplayActive() ? "LIGADO" : "SEM LIGAÇÃO")
                            color: root.wifiDisplayActive() ? root.cyan : root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize
                        }
                    }
                    Column {
                        width: parent.width; spacing: 4; visible: root.controlsWifiOpen
                        Rectangle {
                            width: parent.width; height: 56; radius: 11
                            color: root.wifiDisplayActive() ? "#18343e" : "#182731"
                            border.width: 1; border.color: root.wifiDisplayActive() ? root.cyanDim : "#31505d"
                            Text {
                                anchors.left: parent.left; anchors.leftMargin: 14; anchors.top: parent.top; anchors.topMargin: 8
                                width: parent.width - 130; elide: Text.ElideRight
                                text: root.wifiDisplayActive() ? root.hostState.network_name : (root.wifiTogglePhase === "connecting" ? "A ligar a " + root.wifiLastNetwork : "SEM LIGAÇÃO")
                                color: root.wifiDisplayActive() ? root.cyan : root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuTitleSize; font.bold: true
                            }
                            Text {
                                anchors.left: parent.left; anchors.leftMargin: 14; anchors.bottom: parent.bottom; anchors.bottomMargin: 8
                                text: root.wifiDisplayActive()
                                    ? "● Ligado · " + root.wifiDetails(root.hostState.network_name).signal + "%"
                                    : (root.wifiTogglePhase === "connecting" ? "◌ A estabelecer ligação…" : "○ Sem ligação")
                                color: root.wifiDisplayActive() ? "#55dfa1" : root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize
                            }
                            Rectangle {
                                visible: root.wifiDisplayActive() && root.wifiTogglePhase !== "connecting"
                                anchors.right: parent.right; anchors.rightMargin: 8; anchors.verticalCenter: parent.verticalCenter
                                width: 84; height: 28; radius: 8
                                color: disconnectMouse.containsMouse ? "#743541" : "#18242b"
                                Text { anchors.centerIn: parent; text: "Desligar"; color: "#ffb0bd"; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize; font.bold: true }
                                BounceMouseArea { id: disconnectMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: { root.cancelWifiPassword(); root.toggleWifiConnection() } }
                            }
                        }

                        Item {
                            visible: !!root.hostState.network_name
                            width: parent.width
                            height: visible ? 6 : 0
                            BounceMouseArea { anchors.fill: parent; onClicked: root.cancelWifiPassword() }
                        }
                        Item {
                            width: parent.width; height: 18
                            BounceMouseArea { anchors.fill: parent; onClicked: root.cancelWifiPassword() }
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                text: "REDES PRÓXIMAS  ·  " + (root.hostState.available_networks || []).length
                                color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; font.bold: true
                            }
                        }
                        Rectangle {
                            id: wifiPasswordCard
                            visible: root.wifiPasswordVisible
                            width: parent.width
                            height: visible ? ((!root.wifiIsKnown(root.wifiSelectedSsid) && !root.wifiIsOpen(root.wifiSelectedSsid)) ? 86 : 50) : 0
                            radius: 11
                            color: "#182731"; border.width: 1; border.color: "#31505d"
                            Column {
                                anchors.fill: parent; anchors.margins: 8; spacing: 5
                                Text { text: "Ligar a " + root.wifiSelectedSsid; color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true; elide: Text.ElideRight; width: parent.width }
                                Rectangle {
                                    visible: !root.wifiIsKnown(root.wifiSelectedSsid) && !root.wifiIsOpen(root.wifiSelectedSsid)
                                    width: parent.width; height: visible ? 30 : 0; radius: 5; color: "#0b1216"; border.width: wifiPasswordInput.activeFocus ? 1 : 0; border.color: root.cyan
                                    TextInput {
                                        id: wifiPasswordInput; anchors.fill: parent; anchors.leftMargin: 9; anchors.rightMargin: 9; verticalAlignment: TextInput.AlignVCenter
                                        text: root.wifiPassword; onTextChanged: root.wifiPassword = text; echoMode: TextInput.Password; passwordCharacter: "•"
                                        color: root.textMain; selectionColor: root.cyanDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize
                                        onAccepted: root.submitWifiPassword()
                                    }
                                    Text { anchors.left: parent.left; anchors.leftMargin: 9; anchors.verticalCenter: parent.verticalCenter; visible: !wifiPasswordInput.text.length; text: "Palavra-passe"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize }
                                }
                                Row {
                                    spacing: 14
                                    Text { text: "Cancelar"; color: cancelWifiMouse.containsMouse ? root.textMain : root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; BounceMouseArea { id: cancelWifiMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.cancelWifiPassword() } }
                                    Text { text: wifiCredentialProcess.running ? "A ligar…" : (root.wifiSelectedSsid === root.hostState.network_name ? "Já ligada" : "Ligar"); color: connectWifiMouse.containsMouse ? "#ffffff" : root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; font.bold: true; BounceMouseArea { id: connectWifiMouse; anchors.fill: parent; enabled: root.wifiSelectedSsid !== root.hostState.network_name; hoverEnabled: true; cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor; onClicked: root.submitWifiPassword() } }
                                }
                            }
                        }
                        Text { visible: root.wifiMessage.length > 0; width: parent.width; wrapMode: Text.Wrap; text: root.wifiMessage; color: root.wifiMessage.indexOf("Não") === 0 ? "#ff91a4" : root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize }
                        Repeater {
                            model: root.hostState.available_networks || []
                            Rectangle {
                                required property string modelData
                                visible: modelData !== root.hostState.network_name
                                      && (!root.wifiPasswordVisible || modelData !== root.wifiSelectedSsid)
                                width: parent ? parent.width : 300; height: visible ? 40 : 0; radius: 10
                                color: nearbyWifiMouse.containsMouse ? "#20323c" : "#182731"
                                border.width: nearbyWifiMouse.containsMouse ? 1 : 0; border.color: "#31505d"
                                Text {
                                    anchors.left: parent.left; anchors.leftMargin: 12; anchors.top: parent.top; anchors.topMargin: 6
                                    width: parent.width - 145; elide: Text.ElideRight
                                    text: modelData; color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize
                                }
                                Row {
                                    anchors.left: parent.left; anchors.leftMargin: 12; anchors.bottom: parent.bottom; anchors.bottomMargin: 5
                                    spacing: 6
                                    WifiSecurityIcon { open: root.wifiIsOpen(modelData); anchors.verticalCenter: parent.verticalCenter }
                                    Text {
                                        text: root.wifiSignalBars(root.wifiDetails(modelData).signal) + "  " + root.wifiDetails(modelData).signal + "%  ·  " + root.wifiSecurityLabel(modelData)
                                        color: root.textDim
                                        font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize; font.bold: true
                                    }
                                }
                                BounceMouseArea {
                                    id: nearbyWifiMouse
                                    anchors.fill: parent
                                    enabled: true
                                    hoverEnabled: true
                                    cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                                    onClicked: {
                                        root.cancelWifiPassword()
                                        root.wifiSelectionTap = true
                                        root.beginWifiConnect(modelData)
                                    }
                                }
                            }
                        }
                        Text {
                            visible: !(root.hostState.available_networks || []).length
                            text: "-- nenhuma rede encontrada --"
                            color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize
                        }
                    }

                    Rectangle {
                        visible: root.controlsBluetoothOpen
                        width: parent.width; height: visible ? 44 : 0; radius: 11
                        color: "#182731"
                        border.width: 1; border.color: "#31505d"
                        Rectangle {
                            anchors.left: parent.left; anchors.leftMargin: 8; anchors.verticalCenter: parent.verticalCenter
                            width: 62; height: 28; radius: 8
                            color: bluetoothHeaderMouse.containsMouse ? root.cyanDim : "#101920"
                            Text { anchors.centerIn: parent; z: 2; text: "‹ Voltar"; color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; font.bold: true }
                            BounceMouseArea { id: bluetoothHeaderMouse; anchors.fill: parent; z: 1; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.openControlSection("bluetooth") }
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter; anchors.verticalCenter: parent.verticalCenter
                            text: "Bluetooth"
                            color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true
                        }
                        Text {
                            anchors.right: parent.right; anchors.rightMargin: 11; anchors.verticalCenter: parent.verticalCenter
                            text: root.bluetoothPowerPhase === "turning-on" ? "A LIGAR…" : (root.bluetoothDisplayPowered() ? "LIGADO" : "DESLIGADO")
                            color: root.bluetoothDisplayPowered() ? root.cyan : root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize
                        }
                    }
                    Flickable {
                        visible: root.controlsBluetoothOpen
                        width: parent.width; height: visible ? 216 : 0
                        contentWidth: width; contentHeight: bluetoothContent.implicitHeight
                        clip: true; boundsBehavior: Flickable.StopAtBounds
                        ScrollBar.vertical: ScrollBar { policy: bluetoothContent.implicitHeight > 216 ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff }

                        Column {
                            id: bluetoothContent
                            width: parent.width - (implicitHeight > 216 ? 7 : 0); spacing: 5

                            Rectangle {
                                width: parent.width; height: 56; radius: 11
                                color: "#182731"; border.width: 1; border.color: "#31505d"
                                Text {
                                    anchors.left: parent.left; anchors.leftMargin: 14; anchors.top: parent.top; anchors.topMargin: 8
                                    text: root.bluetoothPowerPhase === "turning-on" ? "A ligar Bluetooth…" : (root.bluetoothDisplayPowered() ? "Bluetooth ativo" : "Bluetooth desligado")
                                    color: root.bluetoothDisplayPowered() ? root.textMain : root.textDim
                                    font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true
                                }
                                Text {
                                    anchors.left: parent.left; anchors.leftMargin: 14; anchors.bottom: parent.bottom; anchors.bottomMargin: 8
                                    text: root.bluetoothConnectedDevices().length + " ligado" + (root.bluetoothConnectedDevices().length === 1 ? "" : "s")
                                    color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize; font.bold: true
                                }
                                Rectangle {
                                    anchors.right: parent.right; anchors.rightMargin: 9; anchors.verticalCenter: parent.verticalCenter
                                    width: 84; height: 28; radius: 8
                                    color: bluetoothPowerMouse.containsMouse ? (root.bluetoothDisplayPowered() ? "#743541" : root.cyanDim) : "#18242b"
                                    border.width: root.bluetoothDisplayPowered() ? 0 : 1; border.color: root.cyanDim
                                    Text { anchors.centerIn: parent; text: root.bluetoothPowerPhase === "turning-on" ? "A ligar…" : (root.bluetoothDisplayPowered() ? "Desligar" : "Ligar"); color: root.bluetoothDisplayPowered() ? "#ffb0bd" : root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; font.bold: true }
                                    BounceMouseArea { id: bluetoothPowerMouse; anchors.fill: parent; enabled: !root.bluetoothPowerPhase.length; hoverEnabled: true; cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor; onClicked: root.toggleBluetoothPower() }
                                }
                            }

                            Rectangle {
                                visible: root.bluetoothDisplayPowered()
                                width: parent.width; height: visible ? 30 : 0; radius: 8
                                color: bluetoothScanMouse.containsMouse ? root.cyanDim : "#101920"
                                border.width: 1; border.color: root.cyanDim
                                Text { anchors.centerIn: parent; text: bluetoothScanProcess.running ? "A PROCURAR…" : "PROCURAR DISPOSITIVOS"; color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; font.bold: true }
                                BounceMouseArea { id: bluetoothScanMouse; anchors.fill: parent; enabled: !bluetoothScanProcess.running; hoverEnabled: true; cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor; onClicked: bluetoothScanProcess.running = true }
                            }

                            Rectangle {
                                visible: root.bluetoothPairSessionId.length > 0
                                width: parent.width
                                height: visible ? (root.bluetoothPairPhase === "needs-response" && root.bluetoothPairChallenge === "pin" ? 108 : 78) : 0
                                radius: 10; color: "#18343e"; border.width: 1; border.color: root.cyanDim
                                Column {
                                    anchors.fill: parent; anchors.margins: 9; spacing: 5
                                    Text { width: parent.width; elide: Text.ElideRight; text: "Emparelhar " + root.bluetoothPairName; color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true }
                                    Text {
                                        width: parent.width; wrapMode: Text.Wrap
                                        text: root.bluetoothPairPhase === "needs-response" && root.bluetoothPairChallenge === "confirm"
                                              ? "Confirma que o código " + (root.bluetoothPairPasskey || "------") + " coincide."
                                              : (root.bluetoothPairPhase === "needs-response" && root.bluetoothPairChallenge === "pin"
                                                 ? "Introduz o PIN apresentado pelo dispositivo."
                                                 : (root.bluetoothPairPhase === "waiting-device"
                                                    ? "Escreve no dispositivo o código " + (root.bluetoothPairPasskey || "------") + "."
                                                    : (root.bluetoothMessage || "A aguardar o dispositivo…")))
                                        color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize
                                    }
                                    Rectangle {
                                        visible: root.bluetoothPairPhase === "needs-response" && root.bluetoothPairChallenge === "pin"
                                        width: parent.width; height: visible ? 28 : 0; radius: 5; color: "#0b1216"; border.width: bluetoothPinInput.activeFocus ? 1 : 0; border.color: root.cyan
                                        TextInput {
                                            id: bluetoothPinInput; anchors.fill: parent; anchors.leftMargin: 9; anchors.rightMargin: 9; verticalAlignment: TextInput.AlignVCenter
                                            text: root.bluetoothPairPin; onTextChanged: root.bluetoothPairPin = text; echoMode: TextInput.Password; maximumLength: 16
                                            color: root.textMain; selectionColor: root.cyanDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize
                                            onAccepted: if (text.length) root.respondBluetoothPair(true, text)
                                        }
                                        Text { anchors.left: parent.left; anchors.leftMargin: 9; anchors.verticalCenter: parent.verticalCenter; visible: !bluetoothPinInput.text.length; text: "PIN"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize }
                                    }
                                    Row {
                                        spacing: 12
                                        Text { text: root.bluetoothPairPhase === "completed" || root.bluetoothPairPhase === "failed" ? "Fechar" : "Cancelar"; color: pairCancelMouse.containsMouse ? root.textMain : root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; BounceMouseArea { id: pairCancelMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.bluetoothPairPhase === "completed" || root.bluetoothPairPhase === "failed" ? root.dismissBluetoothPairing() : root.cancelBluetoothPairing() } }
                                        Text { visible: root.bluetoothPairPhase === "needs-response" && root.bluetoothPairChallenge === "confirm"; text: "Confirmar"; color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; font.bold: true; BounceMouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.respondBluetoothPair(true, "") } }
                                        Text { visible: root.bluetoothPairPhase === "needs-response" && root.bluetoothPairChallenge === "pin"; text: "Emparelhar"; color: root.bluetoothPairPin.length ? root.cyan : root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; font.bold: true; BounceMouseArea { anchors.fill: parent; enabled: root.bluetoothPairPin.length > 0; cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor; onClicked: root.respondBluetoothPair(true, root.bluetoothPairPin) } }
                                    }
                                }
                            }

                            Rectangle {
                                visible: root.bluetoothRemoveAddress.length > 0
                                width: parent.width; height: visible ? 58 : 0; radius: 10
                                color: "#2b2026"; border.width: 1; border.color: "#743541"
                                Text { anchors.left: parent.left; anchors.leftMargin: 10; anchors.top: parent.top; anchors.topMargin: 8; width: parent.width - 20; elide: Text.ElideRight; text: "Esquecer " + root.bluetoothRemoveName + "?"; color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; font.bold: true }
                                Row {
                                    anchors.left: parent.left; anchors.leftMargin: 10; anchors.bottom: parent.bottom; anchors.bottomMargin: 8; spacing: 14
                                    Text { text: "Cancelar"; color: removeCancelMouse.containsMouse ? root.textMain : root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize; BounceMouseArea { id: removeCancelMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: { root.bluetoothRemoveAddress = ""; root.bluetoothRemoveName = "" } } }
                                    Text { text: bluetoothRemoveProcess.running ? "A esquecer…" : "Confirmar"; color: "#ffb0bd"; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize; font.bold: true; BounceMouseArea { anchors.fill: parent; enabled: !bluetoothRemoveProcess.running; cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor; onClicked: root.confirmBluetoothRemove() } }
                                }
                            }

                            Text { visible: root.bluetoothMessage.length > 0 && root.bluetoothPairSessionId.length === 0; width: parent.width; wrapMode: Text.Wrap; text: root.bluetoothMessage; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize }

                            Item { width: parent.width; height: 18; Text { anchors.verticalCenter: parent.verticalCenter; text: "DISPOSITIVOS LIGADOS  ·  " + root.bluetoothConnectedDevices().length; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; font.bold: true } }
                            Repeater {
                                model: root.bluetoothConnectedDevices()
                                Rectangle {
                                    required property var modelData
                                    width: parent ? parent.width : 300; height: 36; radius: 10
                                    color: connectedBtMouse.containsMouse ? "#20434e" : "#18343e"; border.width: 1; border.color: root.cyanDim
                                    Rectangle { width: 8; height: 8; radius: 4; color: root.cyan; anchors.left: parent.left; anchors.leftMargin: 12; anchors.verticalCenter: parent.verticalCenter }
                                    Text { anchors.left: parent.left; anchors.leftMargin: 32; anchors.verticalCenter: parent.verticalCenter; width: parent.width - 130; elide: Text.ElideRight; text: modelData.name || modelData.address; color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true }
                                    Text { anchors.right: parent.right; anchors.rightMargin: 12; anchors.verticalCenter: parent.verticalCenter; text: "DESLIGAR"; color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize; font.bold: true }
                                    BounceMouseArea { id: connectedBtMouse; anchors.fill: parent; enabled: !root.bluetoothDevicePendingAddress.length; hoverEnabled: true; cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor; onClicked: root.bluetoothDeviceAction("bluetooth-disconnect", modelData) }
                                }
                            }
                            Text { visible: root.bluetoothConnectedDevices().length === 0; text: "-- nenhum dispositivo ligado --"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize }

                            Item { width: parent.width; height: 4 }
                            Item { width: parent.width; height: 18; Text { anchors.verticalCenter: parent.verticalCenter; text: "DISPOSITIVOS ANTERIORES  ·  " + root.bluetoothKnownDevices().length; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; font.bold: true } }
                            Repeater {
                                model: root.bluetoothKnownDevices()
                                Rectangle {
                                    required property var modelData
                                    width: parent ? parent.width : 300; height: 36; radius: 10; color: "#182731"; border.width: 1; border.color: "#31505d"
                                    Rectangle { width: 8; height: 8; radius: 4; color: "#405058"; anchors.left: parent.left; anchors.leftMargin: 12; anchors.verticalCenter: parent.verticalCenter }
                                    Text { anchors.left: parent.left; anchors.leftMargin: 32; anchors.verticalCenter: parent.verticalCenter; width: parent.width - 148; elide: Text.ElideRight; text: modelData.name || modelData.address; color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize }
                                    Row {
                                        anchors.right: parent.right; anchors.rightMargin: 8; anchors.verticalCenter: parent.verticalCenter; spacing: 4
                                        Rectangle {
                                            width: root.bluetoothDevicePendingAction === "bluetooth-connect" && root.bluetoothDevicePendingAddress === modelData.address ? 58 : 38
                                            height: 24; radius: 6; color: knownConnectMouse.containsMouse ? root.cyanDim : "#101920"
                                            Text {
                                                anchors.centerIn: parent
                                                text: root.bluetoothDevicePendingAction === "bluetooth-connect" && root.bluetoothDevicePendingAddress === modelData.address ? "A LIGAR…" : "LIGAR"
                                                color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize; font.bold: true
                                                SequentialAnimation on opacity {
                                                    running: root.bluetoothDevicePendingAction === "bluetooth-connect" && root.bluetoothDevicePendingAddress === modelData.address
                                                    loops: Animation.Infinite
                                                    NumberAnimation { to: 0.35; duration: 380 }
                                                    NumberAnimation { to: 1; duration: 380 }
                                                }
                                            }
                                            BounceMouseArea { id: knownConnectMouse; anchors.fill: parent; enabled: !root.bluetoothDevicePendingAddress.length; hoverEnabled: true; cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor; onClicked: root.bluetoothDeviceAction("bluetooth-connect", modelData) }
                                        }
                                        Rectangle { width: 52; height: 24; radius: 6; color: knownRemoveMouse.containsMouse ? "#59303a" : "#18242b"; Text { anchors.centerIn: parent; text: "ESQUECER"; color: "#ffb0bd"; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize; font.bold: true } BounceMouseArea { id: knownRemoveMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.beginBluetoothRemove(modelData) } }
                                    }
                                }
                            }
                            Text { visible: root.bluetoothKnownDevices().length === 0; text: "-- nenhum dispositivo anterior --"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize }

                            Item { width: parent.width; height: 4 }
                            Item { width: parent.width; height: 18; Text { anchors.verticalCenter: parent.verticalCenter; text: "DISPOSITIVOS DISPONÍVEIS  ·  " + root.bluetoothAvailableDevices().length; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; font.bold: true } }
                            Repeater {
                                model: root.bluetoothAvailableDevices()
                                Rectangle {
                                    required property var modelData
                                    width: parent ? parent.width : 300; height: 36; radius: 10; color: "#182731"; border.width: 1; border.color: "#31505d"
                                    Text { anchors.left: parent.left; anchors.leftMargin: 12; anchors.verticalCenter: parent.verticalCenter; width: parent.width - 104; elide: Text.ElideRight; text: modelData.name || modelData.address; color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize }
                                    Rectangle { anchors.right: parent.right; anchors.rightMargin: 8; anchors.verticalCenter: parent.verticalCenter; width: 78; height: 24; radius: 6; color: availablePairMouse.containsMouse ? root.cyanDim : "#101920"; Text { anchors.centerIn: parent; text: "EMPARELHAR"; color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize; font.bold: true } BounceMouseArea { id: availablePairMouse; anchors.fill: parent; enabled: !root.bluetoothPairSessionId.length; hoverEnabled: true; cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor; onClicked: root.beginBluetoothPair(modelData) } }
                                }
                            }
                            Text { visible: root.bluetoothAvailableDevices().length === 0; width: parent.width; wrapMode: Text.Wrap; text: root.hostState.bluetooth_powered ? (bluetoothScanProcess.running ? "-- a procurar dispositivos --" : "-- nenhum dispositivo disponível --") : "-- liga o Bluetooth para procurar dispositivos --"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize }
                        }
                    }

                    Row {
                        visible: root.controlsAllClosed() && !root.powerConfirmOpen
                        width: parent.width; height: visible ? 58 : 0; spacing: 6
                        Rectangle {
                            width: parent.width - 64; height: parent.height; radius: 11
                            color: volumeSummaryMouse.containsMouse ? "#20323c" : "#182731"; border.width: 1; border.color: "#31505d"
                            Rectangle {
                                id: volumeMuteSummaryButton
                                z: 3
                                anchors.left: parent.left; anchors.leftMargin: 11; anchors.top: parent.top; anchors.topMargin: 8
                                width: 26; height: 26; radius: 8; color: volumeMuteSummaryMouse.containsMouse ? root.cyanDim : (root.volumeMuted ? "#202d34" : "#173f49")
                                ControlIcon { anchors.centerIn: parent; width: 16; height: 16; source: root.volumeMuted ? "file:///usr/share/icons/Adwaita/symbolic/status/audio-volume-muted-symbolic.svg" : "file:///usr/share/icons/Adwaita/symbolic/status/audio-volume-high-symbolic.svg"; tint: root.volumeMuted ? root.textDim : root.cyan }
                                BounceMouseArea { id: volumeMuteSummaryMouse; anchors.fill: parent; enabled: !localActionProcess.running; hoverEnabled: true; cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor; onClicked: root.toggleVolumeMute() }
                            }
                            Text { anchors.left: parent.left; anchors.leftMargin: 47; anchors.top: parent.top; anchors.topMargin: 12; text: root.volumeMuted ? "Volume silenciado" : "Volume"; color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true }
                            Text { anchors.right: parent.right; anchors.rightMargin: 12; anchors.top: parent.top; anchors.topMargin: 12; text: root.volumeText; color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; font.bold: true }
                            Slider {
                                id: volumeSummarySlider
                                anchors.left: parent.left; anchors.leftMargin: 12; anchors.right: parent.right; anchors.rightMargin: 12
                                anchors.bottom: parent.bottom; anchors.bottomMargin: 3
                                height: 22; from: 0; to: 100; stepSize: 1; enabled: !localActionProcess.running
                                onPressedChanged: { if (!pressed) root.commitVolume(value) }
                                Binding { target: volumeSummarySlider; property: "value"; value: root.volumeValue; when: !volumeSummarySlider.pressed }
                                background: Rectangle {
                                    x: volumeSummarySlider.leftPadding; y: volumeSummarySlider.topPadding + volumeSummarySlider.availableHeight / 2 - height / 2
                                    width: volumeSummarySlider.availableWidth; height: 3; radius: 2; color: "#34454e"
                                    Rectangle { width: volumeSummarySlider.visualPosition * parent.width; height: parent.height; radius: 2; color: root.volumeMuted ? root.textDim : root.cyan }
                                }
                                handle: Rectangle {
                                    x: volumeSummarySlider.leftPadding + volumeSummarySlider.visualPosition * (volumeSummarySlider.availableWidth - width)
                                    y: volumeSummarySlider.topPadding + volumeSummarySlider.availableHeight / 2 - height / 2
                                    width: volumeSummarySlider.pressed ? 12 : 10; height: width; radius: width / 2; color: volumeSummarySlider.pressed ? "#ffffff" : root.cyan; border.width: 2; border.color: "#182731"
                                }
                            }
                            BounceMouseArea { id: volumeSummaryMouse; anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; z: 1; height: 36; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.openControlSection("audio") }
                        }
                        Rectangle {
                            width: 58; height: parent.height; radius: 11
                            color: microphoneSummaryMouse.containsMouse ? "#20323c" : "#182731"; border.width: 1; border.color: root.microphoneActive ? root.cyanDim : "#31505d"
                            Rectangle {
                                id: microphoneMuteSummaryButton
                                z: 3
                                anchors.horizontalCenter: parent.horizontalCenter; anchors.top: parent.top; anchors.topMargin: 7
                                width: 25; height: 25; radius: 7; color: microphoneMuteSummaryMouse.containsMouse ? root.cyanDim : (root.microphoneMuted ? "#202d34" : "#173f49")
                                ControlIcon { anchors.centerIn: parent; width: 16; height: 16; source: "file:///usr/share/icons/Adwaita/symbolic/devices/audio-input-microphone-symbolic.svg"; tint: root.microphoneMuted ? root.textDim : root.cyan }
                                BounceMouseArea { id: microphoneMuteSummaryMouse; anchors.fill: parent; enabled: !localActionProcess.running; hoverEnabled: true; cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor; onClicked: root.toggleMicrophoneMute() }
                            }
                            Text { anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom; anchors.bottomMargin: 8; text: "MIC " + root.microphoneText; color: root.microphoneMuted ? root.textDim : root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize; font.bold: true }
                            BounceMouseArea { id: microphoneSummaryMouse; anchors.fill: parent; z: 1; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.openControlSection("microphone") }
                        }
                    }
                    Row {
                        visible: root.controlsAllClosed() && !root.powerConfirmOpen
                        width: parent.width; height: visible ? 58 : 0; spacing: 6
                        Rectangle {
                            width: parent.width - 64; height: parent.height; radius: 11
                            color: "#182731"; border.width: 1; border.color: "#31505d"
                            Text {
                                anchors.left: parent.left; anchors.leftMargin: 12; anchors.top: parent.top; anchors.topMargin: 12
                                text: "Brilho do ecrã"; color: root.textMain; font.family: "Adwaita Mono"
                                font.pixelSize: root.menuBodySize; font.bold: true
                            }
                            Text {
                                anchors.right: parent.right; anchors.rightMargin: 12; anchors.top: parent.top; anchors.topMargin: 12
                                text: root.displayBrightness + "%"; color: root.cyan; font.family: "Adwaita Mono"
                                font.pixelSize: root.menuSmallSize; font.bold: true
                            }
                            Slider {
                                id: displayBrightnessSlider
                                anchors.left: parent.left; anchors.leftMargin: 12
                                anchors.right: parent.right; anchors.rightMargin: 12
                                anchors.bottom: parent.bottom; anchors.bottomMargin: 3
                                height: 22; from: 5; to: 100; stepSize: 1
                                onMoved: root.previewDisplayBrightness(value)
                                onPressedChanged: { if (!pressed) root.commitDisplayBrightness(value) }
                                Binding { target: displayBrightnessSlider; property: "value"; value: root.displayBrightness; when: !displayBrightnessSlider.pressed }
                                background: Rectangle {
                                    x: displayBrightnessSlider.leftPadding
                                    y: displayBrightnessSlider.topPadding + displayBrightnessSlider.availableHeight / 2 - height / 2
                                    width: displayBrightnessSlider.availableWidth; height: 3; radius: 2; color: "#34454e"
                                    Rectangle { width: displayBrightnessSlider.visualPosition * parent.width; height: parent.height; radius: 2; color: root.cyan }
                                }
                                handle: Rectangle {
                                    x: displayBrightnessSlider.leftPadding + displayBrightnessSlider.visualPosition * (displayBrightnessSlider.availableWidth - width)
                                    y: displayBrightnessSlider.topPadding + displayBrightnessSlider.availableHeight / 2 - height / 2
                                    width: displayBrightnessSlider.pressed ? 12 : 10; height: width; radius: width / 2
                                    color: displayBrightnessSlider.pressed ? "#ffffff" : root.cyan; border.width: 2; border.color: "#182731"
                                }
                            }
                        }
                        Rectangle {
                            width: 58; height: parent.height; radius: 11
                            color: keyboardBrightnessSummaryMouse.containsMouse ? "#20323c" : "#182731"
                            border.width: 1; border.color: root.keyboardBrightness > 0 ? root.cyanDim : "#31505d"
                            Rectangle {
                                id: keyboardBrightnessSummaryButton
                                anchors.horizontalCenter: parent.horizontalCenter; anchors.top: parent.top; anchors.topMargin: 7
                                width: 25; height: 25; radius: 7
                                color: root.keyboardBrightness === 0 ? "#202d34"
                                       : (root.keyboardBrightness < root.keyboardBrightnessMax ? "#173f49" : root.cyanDim)
                                border.width: root.keyboardBrightness >= root.keyboardBrightnessMax ? 1 : 0
                                border.color: root.cyan
                                ControlIcon {
                                    anchors.centerIn: parent; width: 16; height: 16
                                    source: "file:///usr/share/icons/Adwaita/symbolic/status/keyboard-brightness-symbolic.svg"
                                    tint: root.keyboardBrightness === 0 ? root.textDim
                                          : (root.keyboardBrightness < root.keyboardBrightnessMax ? root.cyan : "#ffffff")
                                }
                            }
                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom; anchors.bottomMargin: 8
                                text: root.keyboardBrightness === 0 ? "LUZ OFF" : (root.keyboardBrightness < root.keyboardBrightnessMax ? "LUZ MÉD" : "LUZ MAX")
                                color: root.keyboardBrightness === 0 ? root.textDim : root.textMain
                                font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize; font.bold: true
                            }
                            BounceMouseArea {
                                id: keyboardBrightnessSummaryMouse
                                anchors.fill: parent; enabled: !keyboardBrightnessProcess.running
                                hoverEnabled: true; cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                                onClicked: root.cycleKeyboardBrightness()
                            }
                        }
                    }
                    Text {
                        visible: root.isHub && root.controlsAllClosed() && root.hardwareControlError.length > 0
                        width: parent.width; text: root.hardwareControlError; color: "#ff91a4"
                        wrapMode: Text.WordWrap; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize
                    }
                    Rectangle {
                        visible: root.controlsAudioOpen
                        width: parent.width; height: visible ? 44 : 0; radius: 11
                        color: "#182731"
                        border.width: 1; border.color: "#31505d"
                        Rectangle {
                            anchors.left: parent.left; anchors.leftMargin: 8; anchors.verticalCenter: parent.verticalCenter
                            width: 62; height: 28; radius: 8
                            color: audioHeaderMouse.containsMouse ? root.cyanDim : "#101920"
                            Text { anchors.centerIn: parent; text: "‹ Voltar"; color: audioHeaderMouse.containsMouse ? "#ffffff" : root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; font.bold: true }
                            BounceMouseArea { id: audioHeaderMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.openControlSection("audio") }
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter; anchors.verticalCenter: parent.verticalCenter
                            text: "Volume"
                            color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true
                        }
                        Text {
                            anchors.right: parent.right; anchors.rightMargin: 11; anchors.verticalCenter: parent.verticalCenter
                            text: root.volumeText
                            color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize
                        }
                    }
                    Column {
                        width: parent.width; spacing: 5; visible: root.controlsAudioOpen

                        Rectangle {
                            width: parent.width; height: 68; radius: 11
                            color: "#182731"; border.width: 1; border.color: "#31505d"
                            Text {
                                anchors.left: parent.left; anchors.leftMargin: 16; anchors.top: parent.top; anchors.topMargin: 8
                                text: root.volumeMuted ? "Volume silenciado" : "Volume de saída"
                                color: root.volumeMuted ? root.textDim : root.textMain
                                font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true
                            }
                            Text {
                                anchors.right: parent.right; anchors.rightMargin: 12; anchors.top: parent.top; anchors.topMargin: 8
                                text: Math.round(volumeSlider.value) + "%"
                                color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true
                            }
                            Slider {
                                id: volumeSlider
                                anchors.left: parent.left; anchors.leftMargin: 16
                                anchors.right: parent.right; anchors.rightMargin: 14
                                anchors.bottom: parent.bottom; anchors.bottomMargin: 7
                                height: 28; from: 0; to: 100; stepSize: 1
                                activeFocusOnTab: true
                                enabled: !localActionProcess.running
                                onPressedChanged: {
                                    if (pressed)
                                        forceActiveFocus()
                                    else
                                        root.commitVolume(value)
                                }
                                Keys.onLeftPressed: (event) => {
                                    if (!localActionProcess.running) {
                                        value = Math.max(from, Math.round(value) - 5)
                                        root.commitVolume(value)
                                    }
                                    event.accepted = true
                                }
                                Keys.onRightPressed: (event) => {
                                    if (!localActionProcess.running) {
                                        value = Math.min(to, Math.round(value) + 5)
                                        root.commitVolume(value)
                                    }
                                    event.accepted = true
                                }
                                Binding { target: volumeSlider; property: "value"; value: root.volumeValue; when: !volumeSlider.pressed }
                                background: Rectangle {
                                    x: volumeSlider.leftPadding
                                    y: volumeSlider.topPadding + volumeSlider.availableHeight / 2 - height / 2
                                    width: volumeSlider.availableWidth; height: 5; radius: 3; color: "#26343a"
                                    Rectangle {
                                        width: volumeSlider.visualPosition * parent.width; height: parent.height; radius: 3
                                        color: root.volumeMuted ? root.textDim : root.cyan
                                    }
                                }
                                handle: Rectangle {
                                    x: volumeSlider.leftPadding + volumeSlider.visualPosition * (volumeSlider.availableWidth - width)
                                    y: volumeSlider.topPadding + volumeSlider.availableHeight / 2 - height / 2
                                    width: 16; height: 16; radius: 8
                                    color: volumeSlider.pressed ? "#ffffff" : root.cyan
                                    border.width: 2; border.color: "#13252c"
                                }
                            }
                        }

                        Row {
                            width: parent.width; height: 30; spacing: 4
                            MenuButton {
                                width: (parent.width - 6) / 2; height: parent.height; label: "AJUSTE −5%"
                                onActivated: root.localAction(["/usr/bin/wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "5%-"])
                            }
                            MenuButton {
                                width: (parent.width - 6) / 2; height: parent.height; label: "AJUSTE +5%"; accent: true
                                onActivated: root.localAction(["/usr/bin/wpctl", "set-volume", "-l", "1", "@DEFAULT_AUDIO_SINK@", "5%+"])
                            }
                        }
                        Rectangle {
                            width: parent.width; height: 30; radius: 7
                            color: volumeMuteMouse.containsMouse ? root.cyanDim : (root.volumeMuted ? "#1c3941" : "#101920")
                            border.width: root.volumeMuted ? 1 : 0; border.color: root.cyan
                            Text { anchors.centerIn: parent; text: root.volumeMuted ? "REATIVAR SOM" : "SILENCIAR"; color: root.volumeMuted ? root.cyan : root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: root.volumeMuted }
                            BounceMouseArea { id: volumeMuteMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.toggleVolumeMute() }
                        }
                    }

                    Rectangle {
                        visible: root.controlsMicrophoneOpen
                        width: parent.width; height: visible ? 44 : 0; radius: 11
                        color: "#182731"; border.width: 1; border.color: "#31505d"
                        Rectangle {
                            anchors.left: parent.left; anchors.leftMargin: 8; anchors.verticalCenter: parent.verticalCenter
                            width: 62; height: 28; radius: 8
                            color: microphoneHeaderMouse.containsMouse ? root.cyanDim : "#101920"
                            Text { anchors.centerIn: parent; text: "‹ Voltar"; color: microphoneHeaderMouse.containsMouse ? "#ffffff" : root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuSmallSize; font.bold: true }
                            BounceMouseArea { id: microphoneHeaderMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.openControlSection("microphone") }
                        }
                        Text { anchors.horizontalCenter: parent.horizontalCenter; anchors.verticalCenter: parent.verticalCenter; text: "Microfone"; color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true }
                        Text { anchors.right: parent.right; anchors.rightMargin: 11; anchors.verticalCenter: parent.verticalCenter; text: root.microphoneText; color: root.microphoneMuted ? root.textDim : root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize }
                    }
                    Column {
                        width: parent.width; spacing: 5; visible: root.controlsMicrophoneOpen
                        Rectangle {
                            width: parent.width; height: 68; radius: 11
                            color: "#182731"; border.width: 1; border.color: "#31505d"
                            Text { anchors.left: parent.left; anchors.leftMargin: 16; anchors.top: parent.top; anchors.topMargin: 8; text: root.microphoneMuted ? "Microfone silenciado" : "Volume de entrada"; color: root.microphoneMuted ? root.textDim : root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true }
                            Text { anchors.right: parent.right; anchors.rightMargin: 12; anchors.top: parent.top; anchors.topMargin: 8; text: Math.round(microphoneSlider.value) + "%"; color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true }
                            Slider {
                                id: microphoneSlider
                                anchors.left: parent.left; anchors.leftMargin: 16; anchors.right: parent.right; anchors.rightMargin: 14
                                anchors.bottom: parent.bottom; anchors.bottomMargin: 7
                                height: 28; from: 0; to: 100; stepSize: 1; activeFocusOnTab: true
                                enabled: !localActionProcess.running
                                onPressedChanged: { if (pressed) forceActiveFocus(); else root.commitMicrophoneVolume(value) }
                                Keys.onLeftPressed: (event) => { if (!localActionProcess.running) { value = Math.max(from, Math.round(value) - 5); root.commitMicrophoneVolume(value) } event.accepted = true }
                                Keys.onRightPressed: (event) => { if (!localActionProcess.running) { value = Math.min(to, Math.round(value) + 5); root.commitMicrophoneVolume(value) } event.accepted = true }
                                Binding { target: microphoneSlider; property: "value"; value: root.microphoneVolume; when: !microphoneSlider.pressed }
                                background: Rectangle {
                                    x: microphoneSlider.leftPadding; y: microphoneSlider.topPadding + microphoneSlider.availableHeight / 2 - height / 2
                                    width: microphoneSlider.availableWidth; height: 5; radius: 3; color: "#26343a"
                                    Rectangle { width: microphoneSlider.visualPosition * parent.width; height: parent.height; radius: 3; color: root.microphoneMuted ? root.textDim : root.cyan }
                                }
                                handle: Rectangle {
                                    x: microphoneSlider.leftPadding + microphoneSlider.visualPosition * (microphoneSlider.availableWidth - width)
                                    y: microphoneSlider.topPadding + microphoneSlider.availableHeight / 2 - height / 2
                                    width: 16; height: 16; radius: 8; color: microphoneSlider.pressed ? "#ffffff" : root.cyan; border.width: 2; border.color: "#13252c"
                                }
                            }
                        }
                        Row {
                            width: parent.width; height: 30; spacing: 4
                            MenuButton { width: (parent.width - 6) / 2; height: parent.height; label: "AJUSTE −5%"; onActivated: root.localAction(["/usr/bin/wpctl", "set-volume", "@DEFAULT_AUDIO_SOURCE@", "5%-"]) }
                            MenuButton { width: (parent.width - 6) / 2; height: parent.height; label: "AJUSTE +5%"; accent: true; onActivated: root.localAction(["/usr/bin/wpctl", "set-volume", "-l", "1", "@DEFAULT_AUDIO_SOURCE@", "5%+"]) }
                        }
                        Rectangle {
                            width: parent.width; height: 30; radius: 7
                            color: microphoneMuteMouse.containsMouse ? root.cyanDim : (root.microphoneMuted ? "#1c3941" : "#101920")
                            border.width: root.microphoneMuted ? 1 : 0; border.color: root.cyan
                            Text { anchors.centerIn: parent; text: root.microphoneMuted ? "REATIVAR MICROFONE" : "SILENCIAR MICROFONE"; color: root.microphoneMuted ? root.cyan : root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: root.microphoneMuted }
                            BounceMouseArea { id: microphoneMuteMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.toggleMicrophoneMute() }
                        }
                    }

                    Row {
                        visible: root.controlsAllClosed() && !root.powerConfirmOpen
                        width: parent.width
                        height: visible ? 40 : 0
                        spacing: 6
                        Rectangle {
                            width: parent.width; height: parent.height; radius: 10
                            color: terminalMouse.containsMouse ? "#203b46" : "#182731"
                            border.width: 1; border.color: "#31505d"
                            Rectangle {
                                anchors.left: parent.left; anchors.leftMargin: 8; anchors.verticalCenter: parent.verticalCenter
                                width: 25; height: 25; radius: 7; color: "#173f49"
                                ControlIcon { anchors.centerIn: parent; width: 16; height: 16; source: "file:///usr/share/icons/Adwaita/symbolic/legacy/utilities-terminal-symbolic.svg" }
                            }
                            Text { anchors.left: parent.left; anchors.leftMargin: 43; anchors.verticalCenter: parent.verticalCenter; text: root.isHub ? "Terminal do Host · sessão única" : "Gestor de ficheiros"; color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true }
                            Text { anchors.right: parent.right; anchors.rightMargin: 11; anchors.verticalCenter: parent.verticalCenter; text: root.isHub ? "SUPER+H" : "›"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize }
                            BounceMouseArea {
                                id: terminalMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                popup.visible = false
                                if (root.isHub) {
                                    if (!hostConsoleProcess.running) hostConsoleProcess.running = true
                                } else if (!environmentFilesProcess.running) environmentFilesProcess.running = true
                                }
                            }
                        }
                    }
                    Row {
                        visible: root.isHub && root.controlsAllClosed() && !root.powerConfirmOpen
                        width: parent.width
                        height: visible ? 40 : 0
                        spacing: 6
                        Rectangle {
                            width: parent.width; height: parent.height; radius: 10
                            color: environmentsControlMouse.containsMouse ? "#203b46" : "#182731"
                            border.width: 1; border.color: "#31505d"
                            Rectangle {
                                anchors.left: parent.left; anchors.leftMargin: 8; anchors.verticalCenter: parent.verticalCenter
                                width: 25; height: 25; radius: 7; color: "#173f49"
                                Text { anchors.centerIn: parent; text: "APX"; color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize; font.bold: true }
                            }
                            Text { anchors.left: parent.left; anchors.leftMargin: 43; anchors.verticalCenter: parent.verticalCenter; text: "Sair para o Host"; color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize; font.bold: true }
                            Text { anchors.right: parent.right; anchors.rightMargin: 11; anchors.verticalCenter: parent.verticalCenter; text: "SUPER+M"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize }
                            BounceMouseArea {
                                id: environmentsControlMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                onClicked: { popup.visible = false; if (!hostExitProcess.running) hostExitProcess.running = true }
                            }
                        }
                    }
                    Text {
                        visible: root.controlsAllClosed() && !root.powerConfirmOpen
                        width: parent.width; height: 18
                        text: "AÇÕES DA SESSÃO"
                        color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize; font.bold: true
                    }
                    Grid {
                        visible: root.controlsAllClosed() && !root.powerConfirmOpen
                        width: parent.width
                        height: visible ? 69 : 0
                        columns: 2
                        rowSpacing: 5
                        columnSpacing: 5
                        Rectangle {
                            width: (parent.width - 5) / 2; height: 32; radius: 8
                            color: updateMouse.containsMouse ? "#21404a" : "#182731"
                            ControlIcon { anchors.left: parent.left; anchors.leftMargin: 9; anchors.verticalCenter: parent.verticalCenter; width: 16; height: 16; source: "file:///usr/share/icons/Adwaita/symbolic/status/software-update-available-symbolic.svg" }
                            Text { anchors.left: parent.left; anchors.leftMargin: 29; anchors.verticalCenter: parent.verticalCenter; text: root.isHub ? "Update" : "Apps"; color: root.cyan; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize }
                            BounceMouseArea { id: updateMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: {
                                popup.visible = false
                                if (root.isHub) {
                                    if (!updateUiProcess.running) updateUiProcess.running = true
                                } else if (!environmentAppsProcess.running) environmentAppsProcess.running = true
                            } }
                        }
                        Rectangle {
                            width: (parent.width - 5) / 2; height: 32; radius: 8; color: lockMouse.containsMouse ? "#20323c" : "#182731"
                            ControlIcon { anchors.left: parent.left; anchors.leftMargin: 8; anchors.verticalCenter: parent.verticalCenter; width: 16; height: 16; source: "file:///usr/share/icons/Adwaita/symbolic/status/system-lock-screen-symbolic.svg"; tint: root.cyan }
                            Text { anchors.left: parent.left; anchors.leftMargin: 27; anchors.verticalCenter: parent.verticalCenter; text: "Bloquear"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize }
                            BounceMouseArea { id: lockMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: {
                                popup.visible = false
                                if (!lockProcess.running) lockProcess.running = true
                            } }
                        }
                        Rectangle {
                            width: (parent.width - 5) / 2; height: 32; radius: 8; color: rebootMouse.containsMouse ? "#20323c" : "#182731"
                            ControlIcon { anchors.left: parent.left; anchors.leftMargin: 6; anchors.verticalCenter: parent.verticalCenter; width: 16; height: 16; source: "file:///usr/share/icons/Adwaita/symbolic/actions/system-reboot-symbolic.svg"; tint: root.cyan }
                            Text { anchors.left: parent.left; anchors.leftMargin: 23; anchors.verticalCenter: parent.verticalCenter; text: root.isHub ? "Reiniciar" : "Ficheiros"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize }
                            BounceMouseArea {
                                id: rebootMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    if (root.isHub)
                                        root.beginPower("reboot")
                                    else
                                        environmentFilesProcess.running = true
                                }
                            }
                        }
                        Rectangle {
                            width: (parent.width - 5) / 2; height: 32; radius: 8; color: poweroffMouse.containsMouse ? "#422a31" : "#182731"
                            ControlIcon { anchors.left: parent.left; anchors.leftMargin: 6; anchors.verticalCenter: parent.verticalCenter; width: 16; height: 16; source: "file:///usr/share/icons/Adwaita/symbolic/actions/system-shutdown-symbolic.svg"; tint: "#ff9dab" }
                            Text { anchors.left: parent.left; anchors.leftMargin: 23; anchors.verticalCenter: parent.verticalCenter; text: root.isHub ? "Desligar" : "Voltar"; color: "#ff9dab"; font.family: "Adwaita Mono"; font.pixelSize: root.menuMetaSize }
                            BounceMouseArea {
                                id: poweroffMouse
                                anchors.fill: parent
                                enabled: root.isHub || (root.sessionKindReady && !root.environmentSwitchPending)
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    if (root.isHub)
                                        root.beginPower("poweroff")
                                    else
                                        root.returnToHub()
                                }
                            }
                        }
                    }
                    Rectangle {
                        visible: root.controlsAllClosed() && root.powerConfirmOpen
                        width: parent.width
                        height: visible ? 104 : 0
                        radius: 7
                        color: "#101920"
                        border.width: 1
                        border.color: root.powerToken.length ? "#ffb15a" : root.cyanDim
                        Column {
                            anchors.fill: parent
                            anchors.margins: 9
                            spacing: 8
                            Text {
                                width: parent.width
                                text: root.powerMessage
                                color: root.powerToken.length ? "#ffd09a" : root.textDim
                                font.family: "Adwaita Mono"
                                font.pixelSize: root.menuBodySize
                                font.bold: true
                                wrapMode: Text.Wrap
                            }
                            Row {
                                width: parent.width
                                spacing: 6
                                MenuButton {
                                    width: (parent.width - 6) / 2
                                    label: "CANCELAR"
                                    onActivated: root.cancelPower()
                                }
                                MenuButton {
                                    visible: root.powerToken.length > 0
                                    width: (parent.width - 6) / 2
                                    label: root.powerBusy ? "A PROCESSAR..." : "CONFIRMAR"
                                    accent: true
                                    onActivated: root.confirmPower()
                                }
                            }
                        }
                    }
                }

                    Column {
                    width: parent.width
                    spacing: 6
                    visible: root.popupKind === "wifi"
                    Text {
                        text: "STATUS :: " + (root.hostState.network_name || "disconnected")
                        color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize
                    }
                    MenuButton { label: "[ SCAN ] procurar redes"; onActivated: root.hostAction("wifi-scan") }
                    MenuButton {
                        visible: !!root.hostState.network_name
                        label: "[ DISCONNECT ] rede atual"
                        onActivated: root.hostAction("wifi-disconnect")
                    }
                    Text { text: "KNOWN NETWORKS"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize }
                    Repeater {
                        model: root.hostState.known_networks || []
                        MenuButton {
                            required property string modelData
                            visible: modelData !== root.hostState.network_name
                            label: "[ CONNECT ] " + modelData
                            onActivated: root.hostAction("wifi-connect", modelData)
                        }
                    }
                }

                    Column {
                    width: parent.width
                    spacing: 6
                    visible: root.popupKind === "bluetooth"
                    MenuButton {
                        label: root.hostState.bluetooth_powered ? "[ POWER ] desligar" : "[ POWER ] ligar"
                        accent: true
                        onActivated: root.hostAction("bluetooth-power", root.hostState.bluetooth_powered ? "off" : "on")
                    }
                    Text { text: "PAIRED DEVICES"; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize }
                    Repeater {
                        model: root.hostState.bluetooth_devices || []
                        MenuButton {
                            required property var modelData
                            label: "[ " + (modelData.connected ? "DISCONNECT" : "CONNECT") + " ] " + modelData.name
                            onActivated: root.hostAction(modelData.connected ? "bluetooth-disconnect" : "bluetooth-connect", modelData.address)
                        }
                    }
                    Text {
                        visible: !(root.hostState.bluetooth_devices || []).length
                        text: "-- nenhum dispositivo emparelhado --"
                        color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize
                    }
                }

                    Column {
                    width: parent.width
                    spacing: 6
                    visible: root.popupKind === "audio"
                    Text { text: "OUTPUT :: " + root.volumeText; color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: root.menuBodySize }
                    MenuButton { label: "[ + 5% ] aumentar volume"; accent: true; onActivated: root.localAction(["/usr/bin/wpctl", "set-volume", "-l", "1", "@DEFAULT_AUDIO_SINK@", "5%+"]) }
                    MenuButton { label: "[ - 5% ] diminuir volume"; onActivated: root.localAction(["/usr/bin/wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "5%-"]) }
                    MenuButton { label: "[ MUTE ] alternar som"; onActivated: root.localAction(["/usr/bin/wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"]) }
                }

                    Column {
                    width: parent.width
                    spacing: 6
                    visible: root.popupKind === "battery"
                    Text { text: "BATTERY :: " + root.batteryText; color: root.textMain; font.family: "Adwaita Mono"; font.pixelSize: 14 }
                    Rectangle { width: parent.width; height: 8; radius: 4; color: "#26343a"
                        Rectangle { height: parent.height; radius: 4; color: root.cyan; width: parent.width * Math.max(0, Math.min(100, parseInt(root.batteryText) || 0)) / 100 }
                    }
                    Text {
                        visible: root.isHub
                        text: "MODO DE ENERGIA :: " + root.platformLabel(root.hardwareProfile.platform_profile)
                        color: root.textDim; font.family: "Adwaita Mono"; font.pixelSize: 11
                    }
                    Row {
                        visible: root.isHub
                        width: parent.width; height: 34; spacing: 6
                        MenuButton {
                            width: (parent.width - 12) / 3; label: "SILENCIOSO"
                            accent: root.hardwareProfile.platform_profile === "low-power"
                            enabled: !root.hardwareBusy
                            onActivated: root.setPlatformProfile("low-power")
                        }
                        MenuButton {
                            width: (parent.width - 12) / 3; label: "NORMAL"
                            accent: root.hardwareProfile.platform_profile === "balanced"
                            enabled: !root.hardwareBusy
                            onActivated: root.setPlatformProfile("balanced")
                        }
                        MenuButton {
                            width: (parent.width - 12) / 3; label: "PERFORMANCE"
                            accent: root.hardwareProfile.platform_profile === "performance"
                            enabled: !root.hardwareBusy
                            onActivated: root.setPlatformProfile("performance")
                        }
                    }
                    Text {
                        visible: root.isHub
                        text: "GPU :: " + root.gpuLabel(root.hardwareProfile.gpu_profile)
                              + (root.hardwareProfile.reboot_required
                                 ? "  →  " + root.gpuLabel(root.hardwareProfile.requested_gpu_profile) + " (REINÍCIO)" : "")
                        color: root.hardwareProfile.reboot_required ? "#ffd09a" : root.cyan
                        font.family: "Adwaita Mono"; font.pixelSize: 12
                    }
                    Column {
                        width: parent.width; spacing: 6
                        visible: root.isHub && !root.hardwareConfirmOpen
                        MenuButton {
                            label: "[ HÍBRIDO ] AMD + NVIDIA sob pedido"
                            accent: root.hardwareProfile.requested_gpu_profile === "hybrid"
                            enabled: !root.hardwareBusy
                            onActivated: root.beginGpuProfile("hybrid")
                        }
                        MenuButton {
                            label: "[ NVIDIA ] dedicada · máximo desempenho"
                            accent: root.hardwareProfile.requested_gpu_profile === "nvidia"
                            enabled: !root.hardwareBusy
                            onActivated: root.beginGpuProfile("nvidia")
                        }
                    }
                    Rectangle {
                        visible: root.isHub && root.hardwareConfirmOpen
                        width: parent.width; height: visible ? 126 : 0; radius: 7
                        color: "#101920"; border.width: 1
                        border.color: root.hardwareApplied ? root.cyan : "#ffb15a"
                        Column {
                            anchors.fill: parent; anchors.margins: 9; spacing: 8
                            Text {
                                width: parent.width; text: root.hardwareMessage
                                color: root.hardwareApplied ? root.cyan : "#ffd09a"
                                font.family: "Adwaita Mono"; font.pixelSize: 10; font.bold: true
                                wrapMode: Text.Wrap
                            }
                            Row {
                                width: parent.width; spacing: 6
                                MenuButton {
                                    width: (parent.width - 6) / 2
                                    label: root.hardwareApplied ? "MAIS TARDE" : "CANCELAR"
                                    onActivated: root.cancelGpuProfile()
                                }
                                MenuButton {
                                    width: (parent.width - 6) / 2
                                    visible: root.hardwareApplied || root.hardwareToken.length > 0
                                    label: root.hardwareApplied ? "REINICIAR AGORA" : (root.hardwareBusy ? "A PROCESSAR..." : "CONFIRMAR")
                                    accent: true
                                    onActivated: root.hardwareApplied ? root.rebootForGpuProfile() : root.confirmGpuProfile()
                                }
                            }
                        }
                    }
                    Text {
                        visible: root.hardwareMessage.length > 0 && !root.hardwareConfirmOpen
                        text: root.hardwareMessage; color: root.textDim; wrapMode: Text.WordWrap
                        width: parent.width; font.family: "Adwaita Mono"; font.pixelSize: 10
                    }
                    Text {
                        text: "Este Legion expõe dois modos físicos: Híbrido (AMD + NVIDIA sob pedido) e NVIDIA dedicada. A mudança de GPU requer reinício."
                        color: root.textDim; wrapMode: Text.WordWrap; width: parent.width
                        font.family: "Adwaita Mono"; font.pixelSize: 9
                    }
                    }
                }
            }
        }
    }

    HyprlandFocusGrab {
        id: popupFocusGrab
        windows: [bar, popup]
        active: popup.visible
        onCleared: if (popup.visible) root.closePopup()
    }
}
