# Python Package Restructuring Plan
## Project: Bible Verses PowerPoint Generator

---

## 1. CURRENT STATE ANALYSIS

### Current Files:
- `app.py` - Main script with JSON loading and CLI
- `create_presentation.py` - Hardcoded verses version
- `create_bible_verses_presentation.py` - Duplicate of app.py
- `README.md` - Documentation
- `.gitignore` - Git ignore file
- `verses.json`, `tamil_verses.json`, `sample_verses.json` - Data files
- Multiple `.pptx` files - Generated outputs

### Issues Identified:
1. **Code Duplication**: `app.py` and `create_bible_verses_presentation.py` are nearly identical
2. **No Package Structure**: Scripts are loose files, not a proper Python package
3. **Mixed Concerns**: Business logic, CLI, and utilities all in one file
4. **No Setup Configuration**: Missing `setup.py` or `pyproject.toml`
5. **No Tests**: No test suite
6. **Hardcoded Script**: `create_presentation.py` has hardcoded verses (outdated)
7. **No Examples Directory**: Sample data mixed with source code

---

## 2. PROPOSED PACKAGE STRUCTURE

```
ppt-package/
├── praisonaippt/              # Main package directory
│   ├── __init__.py                 # Package initialization & version
│   ├── core.py                     # Core presentation creation logic
│   ├── utils.py                    # Utility functions (split_long_text, etc.)
│   ├── loader.py                   # JSON data loading functions
│   └── cli.py                      # Command-line interface
│
├── examples/                       # Example data files
│   ├── verses.json                 # Default example
│   ├── tamil_verses.json           # Tamil example
│   ├── sample_verses.json          # Simple example
│   └── template.json               # Empty template for users
│
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── test_core.py
│   ├── test_utils.py
│   └── test_loader.py
│
├── docs/                           # Documentation
│   ├── usage.md                    # Usage guide
│   └── json_format.md              # JSON format specification
│
├── output/                         # Default output directory (gitignored)
│   └── .gitkeep
│
├── setup.py                        # Package setup file
├── pyproject.toml                  # Modern Python project config
├── requirements.txt                # Dependencies
├── README.md                       # Updated main documentation
├── .gitignore                      # Updated gitignore
├── LICENSE                         # License file (MIT recommended)
└── MANIFEST.in                     # Include non-Python files in package
```

---

## 3. DETAILED MODULE BREAKDOWN

### 3.1 `praisonaippt/__init__.py`
**Purpose**: Package initialization and public API exposure
**Contents**:
- Package version (`__version__ = "1.0.0"`)
- Import main functions for easy access
- Public API: `create_presentation()`, `load_verses()`

### 3.2 `praisonaippt/core.py`
**Purpose**: Core presentation creation logic
**Functions**:
- `create_presentation(data, output_file=None, custom_title=None)` - Main function
- `add_title_slide(prs, title, subtitle)` - Create title slide
- `add_section_slide(prs, section_name)` - Create section slide
- `add_verse_slide(prs, verse_text, reference, part_num=None)` - Create verse slide
- `style_text_frame(text_frame, font_size, color, alignment)` - Apply styling

### 3.3 `praisonaippt/utils.py`
**Purpose**: Utility functions
**Functions**:
- `split_long_text(text, max_length=200)` - Split long text
- `sanitize_filename(filename)` - Clean filename for output
- `validate_verse_data(data)` - Validate JSON structure

### 3.4 `praisonaippt/loader.py`
**Purpose**: Data loading and validation
**Functions**:
- `load_verses_from_file(filepath)` - Load and validate JSON
- `load_verses_from_dict(data)` - Load from dictionary
- `get_example_path(example_name)` - Get path to example files

### 3.5 `praisonaippt/cli.py`
**Purpose**: Command-line interface
**Functions**:
- `main()` - CLI entry point with argparse
- `parse_arguments()` - Argument parsing
- Command-line options:
  - `-i, --input` - Input JSON file (default: verses.json)
  - `-o, --output` - Output PPTX file (auto-generated if not provided)
  - `-t, --title` - Custom presentation title
  - `--list-examples` - List available example files
  - `--use-example` - Use a built-in example
  - `-v, --version` - Show version

---

## 4. CONFIGURATION FILES

### 4.1 `setup.py`
```python
from setuptools import setup, find_packages

setup(
    name="praisonaippt",
    version="1.0.0",
    packages=find_packages(),
    install_requires=["python-pptx>=0.6.21"],
    entry_points={
        "console_scripts": [
            "praisonaippt=praisonaippt.cli:main",
        ],
    },
    # ... metadata
)
```

### 4.2 `pyproject.toml`
Modern Python project configuration with build system and dependencies.

### 4.3 `requirements.txt`
```
python-pptx>=0.6.21
```

### 4.4 `MANIFEST.in`
Include example JSON files in the package distribution.

---

## 5. USER EXPERIENCE IMPROVEMENTS

### 5.1 Installation Methods

**Method 1: From Source (Development)**
```bash
git clone <repo-url>
cd ppt-package
pip install -e .
```

**Method 2: From PyPI (Future)**
```bash
pip install praisonaippt
```

### 5.2 Usage Methods

**Method 1: Command Line**
```bash
# Use default verses.json in current directory
praisonaippt

# Use specific input file
praisonaippt -i my_verses.json -o my_presentation.pptx

# Use built-in example
praisonaippt --use-example tamil_verses

# List available examples
praisonaippt --list-examples
```

**Method 2: Python API**
```python
from praisonaippt import create_presentation, load_verses

# Load and create
data = load_verses("verses.json")
create_presentation(data, output_file="output.pptx")

# Or in one step
from praisonaippt import create_presentation_from_file
create_presentation_from_file("verses.json", "output.pptx")
```

### 5.3 Quick Start for New Users
1. Install package: `pip install -e .`
2. Copy template: `praisonaippt --create-template`
3. Edit `my_verses.json` with your verses
4. Generate: `praisonaippt -i my_verses.json`

---

## 6. MIGRATION STRATEGY

### 6.1 Code Migration
1. Extract `split_long_text()` → `utils.py`
2. Extract `load_verses_data()` → `loader.py`
3. Refactor `create_bible_verses_presentation()` → `core.py` (split into smaller functions)
4. Extract CLI logic from `app.py` → `cli.py`
5. Delete duplicate files (`create_bible_verses_presentation.py`, `create_presentation.py`)

### 6.2 Data Migration
1. Move all `.json` files → `examples/`
2. Move all `.pptx` files → `output/` or delete (they're generated files)
3. Keep one `.json` in root as default for backward compatibility (optional)

### 6.3 Documentation Migration
1. Update `README.md` with new structure and installation instructions
2. Split detailed docs into `docs/` directory
3. Add docstrings to all functions
4. Create `CHANGELOG.md` for version tracking

---

## 7. TESTING STRATEGY

### 7.1 Unit Tests
- `test_utils.py`: Test `split_long_text()`, `sanitize_filename()`
- `test_loader.py`: Test JSON loading, validation, error handling
- `test_core.py`: Test presentation creation functions

### 7.2 Integration Tests
- Test full workflow: JSON → PPTX
- Test CLI commands
- Test with example files

### 7.3 Test Data
- Create minimal test JSON files in `tests/fixtures/`

---

## 8. BACKWARD COMPATIBILITY

### Option 1: Keep Legacy Script (Recommended)
- Keep `app.py` as a wrapper that imports from the package
- Add deprecation warning
- Remove in version 2.0.0

### Option 2: Clean Break
- Remove old scripts entirely
- Update README with migration guide
- Provide clear error messages if old scripts are called

**Recommendation**: Option 1 for smoother transition

---

## 9. IMPLEMENTATION CHECKLIST

### Phase 1: Structure Setup
- [ ] Create package directory structure
- [ ] Create all `__init__.py` files
- [ ] Create configuration files (`setup.py`, `pyproject.toml`, etc.)
- [ ] Update `.gitignore`

### Phase 2: Code Migration
- [ ] Create `utils.py` with utility functions
- [ ] Create `loader.py` with data loading functions
- [ ] Create `core.py` with presentation logic (refactored)
- [ ] Create `cli.py` with command-line interface
- [ ] Update `__init__.py` with public API

### Phase 3: Data & Documentation
- [ ] Move JSON files to `examples/`
- [ ] Create `template.json`
- [ ] Update `README.md`
- [ ] Create documentation in `docs/`
- [ ] Add LICENSE file

### Phase 4: Testing
- [ ] Create test structure
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Run all tests

### Phase 5: Cleanup
- [ ] Remove duplicate files
- [ ] Clean up generated `.pptx` files
- [ ] Verify package installation
- [ ] Test CLI commands
- [ ] Test Python API

---

## 10. BENEFITS OF NEW STRUCTURE

### For Developers:
✅ **Modular Code**: Easy to maintain and extend
✅ **Testable**: Clear separation of concerns
✅ **Reusable**: Can import specific functions
✅ **Professional**: Follows Python packaging best practices

### For Users:
✅ **Easy Installation**: `pip install` support
✅ **Clear Documentation**: Organized docs and examples
✅ **Multiple Usage Methods**: CLI and Python API
✅ **Better Error Messages**: Validation and helpful feedback
✅ **Examples Included**: Ready-to-use templates

### For Distribution:
✅ **PyPI Ready**: Can publish to Python Package Index
✅ **Version Management**: Proper versioning system
✅ **Dependency Management**: Clear requirements
✅ **Cross-Platform**: Works on Windows, Mac, Linux

---

## 11. ESTIMATED EFFORT

- **Phase 1**: 30 minutes (structure setup)
- **Phase 2**: 1 hour (code migration and refactoring)
- **Phase 3**: 30 minutes (data and documentation)
- **Phase 4**: 1 hour (testing - optional for MVP)
- **Phase 5**: 15 minutes (cleanup)

**Total**: ~3 hours for complete implementation

---

## 12. NEXT STEPS

1. **Review this plan** - Verify structure and approach
2. **Get approval** - Confirm this meets requirements
3. **Execute Phase 1** - Create directory structure
4. **Execute Phase 2** - Migrate and refactor code
5. **Execute Phase 3** - Update documentation
6. **Execute Phase 4** - Add tests (optional)
7. **Execute Phase 5** - Final cleanup and verification

---

## NOTES

- Keep changes minimal where possible (per user preference)
- Focus on structure over feature additions
- Maintain all existing functionality
- Prioritize user-friendliness for new users
- Make it easy to start from scratch with clear examples
