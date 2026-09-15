#!/usr/bin/env bash
# Betteragy Installer for macOS and Linux
# Usage: curl -fsSL https://raw.githubusercontent.com/mncuchiinhuttt/betteragy/master/install.sh | bash

set -euo pipefail

REPO_URL="https://github.com/mncuchiinhuttt/betteragy.git"
INSTALL_DIR="$HOME/.betteragy"
BIN_DIR="$HOME/.local/bin"

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

printf "${CYAN}"
cat << 'EOF'
   __         __   __                          
  / /  ___   / /_ / /_ ___  ____ ___ _ ___ _ __ __
 / _ \/ -_) / __// __// -_)/ __// _ `// _ `// // /
/_.__/\__/  \__/ \__/ \__//_/   \_,_/ \_, / \_, / 
                                     /___/ /___/  
EOF
printf "${NC}\n"
printf "${GREEN}==>${NC} Installing Betteragy v1.0.0...\n\n"

# 1. Check for modern tool managers (uv, pipx)
if command -v uv >/dev/null 2>&1; then
    printf "${GREEN}[+]${NC} Detected ${CYAN}uv${NC}. Installing via uv tool...\n"
    uv tool install "git+${REPO_URL}" --force
elif command -v pipx >/dev/null 2>&1; then
    printf "${GREEN}[+]${NC} Detected ${CYAN}pipx${NC}. Installing via pipx...\n"
    pipx install "git+${REPO_URL}" --force
else
    # 2. Fallback to isolated Python venv
    printf "${YELLOW}[!]${NC} uv/pipx not found. Installing into isolated virtual environment...\n"
    
    # Locate suitable Python binary (>= 3.11)
    PYTHON=""
    for cmd in python3.13 python3.12 python3.11 python3 python; do
        if command -v "$cmd" >/dev/null 2>&1; then
            ver=$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
            maj=$(echo "$ver" | cut -d. -f1)
            min=$(echo "$ver" | cut -d. -f2)
            if [ "$maj" -eq 3 ] && [ "$min" -ge 11 ]; then
                PYTHON="$cmd"
                break
            fi
        fi
    done

    if [ -z "$PYTHON" ]; then
        printf "${RED}[x] Error:${NC} Python >= 3.11 is required to install Betteragy.\n"
        printf "    Please install Python 3.11+ via your package manager (brew, apt, etc.) and retry.\n"
        exit 1
    fi

    printf "${GREEN}[+]${NC} Using Python: $($PYTHON --version)\n"
    mkdir -p "$INSTALL_DIR" "$BIN_DIR"

    # Create / update venv
    if [ ! -d "$INSTALL_DIR/venv" ]; then
        "$PYTHON" -m venv "$INSTALL_DIR/venv"
    fi

    "$INSTALL_DIR/venv/bin/python" -m pip install --upgrade pip --quiet
    "$INSTALL_DIR/venv/bin/pip" install "git+${REPO_URL}" --quiet

    # Create symlink in ~/.local/bin
    ln -sf "$INSTALL_DIR/venv/bin/betteragy" "$BIN_DIR/betteragy"
    ln -sf "$INSTALL_DIR/venv/bin/betteragy" "$BIN_DIR/agy"
fi

# 3. Check PATH configuration
SHELL_NAME=$(basename "${SHELL:-/bin/bash}")
RC_FILE=""
if [ "$SHELL_NAME" = "zsh" ]; then
    RC_FILE="$HOME/.zshrc"
elif [ "$SHELL_NAME" = "bash" ]; then
    if [ -f "$HOME/.bashrc" ]; then
        RC_FILE="$HOME/.bashrc"
    else
        RC_FILE="$HOME/.bash_profile"
    fi
fi

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    printf "${YELLOW}[!] Notice:${NC} $BIN_DIR is not in your current PATH.\n"
    if [ -n "$RC_FILE" ] && [ -f "$RC_FILE" ]; then
        if ! grep -q 'export PATH=.*\.local/bin' "$RC_FILE"; then
            printf "    Adding ~/.local/bin to %s...\n" "$RC_FILE"
            echo '' >> "$RC_FILE"
            echo '# Added by Betteragy installer' >> "$RC_FILE"
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$RC_FILE"
        fi
        printf "${CYAN}==>${NC} Run: ${GREEN}source %s${NC} or restart your shell.\n" "$RC_FILE"
    fi
fi

printf "\n${GREEN}[ok] Betteragy v1.0.0 installed successfully!${NC}\n"
printf "--------------------------------------------------------\n"
printf "Quick Start:\n"
printf "  ${CYAN}betteragy${NC}           Launch Interactive TUI & Command Center\n"
printf "  ${CYAN}betteragy quota${NC}     View live AI model quotas & reset timers\n"
printf "  ${CYAN}betteragy proxy${NC}     Start transparent proxy with 429 auto-swap\n"
printf "  ${CYAN}betteragy --help${NC}    See all available commands\n"
printf "--------------------------------------------------------\n\n"
