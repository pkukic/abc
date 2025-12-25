#!/bin/bash
# Installs shared libraries and prompts for ABC scripts

BIN_DIR="$HOME/.local/bin"

mkdir -p "$BIN_DIR/lib"
mkdir -p "$BIN_DIR/prompts"

# Install shared Python library
cp "$TEMPLATE_DIR/scripts/lib/common.py" "$BIN_DIR/lib/"
cp "$TEMPLATE_DIR/scripts/lib/__init__.py" "$BIN_DIR/lib/"

# Install shared shell library
cp "$TEMPLATE_DIR/scripts/lib/common.sh" "$BIN_DIR/lib/"
chmod +x "$BIN_DIR/lib/common.sh"

# Install prompts
cp "$TEMPLATE_DIR/prompts/"*.txt "$BIN_DIR/prompts/"

# Copy .env file for API keys if it exists
if [[ -f "$SCRIPT_DIR/.env" ]]; then
    cp "$SCRIPT_DIR/.env" "$BIN_DIR/"
fi

echo "✓ Shared libraries installed"
