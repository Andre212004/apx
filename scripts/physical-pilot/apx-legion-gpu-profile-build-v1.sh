#!/usr/bin/bash
set -euo pipefail

readonly source_dir=/usr/src/apx-legion-gpu-profile-v1
readonly signing_key=/etc/kernel/secure-boot-private-key.pem
readonly signing_certificate=/etc/kernel/secure-boot-certificate.pem

[[ $(id -u) == 0 ]]
[[ -f $source_dir/apx-legion-gpu-profile-v1.c ]]
[[ -f $source_dir/Makefile ]]
[[ -r $signing_key && -r $signing_certificate ]]

while IFS= read -r build_dir; do
    kernel_release=${build_dir#/usr/lib/modules/}
    kernel_release=${kernel_release%/build}
    [[ $kernel_release =~ ^[A-Za-z0-9._+-]+$ ]]
    /usr/bin/make -C "$build_dir" M="$source_dir" clean
    /usr/bin/make -C "$build_dir" M="$source_dir" modules
    "$build_dir/scripts/sign-file" sha256 "$signing_key" "$signing_certificate" \
        "$source_dir/apx-legion-gpu-profile-v1.ko"
    /usr/bin/install -D -m 0644 "$source_dir/apx-legion-gpu-profile-v1.ko" \
        "/usr/lib/modules/$kernel_release/extra/apx-legion-gpu-profile-v1.ko"
    /usr/bin/depmod "$kernel_release"
done < <(/usr/bin/find /usr/lib/modules -mindepth 2 -maxdepth 2 -type d -name build -print | /usr/bin/sort)
