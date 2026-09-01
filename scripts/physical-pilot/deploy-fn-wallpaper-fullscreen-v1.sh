#!/usr/bin/env bash
set -Eeuo pipefail

# Publish the semantic-only Fn route, common rotating landscape background,
# text-only control centre and role-aware fullscreen/file-manager shortcuts.

readonly repository=/root/apx-host-development-mode-v1/apx
readonly keyboard=/usr/lib/apx/apx-legion-brightness-keys-v1.py
readonly runtime=/usr/lib/apx/apx-lab-runtime.py
readonly seed=/usr/share/apx/config-seeds/environment-shell-v1
readonly hub_root=/var/lib/apx/environments/hub/root
readonly backup="/var/lib/apx/backups/$(date -u +%Y%m%dT%H%M%SZ)-fn-wallpaper-fullscreen-v1"
readonly -a environments=(hub hytale steam minecraft faculdade)
readonly -a shell_files=(hypr/hyprland.lua hyprland/hyprland.conf quickshell/apx/shell.qml)
readonly -a wallpapers=(alpine-lake.png atlantic-coast.png rainforest-stream.png)

fail() { echo "APX Fn/wallpaper deployment refused: $*" >&2; exit 2; }
[[ $EUID -eq 0 && $PWD == "$repository" ]] || fail 'root or repository differs'
[[ $(</etc/hostname) == apx-host && $(</sys/class/dmi/id/product_name) == 82JU ]] \
    || fail 'Host identity differs'
[[ $(/usr/bin/machinectl show apx-hub -p State --value) == running ]] || fail 'Hub is not running'
[[ ! -e $backup ]] || fail 'backup already exists'

for relative in "${shell_files[@]}"; do
    [[ -f $repository/config/environment-shell-v1/$relative \
       && ! -L $repository/config/environment-shell-v1/$relative ]] || fail "source differs: $relative"
    [[ -f $seed/$relative && ! -L $seed/$relative ]] || fail "seed differs: $relative"
done
for image in "${wallpapers[@]}"; do
    [[ -f $repository/config/environment-shell-v1/apx/wallpapers/$image \
       && ! -L $repository/config/environment-shell-v1/apx/wallpapers/$image ]] \
        || fail "wallpaper source differs: $image"
    [[ ! -e $seed/apx/wallpapers/$image ]] || fail "wallpaper seed already exists: $image"
done
[[ -f $keyboard && ! -L $keyboard && -f $runtime && ! -L $runtime ]] \
    || fail 'installed bridge/runtime differs'
[[ -f $repository/scripts/physical-pilot/apx-legion-brightness-keys-v1.py \
   && -f $repository/scripts/virtual-lab/apx-lab-runtime.py ]] || fail 'bridge/runtime source differs'

for environment in "${environments[@]}"; do
    home=/var/lib/apx/environments/$environment/home/apx
    registration=/var/lib/apx/environments/$environment/registration.json
    [[ -d $home && ! -L $home && -f $registration && ! -L $registration ]] \
        || fail "Environment differs: $environment"
    /usr/bin/python3 - "$registration" "$environment" <<'PY'
import json, sys
value = json.load(open(sys.argv[1], encoding="utf-8"))
expected_role = "hub" if sys.argv[2] == "hub" else "graphical-base"
assert value.get("name") == sys.argv[2] and value.get("role") == expected_role
PY
    for relative in "${shell_files[@]}"; do
        [[ -f $home/.config/$relative && ! -L $home/.config/$relative ]] \
            || fail "Environment shell differs: $environment/$relative"
    done
    [[ ! -e $home/.config/apx/wallpapers ]] || fail "Environment wallpaper directory already exists: $environment"
done

readonly thunar_package="$hub_root/var/cache/pacman/pkg/thunar-4.20.9-1-x86_64.pkg.tar.zst"
[[ -f $thunar_package && ! -L $thunar_package ]] || fail 'exact Hub Thunar recovery package is absent'
/usr/bin/systemd-run -M apx-hub --pipe --wait --quiet /usr/bin/pacman -Qq thunar >/dev/null 2>&1 \
    || fail 'Thunar is not installed in the Hub as expected'
! /usr/bin/systemd-run -M apx-hub --uid=apx --pipe --wait --quiet \
    /usr/bin/pgrep -x thunar >/dev/null 2>&1 \
    || fail 'Thunar is currently running in the Hub'

/usr/bin/python3 -m py_compile \
    "$repository/scripts/physical-pilot/apx-legion-brightness-keys-v1.py" \
    "$repository/scripts/virtual-lab/apx-lab-runtime.py"
/usr/bin/python3 -m unittest tests.test_apx_legion_hardware_profiles \
    tests.test_apx_work_defaults tests.test_apx_environment_switch_v1 \
    tests.test_apx_lab_runtime_desktop_seed tests.test_apx_control_center_scale >/dev/null

/usr/bin/install -d -o root -g root -m 0700 "$backup/shared" "$backup/environments"
/usr/bin/cp --archive -- "$keyboard" "$backup/shared/keyboard.previous"
/usr/bin/cp --archive -- "$runtime" "$backup/shared/runtime.previous"
/usr/bin/cp --archive -- "$thunar_package" "$backup/shared/"
for relative in "${shell_files[@]}"; do
    target=$backup/shared/seed/$relative.previous
    /usr/bin/install -d -o root -g root -m 0700 "$(dirname "$target")"
    /usr/bin/cp --archive -- "$seed/$relative" "$target"
done
for environment in "${environments[@]}"; do
    home=/var/lib/apx/environments/$environment/home/apx
    for relative in "${shell_files[@]}"; do
        target=$backup/environments/$environment/$relative.previous
        /usr/bin/install -d -o root -g root -m 0700 "$(dirname "$target")"
        /usr/bin/cp --archive -- "$home/.config/$relative" "$target"
    done
done

reload_hyprland() {
    /usr/bin/systemd-run -M apx-hub --uid=apx --pipe --wait --quiet /usr/bin/bash -lc '
        export XDG_RUNTIME_DIR=/run/apx/session-1000
        for socket in "$XDG_RUNTIME_DIR"/hypr/*/.socket.sock; do
            test -S "$socket" || continue
            export HYPRLAND_INSTANCE_SIGNATURE=$(basename "$(dirname "$socket")")
            exec /usr/bin/hyprctl reload
        done
        exit 1
    ' >/dev/null 2>&1
}

restart_shell_and_bridge() {
    /usr/bin/systemd-run -M apx-hub --uid=apx --pipe --wait --quiet /usr/bin/bash -lc \
        "/usr/bin/pkill -f '^python3 /usr/lib/apx/apx-legion-brightness-keys-v1.py$' || true" \
        >/dev/null 2>&1
    /usr/bin/systemd-run -M apx-hub --uid=apx --pipe --wait --quiet \
        /usr/bin/pkill -x quickshell >/dev/null 2>&1 || true
}

thunar_removed=no
rollback() {
    local status=$?
    trap - ERR
    set +e
    /usr/bin/cp --archive -- "$backup/shared/keyboard.previous" "$keyboard"
    /usr/bin/cp --archive -- "$backup/shared/runtime.previous" "$runtime"
    for relative in "${shell_files[@]}"; do
        /usr/bin/cp --archive -- "$backup/shared/seed/$relative.previous" "$seed/$relative"
    done
    /usr/bin/rm -rf -- "$seed/apx/wallpapers"
    for environment in "${environments[@]}"; do
        home=/var/lib/apx/environments/$environment/home/apx
        for relative in "${shell_files[@]}"; do
            /usr/bin/cp --archive -- "$backup/environments/$environment/$relative.previous" "$home/.config/$relative"
        done
        /usr/bin/rm -rf -- "$home/.config/apx/wallpapers"
    done
    if [[ $thunar_removed == yes ]]; then
        /usr/bin/systemd-run -M apx-hub --pipe --wait --quiet \
            /usr/bin/pacman -U --noconfirm \
            "/var/cache/pacman/pkg/$(basename "$thunar_package")" >/dev/null 2>&1
    fi
    reload_hyprland
    restart_shell_and_bridge
    echo 'APX Fn/wallpaper deployment rolled back' >&2
    exit "$status"
}
trap rollback ERR

# Preserve inodes for files bind-mounted into the active Hub.
/usr/bin/cp -- "$repository/scripts/physical-pilot/apx-legion-brightness-keys-v1.py" "$keyboard"
/usr/bin/cp -- "$repository/scripts/virtual-lab/apx-lab-runtime.py" "$runtime"
/usr/bin/chown root:root "$keyboard" "$runtime"
/usr/bin/chmod 0755 "$keyboard" "$runtime"

for relative in "${shell_files[@]}"; do
    /usr/bin/cp -- "$repository/config/environment-shell-v1/$relative" "$seed/$relative"
    /usr/bin/chown root:root "$seed/$relative"
    /usr/bin/chmod 0644 "$seed/$relative"
done
/usr/bin/install -d -o root -g root -m 0755 "$seed/apx/wallpapers"
for image in "${wallpapers[@]}"; do
    /usr/bin/install -o root -g root -m 0644 \
        "$repository/config/environment-shell-v1/apx/wallpapers/$image" \
        "$seed/apx/wallpapers/$image"
done

for environment in "${environments[@]}"; do
    home=/var/lib/apx/environments/$environment/home/apx
    for relative in "${shell_files[@]}"; do
        /usr/bin/cp -- "$repository/config/environment-shell-v1/$relative" "$home/.config/$relative"
        /usr/bin/chown 1000:1000 "$home/.config/$relative"
        /usr/bin/chmod 0600 "$home/.config/$relative"
    done
    /usr/bin/install -d -o 1000 -g 1000 -m 0700 "$home/.config/apx/wallpapers"
    for image in "${wallpapers[@]}"; do
        /usr/bin/install -o 1000 -g 1000 -m 0600 \
            "$repository/config/environment-shell-v1/apx/wallpapers/$image" \
            "$home/.config/apx/wallpapers/$image"
    done
done

reload_hyprland
restart_shell_and_bridge

ready=no
for _ in {1..100}; do
    if /usr/bin/systemd-run -M apx-hub --uid=apx --pipe --wait --quiet /usr/bin/bash -lc '
        export XDG_RUNTIME_DIR=/run/apx/session-1000
        test "$(pgrep -x quickshell | wc -l)" -eq 1
        test "$(pgrep -f "^python3 /usr/lib/apx/apx-legion-brightness-keys-v1.py$" | wc -l)" -eq 1
        for socket in "$XDG_RUNTIME_DIR"/hypr/*/.socket.sock; do
            test -S "$socket" || continue
            export HYPRLAND_INSTANCE_SIGNATURE=$(basename "$(dirname "$socket")")
            hyprctl layers | grep -A2 "Layer level 0 (background)" | grep -q "namespace: quickshell"
            exit
        done
        exit 1
    ' >/dev/null 2>&1; then
        ready=yes
        break
    fi
    /usr/bin/sleep 0.1
done
if [[ $ready != yes ]]; then
    echo 'APX Fn/wallpaper deployment failed: updated QuickShell/Fn bridge did not become ready' >&2
    false
fi

/usr/bin/systemd-run -M apx-hub --pipe --wait --quiet \
    /usr/bin/pacman -R --noconfirm thunar >/dev/null
thunar_removed=yes
if /usr/bin/systemd-run -M apx-hub --uid=apx --pipe --wait --quiet \
        /usr/bin/bash -lc 'command -v thunar' >/dev/null 2>&1; then
    echo 'APX Fn/wallpaper deployment failed: Thunar remains available in the Hub' >&2
    false
fi
for environment in hytale steam minecraft faculdade; do
    if [[ ! -x /var/lib/apx/environments/$environment/root/usr/bin/thunar ]]; then
        echo "APX Fn/wallpaper deployment failed: workload file manager is absent: $environment" >&2
        false
    fi
done

for relative in "${shell_files[@]}"; do
    /usr/bin/cmp -- "$repository/config/environment-shell-v1/$relative" "$seed/$relative"
done
for image in "${wallpapers[@]}"; do
    /usr/bin/cmp -- "$repository/config/environment-shell-v1/apx/wallpapers/$image" \
        "$seed/apx/wallpapers/$image"
done
for environment in "${environments[@]}"; do
    home=/var/lib/apx/environments/$environment/home/apx
    for relative in "${shell_files[@]}"; do
        /usr/bin/cmp -- "$repository/config/environment-shell-v1/$relative" "$home/.config/$relative"
    done
    for image in "${wallpapers[@]}"; do
        /usr/bin/cmp -- "$repository/config/environment-shell-v1/apx/wallpapers/$image" \
            "$home/.config/apx/wallpapers/$image"
    done
done
/usr/bin/cmp -- "$repository/scripts/physical-pilot/apx-legion-brightness-keys-v1.py" "$keyboard"
/usr/bin/cmp -- "$repository/scripts/virtual-lab/apx-lab-runtime.py" "$runtime"

/usr/bin/chown -R root:root "$backup"
/usr/bin/find "$backup" -type f -exec chmod 0600 {} +
trap - ERR
echo "APX semantic Fn, rotating wallpapers, fullscreen and text controls active; Hub Thunar removed; backup: $backup"
