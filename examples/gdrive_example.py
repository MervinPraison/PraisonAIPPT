#!/usr/bin/env python3
"""
Example script demonstrating Google Drive upload with lazy loading.

This script shows how to:
1. Create a PowerPoint presentation
2. Check if Google Drive upload is available
3. Upload to Google Drive if dependencies are installed
4. Handle missing dependencies gracefully
"""

from praisonaippt import create_presentation
from praisonaippt.lazy_loader import check_optional_dependency


def main():
    # Sample verse data
    data = {
        "presentation_title": "Faith and Hope",
        "presentation_subtitle": "Selected Verses",
        "sections": [
            {
                "section": "Faith",
                "verses": [
                    {
                        "reference": "Hebrews 11:1 (NIV)",
                        "text": "Now faith is confidence in what we hope for and assurance about what we do not see."
                    },
                    {
                        "reference": "2 Corinthians 5:7 (NIV)",
                        "text": "For we live by faith, not by sight."
                    }
                ]
            },
            {
                "section": "Hope",
                "verses": [
                    {
                        "reference": "Romans 15:13 (NIV)",
                        "text": "May the God of hope fill you with all joy and peace as you trust in him."
                    }
                ]
            }
        ]
    }
    
    # Create presentation
    print("Creating presentation...")
    output_file = create_presentation(data, output_file="faith_and_hope.pptx")
    
    if not output_file:
        print("Failed to create presentation")
        return 1
    
    print("Created: " + output_file)
    
    # Check if Google Drive upload is available
    if check_optional_dependency('google.oauth2.service_account'):
        print("\nGoogle Drive upload is available")
        print("To upload, use:")
        print("  praisonaippt -i verses.json --upload-gdrive --gdrive-credentials credentials.json")
        
        # Example of programmatic upload (commented out - requires credentials)
        """
        from praisonaippt.gdrive_uploader import upload_to_gdrive
        
        try:
            result = upload_to_gdrive(
                output_file,
                credentials_path='credentials.json',
                folder_name='Presentations'
            )
            print(f"✓ Uploaded to Google Drive: {result['webViewLink']}")
        except Exception as e:
            print(f"Upload failed: {e}")
        """
    else:
        print("\n⚠ Google Drive upload not available")
        print("To enable Google Drive upload:")
        print("  pip install praisonaippt[gdrive]")
        print("\nThen set up service account credentials:")
        print("  1. Go to https://console.cloud.google.com/")
        print("  2. Create a service account")
        print("  3. Download credentials JSON")
        print("  4. Use --gdrive-credentials option")
    
    return 0


if __name__ == "__main__":
    exit(main())
