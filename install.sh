#!/bin/bash
# Quick installation script for praisonaippt package

set -e

echo "=========================================="
echo "PraisonAI PPT - PowerPoint Bible Verses Generator"
echo "Installation Script"
echo "=========================================="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "⚠️  uv is not installed."
    echo "Installing uv (fast Python package installer)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo ""
    echo "✓ uv installed successfully!"
    echo "Please restart your terminal or run: source ~/.bashrc (or ~/.zshrc)"
    echo "Then run this script again."
    exit 0
fi

echo "✓ uv is installed"
echo ""

# Install the package
echo "Installing praisonaippt package..."
uv pip install -e .

echo ""
echo "=========================================="
echo "✓ Installation Complete!"
echo "=========================================="
echo ""
echo "Quick Start:"
echo "  1. List examples:     praisonaippt --list-examples"
echo "  2. Use an example:    praisonaippt --use-example verses"
echo "  3. Create from file:  praisonaippt -i my_verses.json"
echo "  4. Show help:         praisonaippt --help"
echo ""
echo "To create your own presentation:"
echo "  cp examples/template.json my_verses.json"
echo "  # Edit my_verses.json with your verses"
echo "  praisonaippt -i my_verses.json"
echo ""
