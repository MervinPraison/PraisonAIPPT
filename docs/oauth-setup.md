# OAuth Setup for Google Drive

This guide explains how to set up OAuth authentication to upload presentations to your personal Google Drive.

## Why OAuth?

**Service accounts** cannot upload files to personal Google Drive folders due to storage quota limitations. They can only:
- Upload to Google Shared Drives (Workspace feature)
- Create folders (but not upload files)

**OAuth authentication** allows you to:
- ✅ Upload to your personal Google Drive folders
- ✅ Use your own storage quota
- ✅ Access your existing folders
- ✅ One-time authentication with saved tokens

## Quick Setup

Run the automated setup command:

```bash
praisonaippt setup-oauth
```

This will:
1. Check your Google Cloud project
2. Enable Google Drive API
3. Open your browser to create OAuth credentials
4. Auto-detect the downloaded credentials file
5. Configure everything automatically

## Detailed Steps

### Step 1: Run Setup Command

```bash
praisonaippt setup-oauth
```

Output:
```
============================================================
OAuth Setup for Personal Google Drive
============================================================

✓ Using GCloud project: your-project-id

Enabling Google Drive API...
✓ Google Drive API enabled

Opening Google Cloud Console to create OAuth credentials...
```

### Step 2: Create OAuth Client (In Browser)

The browser will open automatically to:
`https://console.cloud.google.com/apis/credentials?project=your-project-id`

#### First Time Setup (Configure Consent Screen)

If this is your first OAuth client:

1. Click **"Create Credentials"** > **"OAuth client ID"**
2. You'll be prompted to configure the consent screen
3. Click **"Configure Consent Screen"**
4. Choose **"External"** > **"Create"**
5. Fill in required fields:
   - **App name**: `PraisonAI PPT`
   - **User support email**: Your email
   - **Developer contact**: Your email
6. Click **"Save and Continue"**
7. Skip optional scopes > **"Save and Continue"**
8. Add test users:
   - Click **"Add Users"**
   - Enter your email
   - Click **"Add"**
9. Click **"Save and Continue"**
10. Review and go **"Back to Dashboard"**
11. Go back to **"Credentials"** tab

#### Create OAuth Client

1. Click **"Create Credentials"** > **"OAuth client ID"**
2. Application type: **"Desktop app"**
3. Name: `PraisonAI PPT Desktop`
4. Click **"Create"**
5. Click **"Download JSON"**

The file will be downloaded as `client_secret_xxxxx.json`

### Step 3: Complete Setup

Back in the terminal:

```
Press Enter after you've downloaded the OAuth credentials JSON file...
```

Press Enter, and the CLI will:
- Auto-detect the file in your Downloads folder
- Ask: `Found: ~/Downloads/client_secret_xxxxx.json`
- Ask: `Use this file? (y/n):`
- Type `y` and press Enter

Output:
```
✓ OAuth credentials saved to: ~/.praisonaippt/oauth-credentials.json
✓ Updating config.yaml...
✓ Config updated

============================================================
Setup Complete!
============================================================

OAuth Credentials: ~/.praisonaippt/oauth-credentials.json

Next Steps:
1. Test the upload:
   praisonaippt -i examples/job_sickness.json --upload-gdrive

2. On first run, a browser will open for authentication
3. Sign in with your Google account
4. Grant permissions to PraisonAI PPT
5. The token will be saved for future use
```

### Step 4: First Upload (Authentication)

Run your first upload:

```bash
praisonaippt -i examples/job_sickness.json --upload-gdrive
```

A browser window will open asking you to:
1. Sign in to your Google account
2. Review permissions requested by PraisonAI PPT
3. Click **"Allow"**

The authentication token will be saved to `~/.praisonaippt/token.pickle`

### Step 5: Subsequent Uploads

All future uploads will use the saved token automatically:

```bash
praisonaippt -i verses.json --upload-gdrive
```

No browser window will open - it just works!

## Configuration

Your config file (`~/.praisonaippt/config.yaml`) will be updated:

```yaml
gdrive:
  credentials_path: /Users/yourname/.praisonaippt/oauth-credentials.json
  folder_id: 1wolJexKoxxIsEGqjVLdGASIDhNazNkit  # Optional
  folder_name: Bible Presentations              # Optional
  use_date_folders: true                        # Optional
  date_format: YYYY/MM                          # Optional
```

## Files Created

| File | Purpose |
|------|---------|
| `~/.praisonaippt/oauth-credentials.json` | OAuth client credentials |
| `~/.praisonaippt/token.pickle` | Saved authentication token |
| `~/.praisonaippt/config.yaml` | Configuration file |

## Token Refresh

The OAuth token will automatically refresh when it expires. You don't need to re-authenticate unless:
- You delete `token.pickle`
- You revoke access in Google account settings
- The token expires and refresh fails

## Troubleshooting

### Browser Doesn't Open

Manually open the URL shown in the terminal:
```
https://console.cloud.google.com/apis/credentials?project=your-project-id
```

### Can't Find Downloaded File

Manually specify the path:
```
Enter the path to the OAuth credentials file: ~/Downloads/client_secret_xxxxx.json
```

### Permission Denied Error

Make sure you:
1. Signed in with the correct Google account
2. Granted all requested permissions
3. Added your email as a test user in the consent screen

### Token Expired

Delete the token and re-authenticate:
```bash
rm ~/.praisonaippt/token.pickle
praisonaippt -i verses.json --upload-gdrive
```

A new browser window will open for re-authentication.

## Security Notes

- OAuth credentials are stored locally in `~/.praisonaippt/`
- Tokens are saved with restricted permissions (600)
- Never share your `oauth-credentials.json` or `token.pickle` files
- Tokens can be revoked at: https://myaccount.google.com/permissions

## Comparison: OAuth vs Service Account

| Feature | OAuth | Service Account |
|---------|-------|-----------------|
| Personal Drive | ✅ Yes | ❌ No (quota error) |
| Shared Drive | ✅ Yes | ✅ Yes |
| Setup Complexity | Medium | Easy |
| Authentication | Browser (one-time) | None |
| Token Refresh | Automatic | N/A |
| Best For | Personal use | Automation/Workspace |

## Next Steps

- [Configuration Guide](configuration.md)
- [Google Drive Upload](google-drive-upload.md)
- [CLI Reference](../README.md#complete-cli-options)
