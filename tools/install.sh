#!/bin/bash
# Installs the pinned provers on Ubuntu 24.04 x86_64 (local machine, cloud sandbox or CI).
#   CBMC 6.4.1 (github release .deb)
#   Frama-C 33 + Why3 + Z3 + CVC5 (Nix binary cache; Ubuntu's frama-c has no WP plugin)
#   z3-solver (pip) for the bit-lemma checker
# Usage: bash tools/install.sh   (uses sudo for dpkg/apt when not root)
set -eu
SUDO=$([ "$(id -u)" -eq 0 ] || echo sudo)
CBMC_VER=6.4.1
if ! command -v cbmc >/dev/null || ! cbmc --version | grep -q "$CBMC_VER"; then
  tmp=$(mktemp -d)
  curl -fsSL -o "$tmp/cbmc.deb" \
    "https://github.com/diffblue/cbmc/releases/download/cbmc-$CBMC_VER/ubuntu-24.04-cbmc-$CBMC_VER-Linux.deb"
  $SUDO dpkg -i "$tmp/cbmc.deb" || ($SUDO apt-get update -qq && $SUDO apt-get -f install -y -qq)
fi
if ! command -v nix >/dev/null && [ ! -x /nix/var/nix/profiles/default/bin/nix ]; then
  curl -fsSL https://nixos.org/nix/install | sh -s -- --no-daemon --yes
fi
export PATH="/nix/var/nix/profiles/default/bin:$HOME/.nix-profile/bin:$PATH"
nix --extra-experimental-features 'nix-command flakes' profile install \
  nixpkgs#framac nixpkgs#z3 nixpkgs#cvc5 nixpkgs#why3
why3 config detect >/dev/null
python3 -c "import z3" 2>/dev/null || pip install --quiet z3-solver || pip install --quiet --break-system-packages z3-solver
echo "Installed. Add to PATH: $HOME/.nix-profile/bin"
cbmc --version; frama-c -version
