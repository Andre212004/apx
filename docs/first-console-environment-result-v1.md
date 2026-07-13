# First APX Console Environment Result v1

Status: passed on 2026-07-13.

## Plain-language result

APX successfully started a separate, temporary Arch system on the existing Arch
computer. This was not a second host installation. It used the host kernel but
had its own filesystem and package database. It could not see the Development
Environment home, had no external network, and was deleted after a clean stop.

## Proven outcomes

- systemd ran as PID 1 inside the Environment;
- PID, mount, user, and network namespaces differed from the observer;
- exactly 138 packages were visible in the Environment's own pacman database;
- the host Development home was absent;
- systemd reported the system `running`;
- multi-user and user-session units were active;
- no systemd unit had failed and no job remained pending;
- shutdown returned code 0;
- no matching process or mount remained;
- the temporary runtime copy was removed;
- the verified source root remained unchanged.

V9 boot report digest:
`f129d383b0b6c4cc8a80882a46a7237c16becb76693a1af97b2f20ea11b44432`.

Final assessment digest:
`de0266fa91884d05c84887a4a91740e52db82c3067d5fc454337f3509c6998b6`.

## Practical consequence

The minimal lifecycle foundation is now real rather than architectural only.
The next product proof adds a versioned Hyprland graphical role and validates
display, GPU, input, audio, portals, user session handoff, and complete cleanup.
Only after that proof should the Hub's Environment button control the real
lifecycle backend.

No graphical packages, host display configuration, login manager, Btrfs
resource, persistent service, or real host account is authorized by this result.
