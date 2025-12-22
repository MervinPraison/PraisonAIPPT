"""
Tests for lazy loading functionality.
"""

import pytest
from praisonaippt.lazy_loader import (
    lazy_import,
    check_optional_dependency,
    LazyImportError
)


def test_check_optional_dependency_builtin():
    """Test checking for a built-in module."""
    assert check_optional_dependency('os') is True
    assert check_optional_dependency('sys') is True


def test_check_optional_dependency_nonexistent():
    """Test checking for a non-existent module."""
    assert check_optional_dependency('nonexistent_module_xyz') is False


def test_lazy_import_builtin():
    """Test lazy importing a built-in module."""
    os_module = lazy_import('os', 'OS module', 'builtin')
    
    # Module should not be loaded yet
    assert os_module._module is None
    
    # Access an attribute to trigger loading
    path = os_module.path
    
    # Module should now be loaded
    assert os_module._module is not None
    assert hasattr(path, 'join')


def test_lazy_import_error():
    """Test lazy import error for missing module."""
    missing_module = lazy_import(
        'nonexistent_module_xyz',
        'Test Feature',
        'test-extra'
    )
    
    # Should not raise error on creation
    assert missing_module is not None
    
    # Should raise LazyImportError when accessed
    with pytest.raises(LazyImportError) as exc_info:
        _ = missing_module.some_attribute
    
    # Check error attributes
    assert exc_info.value.module_name == 'nonexistent_module_xyz'
    assert exc_info.value.feature_name == 'Test Feature'
    assert exc_info.value.install_extra == 'test-extra'
    assert 'pip install praisonaippt[test-extra]' in str(exc_info.value)


def test_lazy_import_multiple_access():
    """Test that lazy import only loads module once."""
    json_module = lazy_import('json', 'JSON module', 'builtin')
    
    # First access
    _ = json_module.dumps
    first_module = json_module._module
    
    # Second access
    _ = json_module.loads
    second_module = json_module._module
    
    # Should be the same module instance
    assert first_module is second_module


def test_gdrive_availability():
    """Test Google Drive availability check."""
    from praisonaippt.gdrive_uploader import is_gdrive_available
    
    # Should return False if dependencies not installed
    # (unless they happen to be installed in test environment)
    result = is_gdrive_available()
    assert isinstance(result, bool)


def test_lazy_loader_no_premature_import():
    """Test that lazy loader doesn't import on initialization."""
    import sys
    
    # Create lazy loader for a module that's not imported yet
    lazy_mod = lazy_import('urllib.parse', 'URL parsing', 'builtin')
    
    # The lazy loader itself shouldn't trigger import
    assert lazy_mod._module is None
    
    # Now access it
    _ = lazy_mod.urlparse
    
    # Now it should be imported
    assert lazy_mod._module is not None
    assert 'urllib.parse' in sys.modules


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
