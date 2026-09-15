#!/usr/bin/env bash
# Betteragy Installer for macOS and Linux
# Usage: curl -fsSL https://betteragy.dev/install.sh | bash

set -euo pipefail

REPO_URL="https://github.com/mncuchiinhuttt/betteragy.git"
INSTALL_DIR="$HOME/.betteragy"
BIN_DIR="$HOME/.local/bin"

# Terminal Colors & Styles
BOLD='\033[1m'
DIM='\033[2m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # Reset

clear 2>/dev/null || true

printf "${CYAN}"
cat << 'EOF'
  ____       _   _                             
 |  _ \     | | | |                            
 | |_) | ___| |_| |_ ___ _ __ __ _  __ _ _   _ 
 |  _ < / _ \ __| __/ _ \ '__/ _` |/ _` | | | |
 | |_) |  __/ |_| ||  __/ | | (_| | (_| | |_| |
 |____/ \___|\__|\__\___|_|  \__,_|\__, |\__, |
                                    __/ | __/ |
                                   |___/ |___/ 
EOF
printf "${NC}\n"
printf "  ${BOLD}Everything to Power Antigravity AI — v1.0.0${NC}\n"
printf "  ${DIM}Zero-restart auto-rotation & quota intelligence${NC}\n\n"

# 1. Environment & Python check
printf "  ${CYAN}[1/3]${NC} Checking Python runtime environment...\n"
if command -v uv >/dev/null 2>&1; then
    printf "        ${GREEN}+${NC} Detected ${BOLD}uv${NC}. Installing via uv tool...\n"
    uv tool install "git+${REPO_URL}" --force --quiet
elif command -v pipx >/dev/null 2>&1; then
    printf "        ${GREEN}+${NC} Detected ${BOLD}pipx${NC}. Installing via pipx...\n"
    pipx install "git+${REPO_URL}" --force --quiet
else
    # Fallback to isolated Python venv
    printf "        ${YELLOW}!${NC} Using isolated Python virtual environment...\n"
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
        printf "\n  ${RED}[x] Error: Python 3.11+ is required to run Betteragy.${NC}\n"
        printf "      Please install Python 3.11+ via brew, apt, or python.org and retry.\n\n"
        exit 1
    fi

    printf "        ${GREEN}+${NC} Using Python: $($PYTHON --version)\n"
    mkdir -p "$INSTALL_DIR" "$BIN_DIR"

    if [ ! -d "$INSTALL_DIR/venv" ]; then
        "$PYTHON" -m venv "$INSTALL_DIR/venv"
    fi

    "$INSTALL_DIR/venv/bin/python" -m pip install --upgrade pip --quiet
    "$INSTALL_DIR/venv/bin/pip" install "git+${REPO_URL}" --quiet

    ln -sf "$INSTALL_DIR/venv/bin/betteragy" "$BIN_DIR/betteragy"
    ln -sf "$INSTALL_DIR/venv/bin/betteragy" "$BIN_DIR/agy"
fi

# 2. PATH Verification
printf "  ${CYAN}[2/3]${NC} Verifying system PATH configuration...\n"
SHELL_NAME=$(basename "${SHELL:-/bin/bash}")
RC_FILE=""
if [ "$SHELL_NAME" = "zsh" ]; then
    RC_FILE="$HOME/.zshrc"
elif [ "$SHELL_NAME" = "bash" ]; then
    RC_FILE="$HOME/.bashrc"
    [ ! -f "$RC_FILE" ] && RC_FILE="$HOME/.bash_profile"
fi

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    if [ -n "$RC_FILE" ] && [ -f "$RC_FILE" ]; then
        if ! grep -q 'export PATH=.*\.local/bin' "$RC_FILE"; then
            echo '' >> "$RC_FILE"
            echo '# Added by Betteragy installer' >> "$RC_FILE"
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$RC_FILE"
        fi
        printf "        ${YELLOW}!${NC} Added ~/.local/bin to %s\n" "$RC_FILE"
        printf "        ${DIM}Run 'source %s' after installation${NC}\n" "$RC_FILE"
    fi
else
    printf "        ${GREEN}+${NC} PATH contains ~/.local/bin (Ready)\n"
fi

# 3. Installation Summary
printf "  ${CYAN}[3/3]${NC} Finalizing binary hooks...\n\n"

printf "  ┌────────────────────────────────────────────────────────┐\n"
printf "  │  ${BOLD}${GREEN}Betteragy v1.0.0 — Installed Successfully!${NC}            │\n"
printf "  ├────────────────────────────────────────────────────────┤\n"
printf "  │  ${BOLD}Commands:${NC}                                             │\n"
printf "  │    ${CYAN}betteragy${NC}           Launch Interactive TUI Dashboard  │\n"
printf "  │    ${CYAN}betteragy quota${NC}     Inspect Gemini 3.8 & Claude Quota │\n"
printf "  │    ${CYAN}betteragy proxy${NC}     Start 429 Interception MITM Daemon│\n"
printf "  │    ${CYAN}betteragy --help${NC}    Display full CLI reference        │\n"
printf "  └────────────────────────────────────────────────────────┘\n\n"

# Interactive Star on GitHub Prompt
printf "  ${BOLD}${CYAN}* Love Betteragy? Star us on GitHub!${NC}\n"
printf "  ${DIM}Repository: https://github.com/mncuchiinhuttt/betteragy${NC}\n\n"
printf "  ${YELLOW}==>${NC} ${BOLD}Press [ENTER] to star on GitHub${NC} ${DIM}(or Ctrl+C to exit)${NC}: "

# Read keyboard input even when running via `curl ... | bash`
KEY=""
if [ -t 0 ]; then
    read -r KEY || true
elif [ -r /dev/tty ]; then
    read -r KEY </dev/tty || true
fi

# Open repository in default browser
REPO_PAGE="https://github.com/mncuchiinhuttt/betteragy"
if command -v open >/dev/null 2>&1; then
    open "$REPO_PAGE" >/dev/null 2>&1 &
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$REPO_PAGE" >/dev/null 2>&1 &
fi

printf "\n  ${GREEN}[ok] Thank you for starring! Happy coding with Antigravity AI.${NC}\n\n"
