#!/usr/bin/env python3
"""
Test script for PDF conversion functionality.
"""

import sys
import os
from pathlib import Path

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent))

from praisonaippt.pdf_converter import PDFConverter, PDFOptions, convert_pptx_to_pdf
from praisonaippt.core import create_presentation

def test_pdf_converter():
    """Test the PDF converter functionality"""
    print("Testing PDF Converter...")
    
    # Test 1: Check available backends
    print("\n1. Checking available backends...")
    converter = PDFConverter()
    backends = converter.get_available_backends()
    print(f"Available backends: {backends}")
    
    if not backends:
        print("⚠️  No PDF backends available. Install Aspose.Slides or LibreOffice.")
        return False
    
    # Test 2: Test with sample data
    print("\n2. Creating sample presentation...")
    sample_data = {
        "presentation_title": "PDF Test Presentation",
        "presentation_subtitle": "Testing PDF Conversion",
        "sections": [
            {
                "section": "Test Section",
                "verses": [
                    {
                        "reference": "Test 1:1",
                        "text": "This is a test verse for PDF conversion functionality.",
                        "highlights": ["test", "PDF"]
                    }
                ]
            }
        ]
    }
    
    # Create presentation
    result = create_presentation(sample_data, output_file="test_pdf.pptx")
    if not result:
        print("❌ Failed to create test presentation")
        return False
    
    pptx_file = result if isinstance(result, str) else result.get('pptx')
    print(f"✓ Created test presentation: {pptx_file}")
    
    # Test 3: Convert to PDF
    print("\n3. Converting to PDF...")
    try:
        pdf_file = convert_pptx_to_pdf(pptx_file, "test_output.pdf")
        print(f"✓ Successfully converted to PDF: {pdf_file}")
        
        # Check if file exists
        if os.path.exists(pdf_file):
            file_size = os.path.getsize(pdf_file)
            print(f"✓ PDF file size: {file_size} bytes")
        else:
            print("❌ PDF file was not created")
            return False
            
    except Exception as e:
        print(f"❌ PDF conversion failed: {e}")
        return False
    
    # Test 4: Test with options
    print("\n4. Testing with custom options...")
    try:
        options = PDFOptions(quality='medium', include_hidden_slides=False)
        pdf_file2 = convert_pptx_to_pdf(pptx_file, "test_custom.pdf", options=options)
        print(f"✓ Custom conversion successful: {pdf_file2}")
        
        if os.path.exists(pdf_file2):
            file_size = os.path.getsize(pdf_file2)
            print(f"✓ Custom PDF file size: {file_size} bytes")
        
    except Exception as e:
        print(f"❌ Custom PDF conversion failed: {e}")
    
    # Cleanup
    print("\n5. Cleaning up...")
    for file in ["test_pdf.pptx", "test_output.pdf", "test_custom.pdf"]:
        if os.path.exists(file):
            os.remove(file)
            print(f"✓ Removed {file}")
    
    print("\n✅ PDF conversion test completed successfully!")
    return True

def test_api_integration():
    """Test API integration with PDF conversion"""
    print("\nTesting API Integration...")
    
    sample_data = {
        "presentation_title": "API Integration Test",
        "sections": [
            {
                "section": "Test Section",
                "verses": [
                    {
                        "reference": "API 1:1",
                        "text": "Testing API integration with PDF conversion.",
                        "highlights": ["API", "PDF"]
                    }
                ]
            }
        ]
    }
    
    try:
        # Test with PDF conversion enabled
        result = create_presentation(
            sample_data, 
            output_file="api_test.pptx",
            convert_to_pdf=True
        )
        
        if isinstance(result, dict):
            print("✓ API integration successful:")
            print(f"  PPTX: {result.get('pptx')}")
            print(f"  PDF: {result.get('pdf')}")
            
            # Cleanup
            for file in [result.get('pptx'), result.get('pdf')]:
                if file and os.path.exists(file):
                    os.remove(file)
                    print(f"✓ Removed {file}")
            
            return True
        else:
            print("❌ API integration failed - expected dict return")
            return False
            
    except Exception as e:
        print(f"❌ API integration failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("PDF Conversion Test Suite")
    print("=" * 60)
    
    success = True
    
    # Run tests
    success &= test_pdf_converter()
    success &= test_api_integration()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)
