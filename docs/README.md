# PraisonAI PPT - Documentation

[![PyPI version](https://badge.fury.io/py/praisonaippt.svg)](https://badge.fury.io/py/praisonaippt)

Welcome to the PraisonAI PPT documentation directory!

## 📚 Documentation Index

### User Documentation
- **[Main README](../README.md)** - Complete user guide and package overview
- **[Quick Start Guide](../QUICKSTART.md)** - Get started in 3 easy steps
- **[Highlights Feature](HIGHLIGHTS_FEATURE.md)** - Text highlighting documentation

### Development Documentation
- **[Implementation Summary](IMPLEMENTATION_SUMMARY.md)** - Complete implementation overview
- **[Highlights Implementation](HIGHLIGHTS_IMPLEMENTATION.md)** - Highlighting feature implementation details
- **[Restructuring Plan](RESTRUCTURING_PLAN.md)** - Original package restructuring plan
- **[Plan Review](PLAN_REVIEW.md)** - Plan review and validation

## 🎯 Quick Links

### For Users
- [Installation Instructions](../README.md#-installation)
- [Usage Examples](../README.md#-usage)
- [JSON Format Guide](../README.md#-json-file-format)
- [Highlighting Feature Guide](HIGHLIGHTS_FEATURE.md)

### For Developers
- [Package Structure](IMPLEMENTATION_SUMMARY.md#-final-package-structure)
- [Features Implemented](IMPLEMENTATION_SUMMARY.md#-features-implemented)
- [Code Organization](IMPLEMENTATION_SUMMARY.md#-key-improvements)

## 📖 Feature Documentation

### Text Highlighting
The text highlighting feature allows you to emphasize specific words or phrases in your presentations. See the [complete guide](HIGHLIGHTS_FEATURE.md) for:
- Usage examples
- JSON format
- Best practices
- Troubleshooting

## 🏗️ Architecture Documentation

### Package Structure
```
praisonaippt/
├── __init__.py       # Public API
├── core.py          # Presentation creation
├── utils.py         # Utility functions
├── loader.py        # JSON loading
└── cli.py           # Command-line interface
```

### Key Design Decisions
- Modular code separation for maintainability
- Both CLI and Python API supported
- Built-in examples for easy start
- Text highlighting with minimal configuration

## 🔧 Development Notes

### Font Sizes
- Verse Text: 32pt
- Reference Text: 22pt
- Section Titles: 44pt

### Highlight Formatting
- Bold text
- Orange color (RGB: 255, 140, 0)
- Case-insensitive matching

## 📝 Version History

### v1.0.0 (2025-10-26)
- Initial release
- Package restructuring completed
- Text highlighting feature added
- UV package manager support
- Comprehensive documentation

## 🤝 Contributing

For development setup and contribution guidelines, see the main [README](../README.md).

## 📞 Support

- **PyPI**: https://pypi.org/project/praisonaippt/
- **Repository**: https://github.com/MervinPraison/PraisonAIPPT
- **Issues**: https://github.com/MervinPraison/PraisonAIPPT/issues

---

**Last Updated**: 2025-10-26
