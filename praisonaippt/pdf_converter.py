"""
PDF Converter Module for PraisonAI PPT

This module provides PPTX to PDF conversion functionality with multiple backends.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass
import logging

# Setup logging
logger = logging.getLogger(__name__)


@dataclass
class PDFOptions:
    """PDF conversion configuration options"""
    backend: str = 'auto'                    # 'aspose', 'libreoffice', 'auto'
    quality: str = 'high'                    # 'low', 'medium', 'high'
    include_hidden_slides: bool = False
    password_protect: bool = False
    password: Optional[str] = None
    compression: bool = True
    notes_pages: bool = False
    slide_range: Optional[Tuple[int, int]] = None
    compliance: Optional[str] = None         # 'PDF/A', 'PDF/UA'
    
    def __post_init__(self):
        """Validate options after initialization"""
        if self.quality not in ['low', 'medium', 'high']:
            raise ValueError(f"Invalid quality: {self.quality}")
        if self.backend not in ['aspose', 'libreoffice', 'auto']:
            raise ValueError(f"Invalid backend: {self.backend}")


class PDFConverter:
    """Handles PPTX to PDF conversion with multiple backends"""
    
    def __init__(self, backend: str = 'auto', config: Optional[Dict[str, Any]] = None):
        """
        Initialize PDF converter
        
        Args:
            backend: Conversion backend ('aspose', 'libreoffice', 'auto')
            config: Additional configuration options
        """
        self.backend = backend
        self.config = config or {}
        self._available_backends = self._detect_backends()
        
        # Select appropriate backend
        if backend == 'auto':
            self._active_backend = self._select_best_backend()
        else:
            if backend not in self._available_backends:
                raise ValueError(f"Backend '{backend}' is not available")
            self._active_backend = backend
    
    def _detect_backends(self) -> List[str]:
        """Detect available conversion backends"""
        available = []
        
        # Check for Aspose.Slides
        if self._check_aspose_available():
            available.append('aspose')
            logger.info("Aspose.Slides backend is available")
        
        # Check for LibreOffice
        if self._check_libreoffice_available():
            available.append('libreoffice')
            logger.info("LibreOffice backend is available")
        
        if not available:
            logger.warning("No PDF conversion backends available")
        
        return available
    
    def _check_aspose_available(self) -> bool:
        """Check if Aspose.Slides is available"""
        try:
            import importlib.util
            spec = importlib.util.find_spec("aspose.slides")
            return spec is not None
        except ImportError:
            return False
    
    def _check_libreoffice_available(self) -> bool:
        """Check if LibreOffice is available on the system"""
        system = platform.system().lower()
        
        if system == 'windows':
            # Check common Windows paths
            paths = [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
                r"C:\Program Files\LibreOffice\program\libreoffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\libreoffice.exe"
            ]
        elif system == 'darwin':  # macOS
            paths = [
                "/Applications/LibreOffice.app/Contents/MacOS/soffice",
                "/Applications/LibreOffice.app/Contents/MacOS/libreoffice"
            ]
        else:  # Linux
            paths = [
                "/usr/bin/libreoffice",
                "/usr/bin/soffice",
                "/opt/libreoffice/program/soffice",
                "/usr/lib/libreoffice/program/soffice"
            ]
        
        for path in paths:
            if os.path.exists(path):
                self._libreoffice_path = path
                return True
        
        # Try to find in PATH
        try:
            subprocess.run(['libreoffice', '--version'], 
                         capture_output=True, check=True, timeout=5)
            self._libreoffice_path = 'libreoffice'
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return False
    
    def _select_best_backend(self) -> str:
        """Select the best available backend"""
        if 'aspose' in self._available_backends:
            return 'aspose'
        elif 'libreoffice' in self._available_backends:
            return 'libreoffice'
        else:
            raise RuntimeError("No PDF conversion backends available")
    
    def get_available_backends(self) -> List[str]:
        """Return list of available conversion backends"""
        return self._available_backends.copy()
    
    def convert_to_pdf(self, pptx_path: str, pdf_path: Optional[str] = None, 
                      options: Optional[PDFOptions] = None) -> str:
        """
        Convert PPTX file to PDF
        
        Args:
            pptx_path: Path to input PPTX file
            pdf_path: Path to output PDF file (optional)
            options: PDF conversion options
            
        Returns:
            Path to generated PDF file
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            RuntimeError: If conversion fails
        """
        # Validate input
        if not os.path.exists(pptx_path):
            raise FileNotFoundError(f"Input file not found: {pptx_path}")
        
        if not pptx_path.lower().endswith(('.pptx', '.ppt')):
            raise ValueError("Input file must be a PowerPoint presentation")
        
        # Generate output path if not provided
        if pdf_path is None:
            pdf_path = str(Path(pptx_path).with_suffix('.pdf'))
        
        # Use provided options or defaults
        if options is None:
            options = PDFOptions()
        
        # Convert using selected backend
        if self._active_backend == 'aspose':
            return self._convert_with_aspose(pptx_path, pdf_path, options)
        elif self._active_backend == 'libreoffice':
            return self._convert_with_libreoffice(pptx_path, pdf_path, options)
        else:
            raise RuntimeError(f"Backend '{self._active_backend}' is not implemented")
    
    def _convert_with_aspose(self, pptx_path: str, pdf_path: str, options: PDFOptions) -> str:
        """Convert using Aspose.Slides backend"""
        try:
            import aspose.slides as slides
            import aspose.slides.export as export
        except ImportError:
            raise RuntimeError("Aspose.Slides is not installed")
        
        logger.info(f"Converting {pptx_path} to PDF using Aspose.Slides")
        
        try:
            # Load presentation
            presentation = slides.Presentation(pptx_path)
            
            # Configure PDF options
            pdf_options = export.PdfOptions()
            
            # Apply quality settings
            if options.quality == 'low':
                pdf_options.jpeg_quality = 50
                pdf_options.compress_images = True
            elif options.quality == 'medium':
                pdf_options.jpeg_quality = 75
                pdf_options.compress_images = True
            else:  # high
                pdf_options.jpeg_quality = 90
                pdf_options.compress_images = options.compression
            
            # Include hidden slides if requested
            pdf_options.show_hidden_slides = options.include_hidden_slides
            
            # Password protection
            if options.password_protect and options.password:
                pdf_options.password = options.password
            
            # Compliance settings
            if options.compliance:
                if options.compliance == 'PDF/A':
                    pdf_options.compliance = export.PdfCompliance.PDF_A1A
                elif options.compliance == 'PDF/UA':
                    pdf_options.compliance = export.PdfCompliance.PDF_UA1
            
            # Slide range
            if options.slide_range:
                start, end = options.slide_range
                slides_to_convert = []
                for i in range(start - 1, min(end, len(presentation.slides))):
                    slides_to_convert.append(presentation.slides[i])
                
                # Convert specific slides
                temp_presentation = slides.Presentation()
                for slide in slides_to_convert:
                    temp_presentation.slides.add_clone(slide)
                temp_presentation.save(pdf_path, export.SaveFormat.PDF, pdf_options)
                temp_presentation.dispose()
            else:
                # Convert all slides
                presentation.save(pdf_path, export.SaveFormat.PDF, pdf_options)
            
            presentation.dispose()
            
            logger.info(f"Successfully converted to {pdf_path}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Aspose conversion failed: {str(e)}")
            raise RuntimeError(f"PDF conversion failed: {str(e)}")
    
    def _convert_with_libreoffice(self, pptx_path: str, pdf_path: str, options: PDFOptions) -> str:
        """Convert using LibreOffice backend"""
        logger.info(f"Converting {pptx_path} to PDF using LibreOffice")
        
        try:
            # Prepare output directory
            output_dir = os.path.dirname(pdf_path) or '.'
            
            # Build command
            cmd = [self._libreoffice_path, '--headless', '--convert-to', 'pdf']
            
            # Add output directory
            cmd.extend(['--outdir', output_dir])
            
            # Add input file
            cmd.append(pptx_path)
            
            # Execute conversion
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                logger.error(f"LibreOffice conversion failed: {result.stderr}")
                raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")
            
            # Check if output file was created
            expected_pdf = os.path.join(output_dir, Path(pptx_path).stem + '.pdf')
            if os.path.exists(expected_pdf):
                # Move to desired location if different
                if expected_pdf != pdf_path:
                    import shutil
                    shutil.move(expected_pdf, pdf_path)
                
                logger.info(f"Successfully converted to {pdf_path}")
                return pdf_path
            else:
                raise RuntimeError("LibreOffice did not generate output file")
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("LibreOffice conversion timed out")
        except Exception as e:
            logger.error(f"LibreOffice conversion failed: {str(e)}")
            raise RuntimeError(f"PDF conversion failed: {str(e)}")


def convert_pptx_to_pdf(pptx_path: str, pdf_path: Optional[str] = None, 
                        backend: str = 'auto', options: Optional[PDFOptions] = None) -> str:
    """
    Convenience function to convert PPTX to PDF
    
    Args:
        pptx_path: Path to input PPTX file
        pdf_path: Path to output PDF file (optional)
        backend: Conversion backend to use
        options: PDF conversion options
        
    Returns:
        Path to generated PDF file
    """
    converter = PDFConverter(backend=backend)
    return converter.convert_to_pdf(pptx_path, pdf_path, options)


# Example usage and testing
if __name__ == "__main__":
    # Simple test
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        
        try:
            result = convert_pptx_to_pdf(input_file, output_file)
            print(f"Successfully converted to: {result}")
        except Exception as e:
            print(f"Conversion failed: {e}")
    else:
        print("Usage: python pdf_converter.py <input.pptx> [output.pdf]")
