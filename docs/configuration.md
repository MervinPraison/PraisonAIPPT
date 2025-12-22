# Configuration Management

PraisonAI PPT uses a YAML configuration file to store persistent settings, eliminating the need to specify options repeatedly via command-line arguments.

## Configuration File

**Location**: `~/.praisonaippt/config.yaml`  
**Format**: YAML (user-friendly, easy to edit)  
**Auto-created**: On first `praisonaippt config init` run

## Quick Start

### Initialize Configuration

```bash
praisonaippt config init
```

This will prompt you interactively for:
- Google Drive credentials path
- Default folder name
- PDF conversion settings
- Default behaviors

### Show Current Configuration

```bash
praisonaippt config show
```

Or use the flag:
```bash
praisonaippt --config-show
```

## Configuration Structure

```yaml
gdrive:
  credentials_path: ~/.praisonaippt/oauth-credentials.json
  folder_id: null
  folder_name: Bible Presentations
  use_date_folders: false
  date_format: YYYY/MM

pdf:
  backend: auto
  quality: high
  compression: true

defaults:
  output_format: pptx
  auto_convert_pdf: false
  auto_upload_gdrive: false
```

## Configuration Options

### Google Drive Settings (`gdrive`)

| Option | Type | Description | Example |
|--------|------|-------------|---------|
| `credentials_path` | string | Path to OAuth or service account credentials | `~/.praisonaippt/oauth-credentials.json` |
| `folder_id` | string | Google Drive folder ID | `1wolJexKoxxIsEGqjVLdGASIDhNazNkit` |
| `folder_name` | string | Folder name (auto-creates if missing) | `Bible Presentations` |
| `use_date_folders` | boolean | Create date-based subfolders | `true` or `false` |
| `date_format` | string | Date folder format pattern | `YYYY/MM`, `YYYY-MM`, `YYYY/MM/DD` |

### PDF Settings (`pdf`)

| Option | Type | Description | Values |
|--------|------|-------------|--------|
| `backend` | string | PDF conversion backend | `aspose`, `libreoffice`, `auto` |
| `quality` | string | PDF quality level | `low`, `medium`, `high` |
| `compression` | boolean | Enable image compression | `true`, `false` |

### Default Behaviors (`defaults`)

| Option | Type | Description | Values |
|--------|------|-------------|--------|
| `output_format` | string | Default output format | `pptx` |
| `auto_convert_pdf` | boolean | Automatically convert to PDF | `true`, `false` |
| `auto_upload_gdrive` | boolean | Automatically upload to Google Drive | `true`, `false` |

## Configuration Priority

Settings are applied in this order (later overrides earlier):

1. **Built-in defaults** (lowest priority)
2. **Configuration file** (`~/.praisonaippt/config.yaml`)
3. **Command-line arguments** (highest priority)

### Example

```yaml
# config.yaml
gdrive:
  folder_name: Bible Presentations
```

```bash
# This command overrides the config
praisonaippt -i verses.json --upload-gdrive --gdrive-folder-name "Sunday Service"
```

Result: Uploads to "Sunday Service" folder, not "Bible Presentations"

## Configuration Examples

### Example 1: Google Drive Only

```yaml
gdrive:
  credentials_path: ~/.praisonaippt/oauth-credentials.json
  folder_name: Church Presentations
```

### Example 2: Auto-Convert to PDF

```yaml
pdf:
  backend: libreoffice
  quality: high
  compression: false

defaults:
  auto_convert_pdf: true
```

### Example 3: Complete Automation

```yaml
gdrive:
  credentials_path: ~/.praisonaippt/oauth-credentials.json
  folder_name: Bible Study
  use_date_folders: true
  date_format: YYYY/MM

pdf:
  backend: auto
  quality: high

defaults:
  auto_convert_pdf: true
  auto_upload_gdrive: true
```

With this config, just run:
```bash
praisonaippt -i verses.json
```

It will automatically:
1. Create PPTX presentation
2. Convert to PDF
3. Upload to Google Drive in `Bible Study/2024/12/`

### Example 4: With Comments

```yaml
# Google Drive Settings
gdrive:
  credentials_path: ~/.praisonaippt/oauth-credentials.json  # OAuth credentials
  folder_name: Bible Presentations                          # Auto-creates if missing
  use_date_folders: true                                    # Organize by date
  date_format: YYYY/MM                                      # Year/Month folders

# PDF Conversion
pdf:
  backend: auto      # Options: aspose, libreoffice, auto
  quality: high      # Options: low, medium, high
  compression: true  # Reduce file size

# Automation
defaults:
  auto_convert_pdf: false     # Set true for automatic PDF
  auto_upload_gdrive: false   # Set true for automatic upload
```

## Manual Configuration

### Create Config File

```bash
mkdir -p ~/.praisonaippt
nano ~/.praisonaippt/config.yaml
```

### Edit Config File

```bash
# Using nano
nano ~/.praisonaippt/config.yaml

# Using vim
vim ~/.praisonaippt/config.yaml

# Using VS Code
code ~/.praisonaippt/config.yaml
```

## Date Folder Formats

When `use_date_folders: true`, files are organized by date:

| Format | Example | Result |
|--------|---------|--------|
| `YYYY/MM/DD` | 2024/12/22 | `Folder/2024/12/22/file.pptx` |
| `YYYY/MM` | 2024/12 | `Folder/2024/12/file.pptx` |
| `YYYY-MM-DD` | 2024-12-22 | `Folder/2024-12-22/file.pptx` |
| `YYYY-MM` | 2024-12 | `Folder/2024-12/file.pptx` |
| `YYYY` | 2024 | `Folder/2024/file.pptx` |

## Python API

### Load Configuration

```python
from praisonaippt import load_config

config = load_config()

# Get specific values
creds = config.get_gdrive_credentials()
folder = config.get_gdrive_folder_name()
use_dates = config.use_date_folders()
```

### Initialize Configuration

```python
from praisonaippt import init_config

# Interactive setup
config = init_config(interactive=True)

# Non-interactive (uses defaults)
config = init_config(interactive=False)
```

### Access Configuration

```python
from praisonaippt import Config

config = Config()

# Get values
backend = config.get('pdf', 'backend', 'auto')
quality = config.get('pdf', 'quality', 'high')

# Set values
config.set('pdf', 'backend', 'libreoffice')
config.set('defaults', 'auto_convert_pdf', True)

# Save changes
config.save()
```

## CLI Commands

### Initialize Configuration

```bash
# Interactive setup
praisonaippt config init
praisonaippt --config-init

# Show current config
praisonaippt config show
praisonaippt --config-show
```

### Setup Credentials

```bash
# OAuth (for personal Drive)
praisonaippt setup-oauth

# Service account (for Shared Drive)
praisonaippt setup-credentials
```

## Benefits

✅ **No Repetition** - Set credentials once, use everywhere  
✅ **Faster Commands** - Less typing, fewer arguments  
✅ **Consistent Settings** - Same quality/backend every time  
✅ **Secure** - Credentials stored in home directory  
✅ **Flexible** - Override config with CLI args when needed  
✅ **User-Friendly** - YAML format with comments support  

## Troubleshooting

### Config Not Found

If config doesn't exist, create it:
```bash
praisonaippt config init
```

### Invalid YAML Syntax

Check for:
- Proper indentation (2 spaces)
- No tabs (use spaces only)
- Quotes around special characters
- Valid boolean values (`true`/`false`, not `yes`/`no`)

### Credentials Not Working

Verify the path:
```bash
ls -la ~/.praisonaippt/oauth-credentials.json
```

Re-run setup if needed:
```bash
praisonaippt setup-oauth
```

### Config Not Applied

Check priority:
1. CLI arguments override config
2. Verify config syntax is correct
3. Run `praisonaippt config show` to see current values

## Related Documentation

- [OAuth Setup](oauth-setup.md)
- [Google Drive Upload](google-drive-upload.md)
- [CLI Reference](../README.md#complete-cli-options)
