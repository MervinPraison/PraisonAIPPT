#!/bin/bash
# Quick installation script for pptx-bible-verses package

set -e

echo "=========================================="
echo "PowerPoint Bible Verses Generator"
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
echo "Installing pptx-bible-verses package..."
uv pip install -e .

echo ""
echo "=========================================="
echo "✓ Installation Complete!"
echo "=========================================="
echo ""
echo "Quick Start:"
echo "  1. List examples:     pptx-bible-verses --list-examples"
echo "  2. Use an example:    pptx-bible-verses --use-example verses"
echo "  3. Create from file:  pptx-bible-verses -i my_verses.json"
echo "  4. Show help:         pptx-bible-verses --help"
echo ""
echo "To create your own presentation:"
echo "  cp examples/template.json my_verses.json"
echo "  # Edit my_verses.json with your verses"
echo "  pptx-bible-verses -i my_verses.json"
echo ""
