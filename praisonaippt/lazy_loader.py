"""
Lazy loading utility for optional dependencies.

This module provides a mechanism to import optional dependencies only when needed,
avoiding import errors when those dependencies are not installed.
"""

import importlib
from typing import Any


class LazyImportError(ImportError):
    """Custom exception for lazy import failures with helpful messages."""
    
    def __init__(self, module_name: str, feature_name: str, install_extra: str):
        self.module_name = module_name
        self.feature_name = feature_name
        self.install_extra = install_extra
        
        message = (
            f"\n{'='*70}\n"
            f"Missing dependency for {feature_name}\n"
            f"{'='*70}\n"
            f"The '{module_name}' module is required for {feature_name}.\n\n"
            f"To install the required dependencies, run:\n"
            f"  pip install praisonaippt[{install_extra}]\n\n"
            f"Or install manually:\n"
            f"  pip install {module_name}\n"
            f"{'='*70}\n"
        )
        super().__init__(message)


class LazyLoader:
    """
    Lazy loader for optional dependencies.
    
    This class delays the import of a module until it's actually accessed,
    allowing the package to function without optional dependencies installed.
    """
    
    def __init__(self, module_name: str, feature_name: str, install_extra: str):
        """
        Initialize the lazy loader.
        
        Args:
            module_name: Name of the module to import (e.g., 'google.oauth2.service_account')
            feature_name: Human-readable feature name (e.g., 'Google Drive upload')
            install_extra: Extra name for pip install (e.g., 'gdrive')
        """
        self.module_name = module_name
        self.feature_name = feature_name
        self.install_extra = install_extra
        self._module = None
        self._attempted = False
    
    def _load(self):
        """Load the module if not already loaded."""
        if not self._attempted:
            self._attempted = True
            try:
                self._module = importlib.import_module(self.module_name)
            except ImportError:
                raise LazyImportError(
                    self.module_name,
                    self.feature_name,
                    self.install_extra
                )
        return self._module
    
    def __getattr__(self, name: str) -> Any:
        """Get attribute from the loaded module."""
        module = self._load()
        return getattr(module, name)
    
    def __call__(self, *args, **kwargs):
        """Allow calling the module if it's callable."""
        module = self._load()
        return module(*args, **kwargs)


def lazy_import(module_name: str, feature_name: str, install_extra: str) -> LazyLoader:
    """
    Create a lazy loader for an optional module.
    
    Args:
        module_name: Name of the module to import
        feature_name: Human-readable feature name
        install_extra: Extra name for pip install
    
    Returns:
        LazyLoader instance
    
    Example:
        >>> google_auth = lazy_import('google.oauth2.service_account', 'Google Drive upload', 'gdrive')
        >>> # Module is not imported yet
        >>> credentials = google_auth.Credentials.from_service_account_file('key.json')
        >>> # Module is imported only when accessed
    """
    return LazyLoader(module_name, feature_name, install_extra)


def check_optional_dependency(module_name: str) -> bool:
    """
    Check if an optional dependency is available without importing it.
    
    Args:
        module_name: Name of the module to check
    
    Returns:
        True if module is available, False otherwise
    """
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except (ImportError, ModuleNotFoundError, AttributeError, ValueError):
        return False
