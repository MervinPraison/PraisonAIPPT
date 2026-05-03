#!/usr/bin/env python3
"""
Command-line interface for PraisonAI PPT - PowerPoint Bible Verses Generator.
"""

import argparse
import logging
import sys
import json
from pathlib import Path
from . import __version__
from .loader import load_verses_from_file, get_example_path, list_examples
from .core import create_presentation
from .pdf_converter import PDFOptions, convert_pptx_to_pdf
from .config import load_config, init_config


def _configure_logging(verbose: bool, quiet: bool) -> None:
    """Configure root logger level based on CLI flags. Default: WARNING."""
    if verbose:
        level = logging.DEBUG
    elif quiet:
        level = logging.ERROR
    else:
        level = logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
        force=True,
    )


def parse_arguments():
    """
    Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Create PowerPoint presentations from Bible verses in JSON or YAML format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Use default verses.json
  %(prog)s -i my_verses.json            # Use specific input file
  %(prog)s -i verses.json -o output.pptx  # Specify output file
  %(prog)s -t "My Title"                # Use custom title
  %(prog)s --use-example tamil_verses   # Use built-in example
  %(prog)s --list-examples              # List available examples
        """
    )
    
    parser.add_argument(
        '-i', '--input',
        default='verses.yaml',
        help='Input JSON or YAML file with verses (default: verses.yaml, falls back to verses.json)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output PowerPoint file (auto-generated if not specified)'
    )
    
    parser.add_argument(
        '-t', '--title',
        help='Custom presentation title (overrides JSON title)'
    )
    
    parser.add_argument(
        '--use-example',
        metavar='NAME',
        help='Use a built-in example file (e.g., verses, tamil_verses)'
    )
    
    parser.add_argument(
        '--list-examples',
        action='store_true',
        help='List all available example files'
    )
    
    parser.add_argument(
        '--convert-pdf',
        action='store_true',
        help='Convert the generated PowerPoint to PDF'
    )
    
    parser.add_argument(
        '--pdf-backend',
        choices=['aspose', 'libreoffice', 'auto'],
        default='auto',
        help='PDF conversion backend (default: auto)'
    )
    
    parser.add_argument(
        '--pdf-options',
        help='PDF conversion options as JSON string (e.g., \'{"quality":"high","include_hidden_slides":true}\')'
    )
    
    parser.add_argument(
        '--pdf-output',
        help='Custom PDF output filename (auto-generated if not specified)'
    )
    
    parser.add_argument(
        '--upload-gdrive',
        action='store_true',
        help='Upload the generated PowerPoint to Google Drive'
    )
    
    parser.add_argument(
        '--gdrive-credentials',
        help='Path to Google Drive service account credentials JSON file'
    )
    
    parser.add_argument(
        '--gdrive-folder-id',
        help='Google Drive folder ID to upload to (optional, uploads to root if not specified)'
    )
    
    parser.add_argument(
        '--gdrive-folder-name',
        help='Google Drive folder name to upload to (creates if doesn\'t exist)'
    )
    
    parser.add_argument(
        '--gdrive-date-folders',
        action='store_true',
        help='Create date-based subfolders (e.g., 2024/12/22) within the target folder'
    )
    
    parser.add_argument(
        '--config-init',
        action='store_true',
        help='Initialize configuration file interactively'
    )
    
    parser.add_argument(
        '--config-show',
        action='store_true',
        help='Show current configuration'
    )
    
    parser.add_argument(
        'command',
        nargs='?',
        choices=['convert-pdf', 'convert-json', 'convert-yaml', 'config', 'setup-oauth', 'setup-credentials', 'secure-credentials'],
        help='Command to execute (e.g., convert-pdf, convert-json, convert-yaml, config, setup-oauth)'
    )
    
    parser.add_argument(
        'input_file',
        nargs='?',
        help='Input file for convert-pdf or convert-json command'
    )

    parser.add_argument(
        '--json-output',
        metavar='PATH',
        help='Output JSON file path for convert-json command (default: <input>.json)'
    )

    parser.add_argument(
        '--pretty',
        action='store_true',
        default=True,
        help='Output pretty-printed JSON for convert-json (default: True)'
    )

    parser.add_argument(
        '--no-pretty',
        dest='pretty',
        action='store_false',
        help='Output compact JSON for convert-json'
    )

    parser.add_argument(
        '--output-format',
        choices=['json', 'yaml'],
        default='json',
        help='Output format for convert-json command (default: json)'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable DEBUG-level logging.'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress all but ERROR-level logging.'
    )

    return parser.parse_args()


def parse_pdf_options(options_str: str) -> PDFOptions:
    """Parse PDF options from JSON string"""
    try:
        if not options_str:
            return PDFOptions()
        
        options_dict = json.loads(options_str)
        return PDFOptions(**options_dict)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in PDF options: {e}")
    except TypeError as e:
        raise ValueError(f"Invalid PDF options: {e}")


def handle_convert_json_command(args):
    """Handle convert-json command: extract JSON/YAML dict from a PPTX file."""
    from .pptx_to_json import pptx_to_json

    if not args.input_file:
        print("Error: Input file required for convert-json command")
        print("Usage: praisonaippt convert-json <input.pptx> [--json-output output.json] [--output-format yaml]")
        return 1

    input_path = Path(args.input_file)

    if not input_path.exists():
        print(f"Error: Input file not found: {args.input_file}")
        return 1

    suffix = input_path.suffix.lower()

    if suffix in ['.yaml', '.yml']:
        try:
            import yaml
            with open(input_path, 'r', encoding='utf-8') as yf:
                data = yaml.safe_load(yf)
                
            # Determine output path
            if hasattr(args, 'json_output') and args.json_output:
                output_path = args.json_output
            else:
                output_path = input_path.with_suffix('.json')
                
            pretty = getattr(args, 'pretty', True)
            with open(output_path, 'w', encoding='utf-8') as jf:
                json.dump(data, jf, indent=2 if pretty else None, ensure_ascii=False)
                
            print(f"✓ Converted '{input_path.name}' to '{Path(output_path).name}'")
            return 0
        except Exception as e:
            print(f"Error converting YAML to JSON: {e}")
            return 1

    if suffix not in ['.pptx', '.ppt']:
        print("Error: Input file must be a PowerPoint file (.pptx/.ppt) or a YAML file (.yaml/.yml)")
        return 1

    try:
        # Determine output format
        output_format = getattr(args, 'output_format', 'json') or 'json'
        
        # Determine output path with correct extension
        if hasattr(args, 'json_output') and args.json_output:
            output_path = args.json_output
        else:
            ext = '.yaml' if output_format == 'yaml' else '.json'
            output_path = str(Path(args.input_file).with_suffix(ext))

        pretty = getattr(args, 'pretty', True)

        print(f"Extracting {output_format.upper()} from {args.input_file}...")
        pptx_to_json(args.input_file, output_path=output_path, pretty=pretty, output_format=output_format)
        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error during JSON extraction: {e}")
        return 1


def handle_convert_yaml_command(args):
    """Handle convert-yaml command: convert verses.json to verses.yaml."""
    if not args.input_file:
        print("Error: Input file required for convert-yaml command")
        print("Usage: praisonaippt convert-yaml <input.json>")
        return 1

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input_file}")
        return 1

    if input_path.suffix.lower() != '.json':
        print("Error: Input file must be a JSON file (.json)")
        return 1

    try:
        import yaml
        with open(input_path, 'r', encoding='utf-8') as jf:
            data = json.load(jf)
            
        output_path = input_path.with_suffix('.yaml')
        
        with open(output_path, 'w', encoding='utf-8') as yf:
            yaml.dump(data, yf, allow_unicode=True, sort_keys=False, default_flow_style=False)
            
        print(f"✓ Converted '{input_path.name}' to '{output_path.name}'")
        return 0

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return 1
    except Exception as e:
        print(f"Error during YAML conversion: {e}")
        return 1


def handle_convert_pdf_command(args):
    """Handle standalone convert-pdf command (full parity with --convert-pdf flag)."""
    if not args.input_file:
        print("Error: Input file required for convert-pdf command")
        return 1

    if not Path(args.input_file).exists():
        print(f"Error: Input file not found: {args.input_file}")
        return 1

    if not args.input_file.lower().endswith(('.pptx', '.ppt')):
        print("Error: Input file must be a PowerPoint presentation")
        return 1

    try:
        pdf_options = parse_pdf_options(args.pdf_options)

        if args.pdf_output:
            pdf_path = args.pdf_output
        else:
            pdf_path = str(Path(args.input_file).with_suffix('.pdf'))

        print(f"Converting {args.input_file} to PDF...")
        pdf_result = None
        try:
            pdf_result = convert_pptx_to_pdf(
                args.input_file, pdf_path,
                backend=args.pdf_backend, options=pdf_options)
            print(f"✓ Successfully converted to: {pdf_result}")
        except Exception as primary_err:
            print(f"  Local conversion unavailable ({primary_err}), trying via Google Drive...")
            try:
                pdf_result = _convert_pdf_via_gdrive(args.input_file, pdf_path)
                print(f"✓ PDF created via Google Drive: {pdf_result}")
            except Exception as gdrive_err:
                print(f"Error: PDF conversion failed: {gdrive_err}")
                return 1

        # Upload PDF to Google Drive if requested
        config = load_config()
        if pdf_result and (args.upload_gdrive or config.should_auto_upload_gdrive()):
            handle_gdrive_upload(args.input_file, args, config, pdf_path=pdf_result)

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def handle_setup_oauth():
    """Handle OAuth credentials setup."""
    import subprocess
    from pathlib import Path
    import webbrowser
    
    print("\n" + "=" * 60)
    print("OAuth Setup for Personal Google Drive")
    print("=" * 60)
    print()
    
    config_dir = Path.home() / '.praisonaippt'
    oauth_creds = config_dir / 'oauth-credentials.json'
    
    # Get project ID
    try:
        result = subprocess.run(
            ['gcloud', 'config', 'get-value', 'project'],
            capture_output=True,
            text=True
        )
        project_id = result.stdout.strip()
        
        if not project_id:
            print("Error: No active GCloud project found.")
            print("Please set a project with: gcloud config set project PROJECT_ID")
            return 1
        
        print(f"✓ Using GCloud project: {project_id}")
    except FileNotFoundError:
        print("Error: gcloud CLI not found. Please install Google Cloud SDK.")
        return 1
    
    print()
    
    # Enable Drive API
    print("Enabling Google Drive API...")
    subprocess.run([
        'gcloud', 'services', 'enable', 'drive.googleapis.com',
        f'--project={project_id}'
    ], capture_output=True)
    print("✓ Google Drive API enabled")
    
    print()
    print("Opening Google Cloud Console to create OAuth credentials...")
    print()
    
    # Open browser to credentials page
    credentials_url = f"https://console.cloud.google.com/apis/credentials?project={project_id}"
    webbrowser.open(credentials_url)
    
    print("In the browser that just opened:")
    print()
    print("1. Click 'Create Credentials' > 'OAuth client ID'")
    print("2. If prompted to configure consent screen:")
    print("   a. Click 'Configure Consent Screen'")
    print("   b. User Type: External > Create")
    print("   c. App name: PraisonAI PPT")
    print("   d. User support email: (your email)")
    print("   e. Developer contact: (your email)")
    print("   f. Save and Continue (skip optional fields)")
    print("   g. Add test users: (your email)")
    print("   h. Save and Continue > Back to Dashboard")
    print("   i. Go back to Credentials tab")
    print()
    print("3. Click 'Create Credentials' > 'OAuth client ID'")
    print("4. Application type: Desktop app")
    print("5. Name: PraisonAI PPT Desktop")
    print("6. Click 'Create'")
    print("7. Click 'Download JSON' (or copy the client ID/secret)")
    print()
    
    input("Press Enter after you've downloaded the OAuth credentials JSON file...")
    
    print()
    
    # Try to find the downloaded file automatically
    downloads_dir = Path.home() / 'Downloads'
    if downloads_dir.exists():
        # Look for recently downloaded client_secret files
        import glob
        import os
        pattern = str(downloads_dir / 'client_secret_*.json')
        files = glob.glob(pattern)
        if files:
            # Get most recent
            latest_file = max(files, key=os.path.getctime)
            print(f"Found: {latest_file}")
            use_found = input("Use this file? (y/n): ").strip().lower()
            if use_found == 'y':
                downloaded_file = latest_file
            else:
                downloaded_file = input("Enter the path to the OAuth credentials file: ").strip()
        else:
            downloaded_file = input("Enter the path to the OAuth credentials file: ").strip()
    else:
        downloaded_file = input("Enter the path to the OAuth credentials file: ").strip()
    
    downloaded_file = os.path.expanduser(downloaded_file)
    
    if not Path(downloaded_file).exists():
        print(f"Error: File not found: {downloaded_file}")
        return 1
    
    # Copy to config directory and secure
    config_dir.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy(downloaded_file, oauth_creds)
    oauth_creds.chmod(0o600)
    
    # Remove the downloaded file from Downloads for security
    try:
        Path(downloaded_file).unlink()
        print(f"✓ OAuth credentials moved to: {oauth_creds}")
    except Exception:
        print(f"✓ OAuth credentials saved to: {oauth_creds}")
    
    print("✓ Credentials secured with permissions 600")
    
    # Update config.yaml
    config_file = config_dir / 'config.yaml'
    if config_file.exists():
        print("✓ Updating config.yaml...")
        import yaml
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        if 'gdrive' not in config_data:
            config_data['gdrive'] = {}
        config_data['gdrive']['credentials_path'] = str(oauth_creds)
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
        
        # Secure config file too
        config_file.chmod(0o600)
        print("✓ Config updated and secured")
    
    print()
    print("=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print()
    print(f"OAuth Credentials: {oauth_creds}")
    print()
    print("Next Steps:")
    print("1. Test the upload:")
    print("   praisonaippt -i examples/job_sickness.json --upload-gdrive")
    print()
    print("2. On first run, a browser will open for authentication")
    print("3. Sign in with your Google account")
    print("4. Grant permissions to PraisonAI PPT")
    print("5. The token will be saved for future use")
    print()
    
    return 0


def handle_secure_credentials():
    """Handle securing credentials files with proper permissions."""
    from pathlib import Path
    import shutil
    import sys
    
    print("\n" + "=" * 60)
    print("Secure Credentials Files")
    print("=" * 60)
    print()
    
    config_dir = Path.home() / '.praisonaippt'
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Files to check and secure
    credential_files = [
        'oauth-credentials.json',
        'gdrive-credentials.json',
        'token.pickle',
        'config.yaml'
    ]
    
    issues_found = False
    files_secured = []
    files_moved = []
    
    print("Checking credential files...")
    print()
    
    # Check for credentials in current directory
    cwd = Path.cwd()
    for filename in credential_files:
        # Check in current directory
        cwd_file = cwd / filename
        target_file = config_dir / filename
        
        if cwd_file.exists() and cwd_file != target_file:
            print(f"⚠ Found {filename} in current directory")
            try:
                move = input(f"  Move to {config_dir}? (y/n): ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n  Skipped")
                continue
            if move == 'y':
                shutil.move(str(cwd_file), str(target_file))
                target_file.chmod(0o600)
                files_moved.append(filename)
                print(f"  ✓ Moved and secured: {filename}")
            issues_found = True
        
        # Check permissions in config directory
        if target_file.exists():
            current_perms = target_file.stat().st_mode & 0o777
            if current_perms != 0o600:
                print(f"⚠ {filename} has insecure permissions: {oct(current_perms)}")
                target_file.chmod(0o600)
                files_secured.append(filename)
                print("  ✓ Secured with permissions 600")
                issues_found = True
    
    # Check Downloads folder for common credential files (only if interactive)
    if sys.stdin.isatty():
        downloads_dir = Path.home() / 'Downloads'
        if downloads_dir.exists():
            patterns = [
                'client_secret_*.json',
                '*credentials*.json',
                'token.pickle'
            ]
            
            import glob
            for pattern in patterns:
                files = glob.glob(str(downloads_dir / pattern))
                for file_path in files:
                    file_path = Path(file_path)
                    print(f"⚠ Found potential credential file in Downloads: {file_path.name}")
                    try:
                        move = input(f"  Move to {config_dir}? (y/n): ").strip().lower()
                    except (EOFError, KeyboardInterrupt):
                        print("\n  Skipped")
                        continue
                    if move == 'y':
                        # Determine target name
                        if 'client_secret' in file_path.name:
                            target_name = 'oauth-credentials.json'
                        elif 'credentials' in file_path.name:
                            target_name = 'gdrive-credentials.json'
                        else:
                            target_name = file_path.name
                        
                        target_file = config_dir / target_name
                        shutil.move(str(file_path), str(target_file))
                        target_file.chmod(0o600)
                        files_moved.append(target_name)
                        print(f"  ✓ Moved and secured as: {target_name}")
                    issues_found = True
    
    print()
    print("=" * 60)
    
    if not issues_found:
        print("✓ All credential files are secure!")
        print()
        print("Current status:")
        for filename in credential_files:
            file_path = config_dir / filename
            if file_path.exists():
                perms = file_path.stat().st_mode & 0o777
                print(f"  ✓ {filename}: {oct(perms)}")
    else:
        print("Security Check Complete!")
        print()
        if files_moved:
            print(f"✓ Moved {len(files_moved)} file(s) to secure location")
        if files_secured:
            print(f"✓ Secured {len(files_secured)} file(s) with proper permissions")
    
    print()
    print(f"Secure location: {config_dir}")
    print("All credential files should have permissions: 600 (owner read/write only)")
    print()
    
    return 0


def handle_setup_credentials():
    """Handle service account credentials setup."""
    import subprocess
    from pathlib import Path
    
    print("\n" + "=" * 60)
    print("Google Drive Service Account Setup")
    print("=" * 60)
    print()
    
    config_dir = Path.home() / '.praisonaippt'
    creds_file = config_dir / 'gdrive-credentials.json'
    service_account_name = "praisonaippt-gdrive"
    
    # Get project ID
    try:
        result = subprocess.run(
            ['gcloud', 'config', 'get-value', 'project'],
            capture_output=True,
            text=True
        )
        project_id = result.stdout.strip()
        
        if not project_id:
            print("Error: No active GCloud project found.")
            print("Please set a project with: gcloud config set project PROJECT_ID")
            return 1
        
        print(f"✓ Using GCloud project: {project_id}")
    except FileNotFoundError:
        print("Error: gcloud CLI not found. Please install Google Cloud SDK.")
        return 1
    
    print()
    
    service_account_email = f"{service_account_name}@{project_id}.iam.gserviceaccount.com"
    
    # Check if service account exists
    result = subprocess.run(
        ['gcloud', 'iam', 'service-accounts', 'describe', service_account_email],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Creating service account: {service_account_name}")
        subprocess.run([
            'gcloud', 'iam', 'service-accounts', 'create', service_account_name,
            '--display-name=PraisonAI PPT Google Drive',
            f'--project={project_id}'
        ])
        print("✓ Service account created")
    else:
        print(f"⚠ Service account already exists: {service_account_email}")
    
    print()
    print("Enabling Google Drive API...")
    subprocess.run([
        'gcloud', 'services', 'enable', 'drive.googleapis.com',
        f'--project={project_id}'
    ], capture_output=True)
    print("✓ Google Drive API enabled")
    
    print()
    print("Creating service account key...")
    config_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        'gcloud', 'iam', 'service-accounts', 'keys', 'create', str(creds_file),
        f'--iam-account={service_account_email}',
        f'--project={project_id}'
    ])
    
    # Secure the credentials file
    creds_file.chmod(0o600)
    print(f"✓ Credentials saved to: {creds_file}")
    print("✓ Credentials secured with permissions 600")
    
    # Update config.yaml
    config_file = config_dir / 'config.yaml'
    if config_file.exists():
        print("✓ Updating config.yaml...")
        import yaml
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        if 'gdrive' not in config_data:
            config_data['gdrive'] = {}
        config_data['gdrive']['credentials_path'] = str(creds_file)
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
        
        # Secure config file
        config_file.chmod(0o600)
        print("✓ Config updated and secured")
    else:
        print("Creating config.yaml...")
        config_data = {
            'gdrive': {
                'credentials_path': str(creds_file),
                'folder_name': 'Bible Presentations',
                'use_date_folders': False,
                'date_format': 'YYYY/MM'
            },
            'pdf': {
                'backend': 'auto',
                'quality': 'high',
                'compression': True
            },
            'defaults': {
                'auto_convert_pdf': False,
                'auto_upload_gdrive': False
            }
        }
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
        
        # Secure config file
        config_file.chmod(0o600)
        print("✓ Config created and secured")
    
    print()
    print("=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print()
    print(f"Service Account Email: {service_account_email}")
    print(f"Credentials File: {creds_file}")
    print()
    print("⚠ IMPORTANT: Service accounts cannot upload to personal Drive folders!")
    print()
    print("You have two options:")
    print("1. Use OAuth instead: praisonaippt setup-oauth")
    print("2. Use Google Shared Drive (Workspace only)")
    print()
    print("To share a folder with this service account:")
    print(f"   Share with: {service_account_email}")
    print("   Permission: Editor")
    print()
    
    return 0


def handle_gdrive_upload(output_file, args, config, pdf_path=None):
    """Handle Google Drive upload if requested — uploads PPTX and optionally PDF."""
    should_upload = args.upload_gdrive or config.should_auto_upload_gdrive()

    if not should_upload:
        return

    try:
        from .gdrive_uploader import upload_to_gdrive, is_gdrive_available

        if not is_gdrive_available():
            print("\nWarning: Google Drive dependencies not installed.")
            print("To enable Google Drive upload, install with:")
            print("  pip install praisonaippt[gdrive]")
            return

        credentials_path = args.gdrive_credentials or config.get_gdrive_credentials()

        if not credentials_path:
            print("\nError: Google Drive credentials not configured")
            return

        folder_id   = args.gdrive_folder_id   or config.get_gdrive_folder_id()
        folder_name = args.gdrive_folder_name  or config.get_gdrive_folder_name()
        use_date_folders = args.gdrive_date_folders or config.use_date_folders()
        date_format = config.get_date_format()

        print("\nUploading to Google Drive...")

        # --- Upload PPTX ---
        result = upload_to_gdrive(
            output_file,
            credentials_path=credentials_path,
            folder_id=folder_id,
            folder_name=folder_name,
            use_date_folders=use_date_folders,
            date_format=date_format
        )
        print("✓ Successfully uploaded to Google Drive")
        print(f"  File ID: {result['id']}")
        print(f"  File Name: {result['name']}")
        if 'webViewLink' in result:
            print(f"  View Link: {result['webViewLink']}")

        # --- Upload PDF if provided ---
        if pdf_path and Path(pdf_path).exists():
            pdf_result = upload_to_gdrive(
                pdf_path,
                credentials_path=credentials_path,
                folder_id=folder_id,
                folder_name=folder_name,
                use_date_folders=use_date_folders,
                date_format=date_format
            )
            print("✓ PDF uploaded to Google Drive")
            print(f"  File Name: {pdf_result['name']}")
            if 'webViewLink' in pdf_result:
                print(f"  PDF Link: {pdf_result['webViewLink']}")

    except Exception as e:
        print(f"\nWarning: Google Drive upload failed: {e}")
        print("Presentation was created successfully at:", output_file)


def _convert_pdf_via_gdrive(pptx_path: str, pdf_path: str) -> str:
    """Backward-compat shim. The real implementation lives in pdf_converter."""
    from .pdf_converter import convert_pptx_to_pdf_via_gdrive
    return convert_pptx_to_pdf_via_gdrive(pptx_path, pdf_path)


def main():
    """
    Main entry point for the CLI.
    """
    args = parse_arguments()
    _configure_logging(getattr(args, 'verbose', False), getattr(args, 'quiet', False))

    # Handle config commands
    if args.config_init:
        init_config(interactive=True)
        return 0
    
    if args.config_show:
        config = load_config()
        config.display()
        return 0
    
    # Handle config subcommand
    if args.command == 'config':
        if args.input_file == 'init':
            init_config(interactive=True)
        elif args.input_file == 'show':
            config = load_config()
            config.display()
        else:
            print("Config commands: init, show")
            print("Usage:")
            print("  praisonaippt config init  # Initialize configuration")
            print("  praisonaippt config show  # Show current configuration")
        return 0
    
    # Handle setup-oauth subcommand
    if args.command == 'setup-oauth':
        return handle_setup_oauth()
    
    # Handle setup-credentials subcommand
    if args.command == 'setup-credentials':
        return handle_setup_credentials()
    
    # Handle secure-credentials subcommand
    if args.command == 'secure-credentials':
        return handle_secure_credentials()
    
    # Load configuration
    config = load_config()
    
    # Handle standalone convert-pdf command
    if args.command == 'convert-pdf':
        return handle_convert_pdf_command(args)

    # Handle convert-json command
    if args.command == 'convert-json':
        return handle_convert_json_command(args)
    
    # Handle convert-yaml command
    if args.command == 'convert-yaml':
        return handle_convert_yaml_command(args)
    
    # List examples if requested
    if args.list_examples:
        examples = list_examples()
        if examples:
            print("Available examples:")
            for example in examples:
                print(f"  - {example.replace('.json', '')}")
            print("\nUse with: praisonaippt --use-example <name>")
        else:
            print("No examples found.")
        return 0
    
    # Determine input file
    if args.use_example:
        input_file = get_example_path(args.use_example)
        if not input_file:
            print(f"Error: Example '{args.use_example}' not found.")
            print("Use --list-examples to see available examples.")
            return 1
        print(f"Using example: {args.use_example}")
    else:
        # Resolve default input: try verses.yaml first, then verses.yml, then verses.json
        input_file = args.input
        if input_file == 'verses.yaml' and not Path(input_file).exists():
            for fallback in ['verses.yml', 'verses.json']:
                if Path(fallback).exists():
                    input_file = fallback
                    break
    
    # Load verses data
    print(f"Loading verses from: {input_file}")
    data = load_verses_from_file(input_file)
    
    if not data:
        return 1

    if data.get('auto_upload_gdrive'):
        args.upload_gdrive = True
    
    # Create presentation
    output_file = create_presentation(
        data,
        output_file=args.output,
        custom_title=args.title
    )
    
    if not output_file:
        return 1
    
    pdf_path = None

    # Convert to PDF if requested
    if args.convert_pdf:
        try:
            pdf_options = parse_pdf_options(args.pdf_options)

            if args.pdf_output:
                pdf_path = args.pdf_output
            else:
                pdf_path = str(Path(output_file).with_suffix('.pdf'))

            print("Converting to PDF...")
            try:
                result = convert_pptx_to_pdf(
                    output_file, pdf_path,
                    backend=args.pdf_backend,
                    options=pdf_options
                )
                print(f"✓ PDF created: {result}")
            except Exception as primary_err:
                # Fallback: try Google Drive API conversion
                print(f"  Local conversion unavailable ({primary_err}), trying via Google Drive...")
                try:
                    result = _convert_pdf_via_gdrive(output_file, pdf_path)
                    print(f"✓ PDF created via Google Drive: {result}")
                except Exception as gdrive_err:
                    print(f"Warning: PDF conversion failed: {gdrive_err}")
                    pdf_path = None  # mark as failed so we don't try to upload

        except Exception as e:
            print(f"Warning: PDF conversion failed: {e}")
            pdf_path = None

    # Upload PPTX (and PDF if generated) to Google Drive
    handle_gdrive_upload(output_file, args, config, pdf_path=pdf_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
