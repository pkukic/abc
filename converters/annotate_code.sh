#!/bin/bash
# Installs the code annotation context menu (Studify Algo, Lang, OS, DSP)

MENU_DIR="$HOME/.local/share/kio/servicemenus"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$MENU_DIR"
mkdir -p "$BIN_DIR"

# Install helper scripts
cp "$TEMPLATE_DIR/scripts/annotate_code.py" "$BIN_DIR/"
cp "$TEMPLATE_DIR/scripts/studify-algo.sh" "$BIN_DIR/"
cp "$TEMPLATE_DIR/scripts/studify-lang.sh" "$BIN_DIR/"
cp "$TEMPLATE_DIR/scripts/studify-os.sh" "$BIN_DIR/"
cp "$TEMPLATE_DIR/scripts/studify-dsp.sh" "$BIN_DIR/"
chmod +x "$BIN_DIR/annotate_code.py"
chmod +x "$BIN_DIR/studify-algo.sh"
chmod +x "$BIN_DIR/studify-lang.sh"
chmod +x "$BIN_DIR/studify-os.sh"
chmod +x "$BIN_DIR/studify-dsp.sh"

# Copy .env file for API keys if it exists
if [[ -f "$SCRIPT_DIR/.env" ]]; then
    cp "$SCRIPT_DIR/.env" "$BIN_DIR/"
fi

# Install desktop entry
cp "$TEMPLATE_DIR/desktop/annotate-code.desktop" "$MENU_DIR/"
chmod +x "$MENU_DIR/annotate-code.desktop"

echo "✓ Code annotation menu installed"
