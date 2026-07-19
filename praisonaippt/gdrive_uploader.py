"""
Google Drive upload functionality with lazy loading.

This module provides functionality to upload PowerPoint files to Google Drive
using the Google Drive API v3. Dependencies are loaded lazily only when needed.
"""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from .lazy_loader import lazy_import, check_optional_dependency

GOOGLE_DOC_MIME = "application/vnd.google-apps.document"


def is_gdrive_available() -> bool:
    """
    Check if Google Drive dependencies are available.
    
    Returns:
        True if dependencies are installed, False otherwise
    """
    return (
        check_optional_dependency('google.oauth2.service_account') and
        check_optional_dependency('googleapiclient.discovery')
    )


class GDriveUploader:
    """
    Google Drive uploader with lazy loading of dependencies.
    
    This class handles authentication and file upload to Google Drive.
    Dependencies are only loaded when the class is instantiated.
    """
    
    def __init__(self, credentials_path: Optional[str] = None, 
                 credentials_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize the Google Drive uploader.
        
        Args:
            credentials_path: Path to service account JSON credentials file
            credentials_dict: Dictionary containing service account credentials
        
        Note:
            Either credentials_path or credentials_dict must be provided.
            If both are provided, credentials_path takes precedence.
        """
        # Lazy import Google Drive dependencies
        self.service_account = lazy_import(
            'google.oauth2.service_account',
            'Google Drive upload',
            'gdrive'
        )
        self.build = lazy_import(
            'googleapiclient.discovery',
            'Google Drive upload',
            'gdrive'
        ).build
        self.MediaFileUpload = lazy_import(
            'googleapiclient.http',
            'Google Drive upload',
            'gdrive'
        ).MediaFileUpload
        
        # Initialize credentials
        self.credentials = self._get_credentials(credentials_path, credentials_dict)
        self.service = None
    
    def _get_credentials(self, credentials_path: Optional[str], 
                        credentials_dict: Optional[Dict[str, Any]]):
        """
        Get Google Drive API credentials (supports both service account and OAuth).
        
        Args:
            credentials_path: Path to credentials JSON file
            credentials_dict: Dictionary with credentials
        
        Returns:
            Credentials object
        
        Raises:
            ValueError: If neither credentials_path nor credentials_dict is provided
        """
        scopes = ['https://www.googleapis.com/auth/drive']
        
        if credentials_path:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(f"Credentials file not found: {credentials_path}")
            
            # Check if it's OAuth credentials or service account
            import json
            with open(credentials_path, 'r') as f:
                creds_data = json.load(f)
            
            # Service account has 'type': 'service_account'
            # Service accounts have no personal Drive storage quota, so fall back
            # to gcloud Application Default Credentials (user's own Google login)
            if creds_data.get('type') == 'service_account':
                return self._get_adc_credentials(scopes)
            else:
                # OAuth credentials - use installed app flow
                return self._get_oauth_credentials(credentials_path, scopes)
        elif credentials_dict:
            if credentials_dict.get('type') == 'service_account':
                return self._get_adc_credentials(scopes)
            else:
                raise ValueError("OAuth credentials must be provided as a file path")
        else:
            # No credentials provided — try ADC as last resort
            return self._get_adc_credentials(scopes)
    
    def _get_adc_credentials(self, scopes: list):
        """
        Get credentials from gcloud Application Default Credentials (ADC).
        Explicitly loads from ~/.config/gcloud/application_default_credentials.json
        to bypass any GOOGLE_APPLICATION_CREDENTIALS env var (which may point to a
        service account key that has no personal Drive storage quota).
        """
        from google.oauth2.credentials import Credentials as UserCredentials
        from google.auth.transport.requests import Request

        adc_path = os.path.expanduser('~/.config/gcloud/application_default_credentials.json')
        if os.path.exists(adc_path):
            import json
            with open(adc_path) as f:
                adc_data = json.load(f)
            if adc_data.get('type') != 'service_account':
                creds = UserCredentials.from_authorized_user_file(adc_path, scopes)
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                return creds

        # Fallback to google.auth.default (may still use service account)
        import google.auth
        creds, _ = google.auth.default(scopes=scopes)
        return creds

    def _get_oauth_credentials(self, credentials_path: str, scopes: list):
        """
        Get OAuth credentials using installed app flow.
        
        Args:
            credentials_path: Path to OAuth client secrets JSON
            scopes: List of OAuth scopes
        
        Returns:
            Credentials object
        """
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        import pickle
        
        # Token file to store user's access and refresh tokens
        token_path = Path(credentials_path).parent / 'token.pickle'
        
        creds = None
        # Check if we have saved credentials
        if token_path.exists():
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # If credentials don't exist or are invalid, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, scopes)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        return creds
    
    def _get_service(self):
        """Get or create the Google Drive service."""
        if self.service is None:
            self.service = self.build('drive', 'v3', credentials=self.credentials)
        return self.service
    
    def _escape_query_value(self, value: str) -> str:
        """Escape a value for use in a Drive API query string."""
        return value.replace("\\", "\\\\").replace("'", "\\'")

    def _list_drive_items(
        self,
        query: str,
        *,
        order_by: str = "createdTime",
        page_size: int = 100,
    ) -> List[Dict[str, str]]:
        """List Drive items matching a query, with stable ordering."""
        service = self._get_service()
        items: List[Dict[str, str]] = []
        page_token = None
        while True:
            response = service.files().list(
                q=query,
                spaces="drive",
                fields="nextPageToken,files(id,name,createdTime,modifiedTime)",
                pageSize=page_size,
                pageToken=page_token,
                orderBy=order_by,
            ).execute()
            items.extend(response.get("files", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        return items

    def find_file_by_name(self, file_name: str, folder_id: Optional[str] = None) -> Optional[str]:
        """
        Find a file by name in a specific folder.

        When duplicates exist, returns the most recently modified match so
        overwrite updates the active copy in the canonical folder.
        """
        safe_name = self._escape_query_value(file_name)
        query = f"name='{safe_name}' and trashed=false"
        if folder_id:
            query += f" and '{folder_id}' in parents"

        files = self._list_drive_items(query, order_by="modifiedTime desc")
        if files:
            return files[0]["id"]
        return None
    
    def update_file(self, file_id: str, file_path: str) -> Dict[str, str]:
        """
        Update an existing file in Google Drive.
        
        Args:
            file_id: ID of the file to update
            file_path: Path to the new file content
        
        Returns:
            Dictionary with file information
        """
        mime_type = self._get_mime_type(file_path)
        
        # Create media upload
        media = self.MediaFileUpload(
            file_path,
            mimetype=mime_type,
            resumable=True
        )
        
        # Update file
        service = self._get_service()
        file = service.files().update(
            fileId=file_id,
            media_body=media,
            fields='id, name, webViewLink, webContentLink'
        ).execute()
        
        return file
    
    def import_file_as_google_doc(
        self,
        file_path: str,
        folder_id: Optional[str] = None,
        file_name: Optional[str] = None,
        overwrite: bool = True,
    ) -> Dict[str, str]:
        """Import a Markdown/text file as a native Google Doc."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if file_name is None:
            file_name = Path(file_path).stem

        source_mime = self._get_mime_type(file_path)
        if Path(file_path).suffix.lower() in (".md", ".markdown"):
            source_mime = "text/markdown"
        elif Path(file_path).suffix.lower() in (".html", ".htm"):
            source_mime = "text/html"

        media = self.MediaFileUpload(
            file_path,
            mimetype=source_mime,
            resumable=True,
        )
        service = self._get_service()

        if overwrite:
            existing_file_id = self.find_file_by_name(file_name, folder_id)
            if existing_file_id:
                print(f"  Google Doc exists, updating: {file_name}")
                try:
                    return service.files().update(
                        fileId=existing_file_id,
                        media_body=media,
                        fields="id, name, webViewLink, webContentLink, mimeType",
                    ).execute()
                except Exception:
                    service.files().delete(fileId=existing_file_id).execute()
                    media = self.MediaFileUpload(
                        file_path,
                        mimetype=source_mime,
                        resumable=True,
                    )

        file_metadata: Dict[str, Any] = {
            "name": file_name,
            "mimeType": GOOGLE_DOC_MIME,
        }
        if folder_id:
            file_metadata["parents"] = [folder_id]

        return service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, name, webViewLink, webContentLink, mimeType",
        ).execute()

    def upload_file(self, file_path: str, folder_id: Optional[str] = None,
                   file_name: Optional[str] = None, overwrite: bool = True) -> Dict[str, str]:
        """
        Upload a file to Google Drive (or update if exists).
        
        Args:
            file_path: Path to the file to upload
            folder_id: Google Drive folder ID (optional, uploads to root if not provided)
            file_name: Custom name for the uploaded file (optional, uses original name if not provided)
            overwrite: If True, updates existing file instead of creating duplicate (default: True)
        
        Returns:
            Dictionary with file information:
            {
                'id': 'file_id',
                'name': 'file_name',
                'webViewLink': 'https://drive.google.com/...',
                'webContentLink': 'https://drive.google.com/...'
            }
        
        Raises:
            FileNotFoundError: If the file doesn't exist
            Exception: If upload fails
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Get file name
        if file_name is None:
            file_name = Path(file_path).name
        
        # Check if file exists and overwrite is enabled
        if overwrite:
            existing_file_id = self.find_file_by_name(file_name, folder_id)
            if existing_file_id:
                print(f"  File exists, updating: {file_name}")
                return self.update_file(existing_file_id, file_path)
        
        # Determine MIME type
        mime_type = self._get_mime_type(file_path)
        
        # Prepare file metadata
        file_metadata = {
            'name': file_name
        }
        
        # Add parent folder if specified
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        # Create media upload
        media = self.MediaFileUpload(
            file_path,
            mimetype=mime_type,
            resumable=True
        )
        
        # Upload file
        service = self._get_service()
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink, webContentLink'
        ).execute()
        
        return file
    
    def _get_mime_type(self, file_path: str) -> str:
        """
        Get MIME type for a file.
        
        Args:
            file_path: Path to the file
        
        Returns:
            MIME type string
        """
        extension = Path(file_path).suffix.lower()
        mime_types = {
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pdf': 'application/pdf',
            '.json': 'application/json',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.markdown': 'text/markdown',
            '.html': 'text/html',
            '.htm': 'text/html',
        }
        return mime_types.get(extension, 'application/octet-stream')
    
    def _get_folder_ids_by_name(
        self, folder_name: str, parent_id: Optional[str] = None
    ) -> List[str]:
        """Return folder IDs with this name under parent, oldest first."""
        safe_name = self._escape_query_value(folder_name)
        query = (
            f"name='{safe_name}' and mimeType='application/vnd.google-apps.folder' "
            "and trashed=false"
        )
        if parent_id:
            query += f" and '{parent_id}' in parents"

        folders = self._list_drive_items(query, order_by="createdTime")
        return [item["id"] for item in folders]

    def get_folder_id_by_name(self, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """
        Get folder ID by folder name.

        When duplicate folders exist under the same parent, returns the oldest
        (canonical) folder so uploads stay consistent.
        """
        folder_ids = self._get_folder_ids_by_name(folder_name, parent_id)
        return folder_ids[0] if folder_ids else None

    def get_or_create_folder(
        self, folder_name: str, parent_id: Optional[str] = None
    ) -> Tuple[str, bool]:
        """
        Resolve a folder by name, creating it only when missing.

        Re-queries after create to absorb parallel-upload races. If duplicates
        already exist, always uses the oldest folder.
        """
        folder_name = folder_name.strip()
        if not folder_name:
            raise ValueError("folder_name must be non-empty")

        existing = self._get_folder_ids_by_name(folder_name, parent_id)
        if existing:
            if len(existing) > 1:
                print(
                    f"  Note: {len(existing)} folders named '{folder_name}' found; "
                    "using oldest"
                )
            return existing[0], False

        self.create_folder(folder_name, parent_id)

        for delay in (0.15, 0.35, 0.75):
            time.sleep(delay)
            existing = self._get_folder_ids_by_name(folder_name, parent_id)
            if existing:
                if len(existing) > 1:
                    print(
                        f"  Note: {len(existing)} folders named '{folder_name}' found; "
                        "using oldest"
                    )
                return existing[0], True

        raise RuntimeError(f"Failed to resolve folder '{folder_name}' after create")

    def ensure_folder_path(
        self, folder_path: str, parent_id: Optional[str] = None
    ) -> Tuple[str, bool]:
        """
        Ensure a nested folder path exists (e.g. "2026/06").

        Returns:
            (final_folder_id, created_any_segment)
        """
        folders = folder_path.split("/")
        current_parent = parent_id
        created_any = False

        for folder_name in folders:
            folder_name = folder_name.strip()
            if not folder_name:
                continue

            current_parent, created = self.get_or_create_folder(folder_name, current_parent)
            created_any = created_any or created

        if current_parent is None:
            raise RuntimeError(f"Invalid folder path: {folder_path}")
        return current_parent, created_any

    def create_folder_path(self, folder_path: str, parent_id: Optional[str] = None) -> str:
        """Create a nested folder path in Google Drive (e.g., "2024/12/22")."""
        folder_id, _ = self.ensure_folder_path(folder_path, parent_id)
        return folder_id
    
    def create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> str:
        """
        Create a folder in Google Drive.
        
        Args:
            folder_name: Name of the folder to create
            parent_id: Parent folder ID (optional, creates in root if not provided)
        
        Returns:
            Created folder ID
        """
        service = self._get_service()
        
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        folder = service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()
        
        return folder['id']


def google_doc_edit_link(file_id: str) -> str:
    """Return a Google Docs editor URL for a Drive file id."""
    return f"https://docs.google.com/document/d/{file_id}/edit"


def upload_to_gdrive(file_path: str, 
                    credentials_path: Optional[str] = None,
                    credentials_dict: Optional[Dict[str, Any]] = None,
                    folder_id: Optional[str] = None,
                    folder_name: Optional[str] = None,
                    file_name: Optional[str] = None,
                    use_date_folders: bool = False,
                    date_format: str = "YYYY/MM",
                    overwrite: bool = True,
                    as_google_doc: bool = False) -> Dict[str, str]:
    """
    Upload a file to Google Drive (convenience function).
    
    Args:
        file_path: Path to the file to upload
        credentials_path: Path to service account JSON credentials file
        credentials_dict: Dictionary containing service account credentials
        folder_id: Google Drive folder ID (optional)
        folder_name: Google Drive folder name to search/create (optional)
        file_name: Custom name for the uploaded file (optional)
        use_date_folders: If True, creates date-based subfolders (e.g., 2024/12)
        date_format: Date format pattern (YYYY/MM, YYYY-MM, YYYY/MM/DD, etc.)
        overwrite: If True, updates existing file instead of creating duplicate (default: True)
        as_google_doc: Import Markdown/text as a native Google Doc (not a .md file)
    
    Returns:
        Dictionary with file information
    
    Example:
        >>> result = upload_to_gdrive(
        ...     'presentation.pptx',
        ...     credentials_path='credentials.json',
        ...     folder_name='Presentations'
        ... )
        >>> print(f"Uploaded: {result['webViewLink']}")
    """
    uploader = GDriveUploader(credentials_path, credentials_dict)
    
    # Handle folder_name if provided
    target_folder_id = folder_id
    if folder_name and not folder_id:
        target_folder_id, created = uploader.get_or_create_folder(folder_name)
        if created:
            print(f"Created folder: {folder_name}")
        else:
            print(f"Using folder: {folder_name}")

    # Handle date-based folders if enabled
    if use_date_folders:
        now = datetime.now()
        date_path = date_format.replace("YYYY", str(now.year))
        date_path = date_path.replace("MM", f"{now.month:02d}")
        date_path = date_path.replace("DD", f"{now.day:02d}")

        target_folder_id, created = uploader.ensure_folder_path(date_path, target_folder_id)
        if created:
            print(f"Created date folder: {date_path}")
        else:
            print(f"Using date folder: {date_path}")
    
    # Upload file
    if as_google_doc:
        return uploader.import_file_as_google_doc(
            file_path, target_folder_id, file_name, overwrite,
        )
    return uploader.upload_file(file_path, target_folder_id, file_name, overwrite)
