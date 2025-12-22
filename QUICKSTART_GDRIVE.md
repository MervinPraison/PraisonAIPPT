# Quick Start: Google Drive Upload

Get started with Google Drive upload in 5 minutes!

## Step 1: Install with Google Drive Support

```bash
pip install praisonaippt[gdrive]
```

## Step 2: Set Up Google Drive Credentials

### Option A: Quick Setup (Recommended for Testing)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable Google Drive API:
   - Navigate to "APIs & Services" > "Library"
   - Search "Google Drive API" → Enable
4. Create Service Account:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Fill in details → Create
5. Download JSON Key:
   - Click on the service account
   - Go to "Keys" tab → "Add Key" → "Create new key"
   - Select JSON → Download
6. Save as `gdrive-credentials.json`

### Option B: Use Environment Variable

```bash
export GDRIVE_CREDENTIALS="/path/to/gdrive-credentials.json"
```

## Step 3: Upload Your First Presentation

### Basic Upload (to root)

```bash
praisonaippt -i verses.json \
  --upload-gdrive \
  --gdrive-credentials gdrive-credentials.json
```

### Upload to Specific Folder

```bash
# By folder name (creates if doesn't exist)
praisonaippt -i verses.json \
  --upload-gdrive \
  --gdrive-credentials gdrive-credentials.json \
  --gdrive-folder-name "Bible Presentations"

# By folder ID
praisonaippt -i verses.json \
  --upload-gdrive \
  --gdrive-credentials gdrive-credentials.json \
  --gdrive-folder-id "1a2b3c4d5e6f7g8h9i0j"
```

### Complete Workflow (PPTX + PDF + Upload)

```bash
praisonaippt -i verses.json \
  --convert-pdf \
  --upload-gdrive \
  --gdrive-credentials gdrive-credentials.json \
  --gdrive-folder-name "Presentations"
```

## Step 4: Python API Usage

```python
from praisonaippt import create_presentation
from praisonaippt.gdrive_uploader import upload_to_gdrive

# Create presentation
data = {
    "presentation_title": "My Verses",
    "sections": [
        {
            "section": "Faith",
            "verses": [
                {"reference": "John 3:16", "text": "For God so loved..."}
            ]
        }
    ]
}

output = create_presentation(data)

# Upload to Google Drive
result = upload_to_gdrive(
    output,
    credentials_path='gdrive-credentials.json',
    folder_name='Presentations'
)

print(f"View: {result['webViewLink']}")
```

## Troubleshooting

### "Google Drive dependencies not installed"

**Solution:**
```bash
pip install praisonaippt[gdrive]
```

### "Credentials file not found"

**Solution:** Verify the path to your credentials file:
```bash
ls -la gdrive-credentials.json
```

### "403 Forbidden" Error

**Solution:** Share the target folder with the service account email (found in credentials JSON):
1. Open Google Drive
2. Right-click folder → Share
3. Add service account email
4. Grant "Editor" permission

## Tips

- **Security**: Never commit `gdrive-credentials.json` to git
- **Folder ID**: Get from URL: `https://drive.google.com/drive/folders/FOLDER_ID`
- **Testing**: Use `--gdrive-folder-name "Test"` for testing
- **Automation**: Use environment variables for credentials path

## Full Documentation

- **Complete Guide**: [`docs/google-drive-upload.md`](docs/google-drive-upload.md)
- **Lazy Loading**: [`docs/lazy-loading.md`](docs/lazy-loading.md)
- **Main README**: [`README.md`](README.md)

## Example Script

Run the included example:
```bash
python examples/gdrive_example.py
```

---

**Need Help?** Check the full documentation or open an issue on GitHub.
