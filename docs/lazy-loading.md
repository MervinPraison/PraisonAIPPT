# Lazy Loading

PraisonAI PPT uses lazy loading for optional dependencies, ensuring the core package works without requiring all optional features to be installed.

## What is Lazy Loading?

Lazy loading is a design pattern that delays the import of optional dependencies until they are actually needed. This provides several benefits:

1. **Smaller Installation**: Core package has minimal dependencies
2. **Faster Startup**: Only load what you need
3. **No Import Errors**: Package works even without optional dependencies
4. **Clear Feedback**: Helpful error messages when features are unavailable

## How It Works

### Traditional Import (Eager Loading)

```python
# This fails if google-api-python-client is not installed
from googleapiclient.discovery import build

def upload_file():
    service = build('drive', 'v3')
    # ... upload logic
```

### Lazy Loading

```python
from praisonaippt.lazy_loader import lazy_import

# This doesn't fail - import happens only when accessed
google_api = lazy_import('googleapiclient.discovery', 'Google Drive upload', 'gdrive')

def upload_file():
    # Import happens here, only if function is called
    service = google_api.build('drive', 'v3')
    # ... upload logic
```

## Using Lazy Loading in Your Code

### Basic Usage

```python
from praisonaippt.lazy_loader import lazy_import

# Create a lazy loader
service_account = lazy_import(
    'google.oauth2.service_account',  # Module to import
    'Google Drive upload',             # Feature name (for error messages)
    'gdrive'                           # pip install extra name
)

# Module is not imported yet - no error even if not installed

# Use it like a normal module
credentials = service_account.Credentials.from_service_account_file('key.json')
# Module is imported here, only when accessed
```

### Check Availability Before Use

```python
from praisonaippt.lazy_loader import check_optional_dependency

if check_optional_dependency('google.oauth2.service_account'):
    # Dependencies are available
    from praisonaippt.gdrive_uploader import upload_to_gdrive
    result = upload_to_gdrive('file.pptx', credentials_path='creds.json')
else:
    # Dependencies not available
    print("Install with: pip install praisonaippt[gdrive]")
```

### Error Handling

```python
from praisonaippt.lazy_loader import lazy_import, LazyImportError

try:
    google_api = lazy_import('googleapiclient.discovery', 'Google Drive', 'gdrive')
    service = google_api.build('drive', 'v3')
except LazyImportError as e:
    print(f"Feature not available: {e.feature_name}")
    print(f"Install with: pip install praisonaippt[{e.install_extra}]")
```

## Features Using Lazy Loading

### Google Drive Upload

The Google Drive upload feature uses lazy loading:

```python
# This works even without Google Drive dependencies installed
from praisonaippt import create_presentation

data = {"presentation_title": "Test", "sections": []}
output = create_presentation(data)

# This only loads Google Drive dependencies when called
from praisonaippt.gdrive_uploader import is_gdrive_available

if is_gdrive_available():
    from praisonaippt.gdrive_uploader import upload_to_gdrive
    upload_to_gdrive(output, credentials_path='creds.json')
```

### PDF Conversion (Aspose)

PDF conversion with Aspose also uses optional dependencies:

```bash
# Install without Aspose
pip install praisonaippt

# Aspose is loaded only when using --convert-pdf with --pdf-backend aspose
praisonaippt -i verses.json --convert-pdf --pdf-backend aspose
```

## API Reference

### `lazy_import(module_name, feature_name, install_extra)`

Create a lazy loader for an optional module.

**Parameters:**
- `module_name` (str): Name of the module to import (e.g., 'google.oauth2.service_account')
- `feature_name` (str): Human-readable feature name (e.g., 'Google Drive upload')
- `install_extra` (str): Extra name for pip install (e.g., 'gdrive')

**Returns:**
- `LazyLoader`: Lazy loader instance

**Example:**
```python
google_auth = lazy_import('google.oauth2.service_account', 'Google Drive', 'gdrive')
credentials = google_auth.Credentials.from_service_account_file('key.json')
```

### `check_optional_dependency(module_name)`

Check if an optional dependency is available without importing it.

**Parameters:**
- `module_name` (str): Name of the module to check

**Returns:**
- `bool`: True if module is available, False otherwise

**Example:**
```python
if check_optional_dependency('google.oauth2.service_account'):
    print("Google Drive upload is available")
else:
    print("Install with: pip install praisonaippt[gdrive]")
```

### `LazyImportError`

Custom exception raised when a lazy import fails.

**Attributes:**
- `module_name` (str): Name of the missing module
- `feature_name` (str): Human-readable feature name
- `install_extra` (str): Extra name for pip install

**Example:**
```python
from praisonaippt.lazy_loader import LazyImportError

try:
    # ... code using lazy import
except LazyImportError as e:
    print(f"Missing: {e.module_name}")
    print(f"For: {e.feature_name}")
    print(f"Install: pip install praisonaippt[{e.install_extra}]")
```

## Creating Your Own Lazy Loaded Features

### Step 1: Create the Lazy Loader

```python
from praisonaippt.lazy_loader import lazy_import

# In your module
my_optional_lib = lazy_import(
    'optional_library',
    'My Feature',
    'myfeature'
)

def my_function():
    # Library is imported only when this function is called
    result = my_optional_lib.do_something()
    return result
```

### Step 2: Add to setup.py

```python
extras_require={
    'myfeature': ['optional-library>=1.0.0'],
    'all': ['optional-library>=1.0.0', ...],
}
```

### Step 3: Provide Availability Check

```python
from praisonaippt.lazy_loader import check_optional_dependency

def is_myfeature_available():
    return check_optional_dependency('optional_library')
```

### Step 4: Document Usage

```python
"""
To use this feature, install with:
    pip install praisonaippt[myfeature]

Or check availability:
    from mymodule import is_myfeature_available
    if is_myfeature_available():
        # Use feature
"""
```

## Best Practices

### 1. Always Provide Availability Checks

```python
def is_feature_available():
    return check_optional_dependency('required_module')
```

### 2. Use Descriptive Feature Names

```python
# Good
lazy_import('google.oauth2', 'Google Drive upload', 'gdrive')

# Bad
lazy_import('google.oauth2', 'feature', 'extra')
```

### 3. Handle Errors Gracefully

```python
try:
    from .optional_feature import do_something
    result = do_something()
except LazyImportError:
    print("Feature not available. Install with: pip install package[extra]")
    result = None
```

### 4. Document Requirements Clearly

Always document:
- What the feature does
- How to install dependencies
- How to check availability
- Example usage

### 5. Test Without Dependencies

Ensure your package works without optional dependencies:

```bash
# Test in clean environment
python -m venv test_env
source test_env/bin/activate
pip install praisonaippt  # Without extras
python -c "from praisonaippt import create_presentation; print('OK')"
```

## Installation Extras

PraisonAI PPT provides several installation extras:

```bash
# Core package only
pip install praisonaippt

# With PDF conversion (Aspose)
pip install praisonaippt[pdf-aspose]

# With PDF conversion (all backends)
pip install praisonaippt[pdf-all]

# With Google Drive upload
pip install praisonaippt[gdrive]

# With everything
pip install praisonaippt[all]
```

## Troubleshooting

### Import Errors

**Problem**: Getting import errors even with lazy loading

**Solution**: Make sure you're not importing the module at the top level:

```python
# Wrong - imports immediately
from googleapiclient.discovery import build

# Correct - imports lazily
from praisonaippt.lazy_loader import lazy_import
google_api = lazy_import('googleapiclient.discovery', 'Feature', 'extra')
```

### Feature Not Available

**Problem**: Feature shows as not available even after installing

**Solution**: Restart Python interpreter or reinstall:

```bash
pip uninstall praisonaippt
pip install praisonaippt[gdrive]
```

### Confusing Error Messages

**Problem**: Error messages don't clearly indicate what's missing

**Solution**: Always use descriptive feature names and install extras:

```python
lazy_import(
    'module.name',
    'Clear Feature Description',  # Shows in error message
    'install-extra'                # Shows in pip install command
)
```

## Performance Considerations

### Startup Time

Lazy loading improves startup time by deferring imports:

```python
# Without lazy loading
import time
start = time.time()
from googleapiclient.discovery import build  # ~0.5s
from google.oauth2.service_account import Credentials  # ~0.3s
print(f"Import time: {time.time() - start}s")  # ~0.8s

# With lazy loading
start = time.time()
from praisonaippt.lazy_loader import lazy_import
google_api = lazy_import('googleapiclient.discovery', 'GDrive', 'gdrive')
print(f"Import time: {time.time() - start}s")  # ~0.001s
```

### Memory Usage

Lazy loading reduces memory usage for unused features:

```python
# Memory is only allocated when feature is used
from praisonaippt import create_presentation

# Low memory usage - Google Drive not loaded
data = {"presentation_title": "Test", "sections": []}
create_presentation(data)

# Memory increases only if Google Drive is used
from praisonaippt.gdrive_uploader import upload_to_gdrive
upload_to_gdrive('file.pptx', credentials_path='creds.json')
```

## Examples

### Example 1: Optional Feature with Fallback

```python
from praisonaippt.lazy_loader import check_optional_dependency

def save_presentation(data, output_file, upload=False):
    from praisonaippt import create_presentation
    
    # Create presentation
    result = create_presentation(data, output_file)
    
    # Upload if requested and available
    if upload:
        if check_optional_dependency('google.oauth2.service_account'):
            from praisonaippt.gdrive_uploader import upload_to_gdrive
            upload_to_gdrive(result, credentials_path='creds.json')
            print("Uploaded to Google Drive")
        else:
            print("Google Drive upload not available")
            print("Install with: pip install praisonaippt[gdrive]")
    
    return result
```

### Example 2: Multiple Optional Features

```python
from praisonaippt.lazy_loader import check_optional_dependency

def process_presentation(data, options):
    from praisonaippt import create_presentation
    
    # Create presentation
    output = create_presentation(data)
    
    # Optional: Convert to PDF
    if options.get('pdf') and check_optional_dependency('aspose.slides'):
        from praisonaippt import convert_pptx_to_pdf
        convert_pptx_to_pdf(output)
    
    # Optional: Upload to Google Drive
    if options.get('upload') and check_optional_dependency('google.oauth2'):
        from praisonaippt.gdrive_uploader import upload_to_gdrive
        upload_to_gdrive(output, credentials_path='creds.json')
    
    return output
```

### Example 3: Graceful Degradation

```python
from praisonaippt.lazy_loader import lazy_import, LazyImportError

def upload_with_fallback(file_path):
    try:
        # Try Google Drive first
        from praisonaippt.gdrive_uploader import upload_to_gdrive
        result = upload_to_gdrive(file_path, credentials_path='creds.json')
        return f"Uploaded to Google Drive: {result['webViewLink']}"
    except LazyImportError:
        # Fall back to local storage
        print("Google Drive not available, keeping file locally")
        return f"Saved locally: {file_path}"
    except Exception as e:
        print(f"Upload failed: {e}")
        return f"Saved locally: {file_path}"
```
