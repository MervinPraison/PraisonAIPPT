# Installation Guide - PraisonAI PPT

## 🚀 Quick Install

The fastest way to get started:

```bash
pip install praisonaippt
```

That's it! You're ready to use PraisonAI PPT.

---

## 📦 Installation Methods

### Method 1: Install from PyPI (Recommended)

**Using pip:**
```bash
pip install praisonaippt
```

**Using uv (faster):**
```bash
uv pip install praisonaippt
```

**Verify installation:**
```bash
praisonaippt --version
```

---

### Method 2: Install from Source

**Clone and install:**
```bash
git clone https://github.com/MervinPraison/PraisonAIPPT.git
cd PraisonAIPPT
pip install .
```

**With uv:**
```bash
git clone https://github.com/MervinPraison/PraisonAIPPT.git
cd PraisonAIPPT
uv pip install .
```

---

### Method 3: Development Installation

For contributors and developers:

```bash
# Clone the repository
git clone https://github.com/MervinPraison/PraisonAIPPT.git
cd PraisonAIPPT

# Install in editable mode
pip install -e .

# Or with uv
uv pip install -e .
```

This allows you to modify the code and see changes immediately.

---

## 🔧 What is uv?

`uv` is a fast Python package installer written in Rust. It's 10-100x faster than pip!

**Install uv:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Learn more:** https://github.com/astral-sh/uv

---

## ✅ Verify Installation

After installation, verify everything works:

```bash
# Check version
praisonaippt --version

# List examples
praisonaippt --list-examples

# Show help
praisonaippt --help
```

---

## 📋 Requirements

- **Python**: 3.7 or higher
- **Dependencies**: python-pptx (automatically installed)

---

## 🐛 Troubleshooting

### Command not found

If you get "command not found: praisonaippt":

1. Make sure the package is installed:
   ```bash
   pip list | grep praisonaippt
   ```

2. Check your Python scripts directory is in PATH:
   ```bash
   python -m site --user-base
   ```

3. Try reinstalling:
   ```bash
   pip install --force-reinstall praisonaippt
   ```

### Permission errors

If you get permission errors:

```bash
# Install for current user only
pip install --user praisonaippt
```

### Virtual environment (recommended)

Using a virtual environment prevents conflicts:

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install
pip install praisonaippt
```

---

## 🔄 Upgrading

To upgrade to the latest version:

```bash
# With pip
pip install --upgrade praisonaippt

# With uv
uv pip install --upgrade praisonaippt
```

---

## 🗑️ Uninstalling

To remove the package:

```bash
pip uninstall praisonaippt
```

---

## 📞 Need Help?

- **PyPI**: https://pypi.org/project/praisonaippt/
- **GitHub**: https://github.com/MervinPraison/PraisonAIPPT
- **Issues**: https://github.com/MervinPraison/PraisonAIPPT/issues

---

**Ready to create presentations?** See [QUICKSTART.md](QUICKSTART.md) for your first presentation!
