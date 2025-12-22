#!/usr/bin/env python3
"""
Command-line interface for PraisonAI PPT - PowerPoint Bible Verses Generator.
"""

import argparse
import sys
import json
from pathlib import Path
from . import __version__
from .loader import load_verses_from_file, get_example_path, list_examples
from .core import create_presentation
from .pdf_converter import PDFOptions, convert_pptx_to_pdf


def parse_arguments():
    """
    Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Create PowerPoint presentations from Bible verses in JSON format",
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
        default='verses.json',
        help='Input JSON file with verses (default: verses.json)'
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
        'command',
        nargs='?',
        choices=['convert-pdf'],
        help='Command to execute (e.g., convert-pdf)'
    )
    
    parser.add_argument(
        'input_file',
        nargs='?',
        help='Input file for convert-pdf command'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'%(prog)s {__version__}'
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


def handle_convert_pdf_command(args):
    """Handle standalone convert-pdf command"""
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
        # Parse PDF options
        pdf_options = parse_pdf_options(args.pdf_options)
        
        # Determine output path
        if args.pdf_output:
            pdf_path = args.pdf_output
        else:
            pdf_path = str(Path(args.input_file).with_suffix('.pdf'))
        
        # Convert to PDF
        print(f"Converting {args.input_file} to PDF...")
        result = convert_pptx_to_pdf(
            args.input_file,
            pdf_path,
            backend=args.pdf_backend,
            options=pdf_options
        )
        
        print(f"✓ Successfully converted to: {result}")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


def main():
    """
    Main entry point for the CLI.
    """
    args = parse_arguments()
    
    # Handle standalone convert-pdf command
    if args.command == 'convert-pdf':
        return handle_convert_pdf_command(args)
    
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
        input_file = args.input
    
    # Load verses data
    print(f"Loading verses from: {input_file}")
    data = load_verses_from_file(input_file)
    
    if not data:
        return 1
    
    # Create presentation
    output_file = create_presentation(
        data,
        output_file=args.output,
        custom_title=args.title
    )
    
    if not output_file:
        return 1
    
    # Convert to PDF if requested
    if args.convert_pdf:
        try:
            # Parse PDF options
            pdf_options = parse_pdf_options(args.pdf_options)
            
            # Determine PDF output path
            if args.pdf_output:
                pdf_path = args.pdf_output
            else:
                pdf_path = str(Path(output_file).with_suffix('.pdf'))
            
            print("Converting to PDF...")
            result = convert_pptx_to_pdf(
                output_file,
                pdf_path,
                backend=args.pdf_backend,
                options=pdf_options
            )
            
            print(f"✓ PDF created: {result}")
            
        except Exception as e:
            print(f"Warning: PDF conversion failed: {e}")
            print("Presentation was created successfully at:", output_file)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
