"""
Google Drive upload functionality with lazy loading.

This module provides functionality to upload PowerPoint files to Google Drive
using the Google Drive API v3. Dependencies are loaded lazily only when needed.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from .lazy_loader import lazy_import, check_optional_dependency


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
        Get Google Drive API credentials.
        
        Args:
            credentials_path: Path to credentials JSON file
            credentials_dict: Dictionary with credentials
        
        Returns:
            Credentials object
        
        Raises:
            ValueError: If neither credentials_path nor credentials_dict is provided
        """
        scopes = ['https://www.googleapis.com/auth/drive.file']
        
        if credentials_path:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(f"Credentials file not found: {credentials_path}")
            
            return self.service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=scopes
            )
        elif credentials_dict:
            return self.service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=scopes
            )
        else:
            raise ValueError(
                "Either credentials_path or credentials_dict must be provided.\n"
                "To use Google Drive upload, you need to:\n"
                "1. Create a service account in Google Cloud Console\n"
                "2. Download the JSON credentials file\n"
                "3. Provide the path using --gdrive-credentials option"
            )
    
    def _get_service(self):
        """Get or create the Google Drive service."""
        if self.service is None:
            self.service = self.build('drive', 'v3', credentials=self.credentials)
        return self.service
    
    def upload_file(self, file_path: str, folder_id: Optional[str] = None,
                   file_name: Optional[str] = None) -> Dict[str, str]:
        """
        Upload a file to Google Drive.
        
        Args:
            file_path: Path to the file to upload
            folder_id: Google Drive folder ID (optional, uploads to root if not provided)
            file_name: Custom name for the uploaded file (optional, uses original name if not provided)
        
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
        }
        return mime_types.get(extension, 'application/octet-stream')
    
    def get_folder_id_by_name(self, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """
        Get folder ID by folder name.
        
        Args:
            folder_name: Name of the folder to find
            parent_id: Parent folder ID (optional, searches in root if not provided)
        
        Returns:
            Folder ID if found, None otherwise
        """
        service = self._get_service()
        
        # Build query
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        
        # Search for folder
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        files = results.get('files', [])
        if files:
            return files[0]['id']
        return None
    
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


def upload_to_gdrive(file_path: str, 
                    credentials_path: Optional[str] = None,
                    credentials_dict: Optional[Dict[str, Any]] = None,
                    folder_id: Optional[str] = None,
                    folder_name: Optional[str] = None,
                    file_name: Optional[str] = None) -> Dict[str, str]:
    """
    Upload a file to Google Drive (convenience function).
    
    Args:
        file_path: Path to the file to upload
        credentials_path: Path to service account JSON credentials file
        credentials_dict: Dictionary containing service account credentials
        folder_id: Google Drive folder ID (optional)
        folder_name: Google Drive folder name to search/create (optional)
        file_name: Custom name for the uploaded file (optional)
    
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
        # Try to find existing folder
        target_folder_id = uploader.get_folder_id_by_name(folder_name)
        if not target_folder_id:
            # Create folder if it doesn't exist
            print(f"Creating folder: {folder_name}")
            target_folder_id = uploader.create_folder(folder_name)
    
    # Upload file
    return uploader.upload_file(file_path, target_folder_id, file_name)
