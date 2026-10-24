#!/bin/bash
# Installs the pinned provers on Ubuntu 24.04 x86_64 (local machine, cloud sandbox or CI).
#   CBMC 6.4.1 (github release .deb)
#   Frama-C 33 + Why3 + Z3 + CVC5 (Nix binary cache; Ubuntu's frama-c has no WP plugin)
#   z3-solver (pip) for the bit-lemma checker
# Usage: bash tools/install.sh   (uses sudo for dpkg/apt when not root)
set -eux
SUDO=$([ "$(id -u)" -eq 0 ] || echo sudo)
CBMC_VER=6.4.1
if ! command -v cbmc >/dev/null || ! cbmc --version | grep -q "$CBMC_VER"; then
  tmp=$(mktemp -d)
  curl -fsSL -o "$tmp/cbmc.deb" \
    "https://github.com/diffblue/cbmc/releases/download/cbmc-$CBMC_VER/ubuntu-24.04-cbmc-$CBMC_VER-Linux.deb"
  # apt resolves the .deb's dependencies itself (dpkg -i alone fails in a bare container).
  $SUDO env DEBIAN_FRONTEND=noninteractive apt-get update -qq
  $SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y "$tmp/cbmc.deb"
fi
if ! command -v nix >/dev/null && [ ! -x /nix/var/nix/profiles/default/bin/nix ]; then
  curl -fsSL -o /tmp/nix-install.sh https://nixos.org/nix/install
  # The installer wants sudo to create /nix; do it ourselves (root in a container).
  [ -d /nix ] || $SUDO sh -c 'mkdir -m 0755 /nix && chown "$(id -un)" /nix' 2>/dev/null || \
    { [ -z "$SUDO" ] && mkdir -m 0755 /nix; }
  # Single-user install as root (CI container): no build users, no sandbox.
  if [ "$(id -u)" -eq 0 ]; then
    mkdir -p /etc/nix && printf 'build-users-group =\nsandbox = false\n' > /etc/nix/nix.conf
  fi
  sh /tmp/nix-install.sh --no-daemon --yes 2>&1 | grep -v "^ *[0-9]*  *[0-9.]*[kMG]* *[0-9]* " || true
  [ -x "$HOME/.nix-profile/bin/nix" ] || [ -x /nix/var/nix/profiles/default/bin/nix ] || { echo "nix install failed"; exit 1; }
fi
export PATH="/nix/var/nix/profiles/default/bin:$HOME/.nix-profile/bin:$PATH"
# Pinned nixpkgs snapshot (the one the published proofs were run with).
NIXPKGS='https://releases.nixos.org/nixpkgs/nixpkgs-26.11pre1097770.5adc50831c25/nixexprs.tar.zst?narHash=sha256-hVMDyAXU0kxRuG3GygbZkzf5x%2BaBNEC0NYEJ6KwHtD4%3D'
nix --extra-experimental-features 'nix-command flakes' profile install \
  "tarball+$NIXPKGS#framac" "tarball+$NIXPKGS#z3" "tarball+$NIXPKGS#cvc5" "tarball+$NIXPKGS#why3"
why3 config detect >/dev/null
python3 -c "import z3" 2>/dev/null || pip install --quiet z3-solver==5.3.1.0 || pip install --quiet --break-system-packages z3-solver==5.3.1.0
echo "Installed. Add to PATH: $HOME/.nix-profile/bin"
cbmc --version; frama-c -version
