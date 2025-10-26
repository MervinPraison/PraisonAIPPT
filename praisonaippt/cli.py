#!/usr/bin/env python3
"""
Command-line interface for PraisonAI PPT - PowerPoint Bible Verses Generator.
"""

import argparse
import sys
from . import __version__
from .loader import load_verses_from_file, get_example_path, list_examples
from .core import create_presentation


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
        '-v', '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    return parser.parse_args()


def main():
    """
    Main entry point for the CLI.
    """
    args = parse_arguments()
    
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
    
    if output_file:
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
