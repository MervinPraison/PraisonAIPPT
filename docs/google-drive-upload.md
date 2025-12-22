# Google Drive Upload

Upload your generated PowerPoint presentations directly to Google Drive using the `--upload-gdrive` option.

## Features

- **Lazy Loading**: Google Drive dependencies are only loaded when needed
- **Service Account Authentication**: Secure authentication using Google service account credentials
- **Folder Management**: Upload to specific folders or create new ones automatically
- **Error Handling**: Graceful fallback if dependencies are not installed

## Installation

Install with Google Drive support:

```bash
pip install praisonaippt[gdrive]
```

Or install all optional features:

```bash
pip install praisonaippt[all]
```

## Setup Google Drive API

### 1. Create a Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Drive API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"

### 2. Create Service Account Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Fill in the service account details and click "Create"
4. Grant the service account appropriate roles (optional)
5. Click "Done"

### 3. Generate JSON Key

1. Click on the created service account
2. Go to the "Keys" tab
3. Click "Add Key" > "Create new key"
4. Select "JSON" format
5. Download the JSON file (keep it secure!)

### 4. Share Google Drive Folder (Optional)

If you want to upload to a specific folder:

1. Create a folder in Google Drive
2. Right-click the folder > "Share"
3. Add the service account email (found in the JSON file)
4. Grant "Editor" permission
5. Copy the folder ID from the URL (e.g., `https://drive.google.com/drive/folders/FOLDER_ID`)

## Usage

### Basic Upload

Upload to Google Drive root:

```bash
praisonaippt -i verses.json --upload-gdrive --gdrive-credentials credentials.json
```

### Upload to Specific Folder by ID

```bash
praisonaippt -i verses.json \
  --upload-gdrive \
  --gdrive-credentials credentials.json \
  --gdrive-folder-id "1a2b3c4d5e6f7g8h9i0j"
```

### Upload to Folder by Name

The tool will search for the folder and create it if it doesn't exist:

```bash
praisonaippt -i verses.json \
  --upload-gdrive \
  --gdrive-credentials credentials.json \
  --gdrive-folder-name "Presentations"
```

### Combined with PDF Conversion

Generate presentation, convert to PDF, and upload to Google Drive:

```bash
praisonaippt -i verses.json \
  --convert-pdf \
  --upload-gdrive \
  --gdrive-credentials credentials.json \
  --gdrive-folder-name "Bible Presentations"
```

## CLI Options

| Option | Description |
|--------|-------------|
| `--upload-gdrive` | Enable Google Drive upload |
| `--gdrive-credentials PATH` | Path to service account credentials JSON file (required) |
| `--gdrive-folder-id ID` | Google Drive folder ID to upload to |
| `--gdrive-folder-name NAME` | Folder name to search/create |

## Programmatic Usage

### Using the Upload Function

```python
from praisonaippt.gdrive_uploader import upload_to_gdrive

# Upload to root
result = upload_to_gdrive(
    'presentation.pptx',
    credentials_path='credentials.json'
)

print(f"Uploaded: {result['webViewLink']}")
```

### Upload to Specific Folder

```python
from praisonaippt.gdrive_uploader import upload_to_gdrive

# Upload to folder by ID
result = upload_to_gdrive(
    'presentation.pptx',
    credentials_path='credentials.json',
    folder_id='1a2b3c4d5e6f7g8h9i0j'
)

# Upload to folder by name (creates if doesn't exist)
result = upload_to_gdrive(
    'presentation.pptx',
    credentials_path='credentials.json',
    folder_name='Presentations'
)
```

### Using the GDriveUploader Class

```python
from praisonaippt.gdrive_uploader import GDriveUploader

# Initialize uploader
uploader = GDriveUploader(credentials_path='credentials.json')

# Create a folder
folder_id = uploader.create_folder('My Presentations')

# Upload file
result = uploader.upload_file('presentation.pptx', folder_id=folder_id)

print(f"File ID: {result['id']}")
print(f"View Link: {result['webViewLink']}")
```

### Check if Dependencies are Available

```python
from praisonaippt.gdrive_uploader import is_gdrive_available

if is_gdrive_available():
    print("Google Drive upload is available")
else:
    print("Install with: pip install praisonaippt[gdrive]")
```

## Lazy Loading

The Google Drive functionality uses lazy loading, which means:

1. **No Import Errors**: The package works even without Google Drive dependencies installed
2. **On-Demand Loading**: Dependencies are only imported when you use `--upload-gdrive`
3. **Helpful Messages**: Clear error messages if dependencies are missing

### Example Error Message

If you try to use `--upload-gdrive` without installing dependencies:

```
Warning: Google Drive dependencies not installed.
To enable Google Drive upload, install with:
  pip install praisonaippt[gdrive]
```

## Troubleshooting

### Authentication Errors

**Error**: `FileNotFoundError: Credentials file not found`

**Solution**: Verify the path to your credentials JSON file is correct.

---

**Error**: `google.auth.exceptions.RefreshError`

**Solution**: 
- Ensure the service account has access to the folder
- Check that the Google Drive API is enabled in your project

### Permission Errors

**Error**: `403 Forbidden`

**Solution**: Share the target folder with the service account email address.

### Missing Dependencies

**Error**: `Missing dependency for Google Drive upload`

**Solution**: Install the required dependencies:
```bash
pip install praisonaippt[gdrive]
```

## Security Best Practices

1. **Never commit credentials**: Add `credentials.json` to `.gitignore`
2. **Use environment variables**: Store credentials path in environment variables
3. **Restrict permissions**: Grant minimal necessary permissions to service account
4. **Rotate keys**: Regularly rotate service account keys

### Using Environment Variables

```bash
export GDRIVE_CREDENTIALS="/path/to/credentials.json"
praisonaippt -i verses.json --upload-gdrive --gdrive-credentials "$GDRIVE_CREDENTIALS"
```

## Examples

### Complete Workflow

```bash
# 1. Generate presentation with custom title
# 2. Convert to PDF
# 3. Upload to Google Drive folder "Bible Study"

praisonaippt -i verses.json \
  -t "Sunday Service - John 3:16" \
  --convert-pdf \
  --upload-gdrive \
  --gdrive-credentials ~/secrets/gdrive-credentials.json \
  --gdrive-folder-name "Bible Study"
```

### Python Script Example

```python
from praisonaippt import create_presentation
from praisonaippt.gdrive_uploader import upload_to_gdrive, is_gdrive_available

# Create presentation
data = {
    "presentation_title": "My Verses",
    "sections": [
        {
            "section": "Faith",
            "verses": [
                {"reference": "John 3:16", "text": "For God so loved the world..."}
            ]
        }
    ]
}

output_file = create_presentation(data)
print(f"Created: {output_file}")

# Upload to Google Drive if available
if is_gdrive_available():
    try:
        result = upload_to_gdrive(
            output_file,
            credentials_path='credentials.json',
            folder_name='Presentations'
        )
        print(f"Uploaded: {result['webViewLink']}")
    except Exception as e:
        print(f"Upload failed: {e}")
else:
    print("Google Drive upload not available")
```

## API Reference

### `upload_to_gdrive()`

Upload a file to Google Drive.

**Parameters:**
- `file_path` (str): Path to the file to upload
- `credentials_path` (str, optional): Path to credentials JSON file
- `credentials_dict` (dict, optional): Credentials as dictionary
- `folder_id` (str, optional): Target folder ID
- `folder_name` (str, optional): Target folder name (creates if doesn't exist)
- `file_name` (str, optional): Custom name for uploaded file

**Returns:**
- `dict`: File information with keys: `id`, `name`, `webViewLink`, `webContentLink`

### `GDriveUploader`

Class for managing Google Drive uploads.

**Methods:**
- `upload_file(file_path, folder_id=None, file_name=None)`: Upload a file
- `create_folder(folder_name, parent_id=None)`: Create a folder
- `get_folder_id_by_name(folder_name, parent_id=None)`: Find folder by name

### `is_gdrive_available()`

Check if Google Drive dependencies are installed.

**Returns:**
- `bool`: True if available, False otherwise
