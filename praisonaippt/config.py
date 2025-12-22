"""
Configuration management for PraisonAI PPT.

This module handles loading and saving configuration from ~/.praisonaippt/config.yaml
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


# Default configuration directory
CONFIG_DIR = Path.home() / '.praisonaippt'
CONFIG_FILE = CONFIG_DIR / 'config.yaml'

# Default configuration
DEFAULT_CONFIG = {
    "gdrive": {
        "credentials_path": None,
        "folder_id": None,
        "folder_name": None,
        "use_date_folders": False,
        "date_format": "YYYY/MM"
    },
    "pdf": {
        "backend": "auto",
        "quality": "high",
        "compression": True
    },
    "defaults": {
        "output_format": "pptx",
        "auto_convert_pdf": False,
        "auto_upload_gdrive": False
    }
}


class Config:
    """Configuration manager for PraisonAI PPT"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Optional custom config file path (defaults to ~/.praisonaippt/config.json)
        """
        self.config_path = config_path or CONFIG_FILE
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or return default config.
        
        Returns:
            Configuration dictionary
        """
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                # Merge with defaults to ensure all keys exist
                return self._merge_with_defaults(config)
            except (yaml.YAMLError, IOError) as e:
                print(f"Warning: Could not load config from {self.config_path}: {e}")
                print("Using default configuration")
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()
    
    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge loaded config with defaults to ensure all keys exist.
        
        Args:
            config: Loaded configuration
        
        Returns:
            Merged configuration
        """
        merged = DEFAULT_CONFIG.copy()
        for section, values in config.items():
            if section in merged and isinstance(values, dict):
                merged[section].update(values)
            else:
                merged[section] = values
        return merged
    
    def save(self) -> bool:
        """
        Save current configuration to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create config directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save configuration in YAML format
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
            
            return True
        except IOError as e:
            print(f"Error: Could not save config to {self.config_path}: {e}")
            return False
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            section: Configuration section (e.g., 'gdrive', 'pdf')
            key: Configuration key
            default: Default value if not found
        
        Returns:
            Configuration value or default
        """
        return self.config.get(section, {}).get(key, default)
    
    def set(self, section: str, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key
            value: Value to set
        """
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
    
    def get_gdrive_credentials(self) -> Optional[str]:
        """
        Get Google Drive credentials path from config.
        
        Returns:
            Credentials path or None
        """
        creds_path = self.get('gdrive', 'credentials_path')
        if creds_path:
            # Expand ~ to home directory
            return os.path.expanduser(creds_path)
        return None
    
    def get_gdrive_folder_id(self) -> Optional[str]:
        """Get Google Drive folder ID from config"""
        return self.get('gdrive', 'folder_id')
    
    def get_gdrive_folder_name(self) -> Optional[str]:
        """Get Google Drive folder name from config"""
        return self.get('gdrive', 'folder_name')
    
    def use_date_folders(self) -> bool:
        """Check if date-based folders should be used"""
        return self.get('gdrive', 'use_date_folders', False)
    
    def get_date_format(self) -> str:
        """Get date format for folder structure"""
        return self.get('gdrive', 'date_format', 'YYYY/MM')
    
    def get_pdf_backend(self) -> str:
        """Get PDF backend from config"""
        return self.get('pdf', 'backend', 'auto')
    
    def get_pdf_quality(self) -> str:
        """Get PDF quality from config"""
        return self.get('pdf', 'quality', 'high')
    
    def get_pdf_compression(self) -> bool:
        """Get PDF compression setting from config"""
        return self.get('pdf', 'compression', True)
    
    def should_auto_convert_pdf(self) -> bool:
        """Check if auto PDF conversion is enabled"""
        return self.get('defaults', 'auto_convert_pdf', False)
    
    def should_auto_upload_gdrive(self) -> bool:
        """Check if auto Google Drive upload is enabled"""
        return self.get('defaults', 'auto_upload_gdrive', False)
    
    def display(self) -> None:
        """Display current configuration"""
        print("\nCurrent Configuration:")
        print("=" * 60)
        print(yaml.dump(self.config, default_flow_style=False, sort_keys=False))
        print("=" * 60)
        print(f"\nConfig file: {self.config_path}")


def init_config(interactive: bool = True) -> Config:
    """
    Initialize configuration with optional interactive setup.
    
    Args:
        interactive: If True, prompt user for configuration values
    
    Returns:
        Config instance
    """
    config = Config()
    
    if interactive:
        print("\n" + "=" * 60)
        print("PraisonAI PPT Configuration Setup")
        print("=" * 60)
        print("\nPress Enter to keep current value or use defaults.\n")
        
        # Google Drive configuration
        print("Google Drive Configuration:")
        print("-" * 40)
        
        current_creds = config.get_gdrive_credentials() or "~/.praisonaippt/gdrive-credentials.json"
        print(f"Current: {current_creds}")
        creds_path = input("Google Drive credentials path (full path or ~/path): ").strip()
        if creds_path:
            config.set('gdrive', 'credentials_path', creds_path)
        
        current_folder = config.get_gdrive_folder_name() or "Bible Presentations"
        print(f"Current: {current_folder}")
        folder_name = input("Default Google Drive folder name: ").strip()
        if folder_name:
            config.set('gdrive', 'folder_name', folder_name)
        
        # PDF configuration
        print("\nPDF Configuration:")
        print("-" * 40)
        
        backend = input("PDF backend (aspose/libreoffice/auto) [auto]: ").strip() or "auto"
        config.set('pdf', 'backend', backend)
        
        quality = input("PDF quality (low/medium/high) [high]: ").strip() or "high"
        config.set('pdf', 'quality', quality)
        
        # Default behaviors
        print("\nDefault Behaviors:")
        print("-" * 40)
        
        auto_pdf = input("Auto-convert to PDF? (yes/no) [no]: ").strip().lower() == 'yes'
        config.set('defaults', 'auto_convert_pdf', auto_pdf)
        
        auto_upload = input("Auto-upload to Google Drive? (yes/no) [no]: ").strip().lower() == 'yes'
        config.set('defaults', 'auto_upload_gdrive', auto_upload)
    
    # Save configuration
    if config.save():
        print(f"\n✓ Configuration saved to: {config.config_path}")
        config.display()
    else:
        print("\n✗ Failed to save configuration")
    
    return config


def load_config() -> Config:
    """
    Load configuration from default location.
    
    Returns:
        Config instance
    """
    return Config()


def get_config_value(section: str, key: str, default: Any = None) -> Any:
    """
    Convenience function to get a config value.
    
    Args:
        section: Configuration section
        key: Configuration key
        default: Default value
    
    Returns:
        Configuration value
    """
    config = load_config()
    return config.get(section, key, default)
