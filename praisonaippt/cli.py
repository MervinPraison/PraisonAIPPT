#!/usr/bin/env python3
"""
Command-line interface for PraisonAI PPT - PowerPoint Bible Verses Generator.
"""

import argparse
import logging
import sys
import json
from pathlib import Path
from typing import Optional
from . import __version__
from .exceptions import SchemaError
from .loader import load_verses_from_file, get_example_path, list_examples
from .template_resolver import list_templates, resolve_template_style
from .schema import validate_verses
from .core import create_presentation
from .list_slides import print_slide_outline
from .pdf_converter import PDFOptions, convert_pptx_to_pdf
from .video_exporter import VideoOptions, convert_pptx_to_video, convert_deck_to_video, resolve_video_backend
from .video_sidecar import load_deck_sidecar
from .slide_images import SlideImageOptions, export_pptx_slide_jpegs, default_slide_images_dir
from .ffmpeg_composer import check_video_tools, print_tool_check_report, pick_video_encoder
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
  %(prog)s --list-templates             # List style theme templates
  %(prog)s -i deck.yaml --template sermon-dark
  %(prog)s template sermon-gold          # Show resolved theme YAML
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
        '--list-templates',
        action='store_true',
        help='List all available style theme templates'
    )

    parser.add_argument(
        '--template',
        metavar='NAME',
        help='Apply a style theme template (e.g. sermon-dark, sermon-gold)'
    )
    
    parser.add_argument(
        '--convert-pdf',
        action='store_true',
        help='Convert the generated PowerPoint to PDF'
    )

    parser.add_argument(
        '--convert-video',
        action='store_true',
        help='Convert the generated PowerPoint to MP4 video'
    )

    parser.add_argument(
        '--video-output',
        help='Custom MP4 output filename (auto-generated if not specified)'
    )

    parser.add_argument(
        '--video-backend',
        choices=['compositor', 'auto', 'powerpoint'],
        default=None,
        help='Video export backend (default: compositor or video_export.backend in YAML)'
    )

    parser.add_argument(
        '--video-preset',
        choices=['draft', 'standard', 'high', '4k'],
        default=None,
        help='Video quality preset (default: standard or video_export.preset in YAML)'
    )

    parser.add_argument(
        '--narration-mode',
        choices=['fixed', 'audio_file', 'avatar', 'tts', 'auto'],
        default=None,
        help='Narration timing mode (default: fixed or video_export.narration_mode in YAML)'
    )

    parser.add_argument(
        '--video-options',
        help='Video export options as JSON string'
    )

    parser.add_argument(
        '--slide-range',
        metavar='START-END',
        help='Export only slides in range (e.g. 1-5)'
    )

    parser.add_argument(
        '--keep-temp',
        action='store_true',
        help='Keep temporary video export files for debugging'
    )

    parser.add_argument(
        '--check',
        action='store_true',
        help='Check video export dependencies (use with convert-video)'
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
        '--export-slide-jpegs',
        action='store_true',
        help='Export each slide as a JPEG image (requires pdftoppm / Poppler)'
    )

    parser.add_argument(
        '--slide-images-dir',
        metavar='DIR',
        help='Output folder for slide JPEGs (default: <pptx_stem>_slides/)'
    )

    parser.add_argument(
        '--slide-images-dpi',
        type=int,
        default=192,
        help='DPI for slide JPEG rasterisation (default: 192)'
    )

    parser.add_argument(
        '--slide-images-quality',
        type=int,
        default=90,
        metavar='1-100',
        help='JPEG quality for slide images (default: 90)'
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
        choices=['convert-pdf', 'convert-video', 'convert-json', 'convert-yaml', 'transcript-to-yaml', 'list-slides', 'export-slide-jpegs', 'config', 'template', 'setup-oauth', 'setup-credentials', 'secure-credentials'],
        help='Command to execute (e.g., list-slides, convert-pdf, convert-video, export-slide-jpegs, template, config)'
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

    parser.add_argument(
        '--no-list-slides',
        action='store_true',
        help='Do not print slide outline after building a presentation'
    )

    parser.add_argument(
        '--transcript-mode',
        choices=['full', 'thematic', 'both'],
        default=None,
        help='Deck variant for transcript-to-yaml (default: both when no --variants)',
    )

    parser.add_argument(
        '--transcript-audio',
        metavar='PATH',
        help='Audio file for silence/emphasis alignment (transcript-to-yaml)',
    )

    parser.add_argument(
        '--align',
        metavar='MODES',
        help='Comma-separated alignment modes: silence, emphasis, karaoke',
    )

    parser.add_argument(
        '--transcript-title',
        metavar='TEXT',
        default='AI Agents: A Serious Upgrade',
        help='Presentation title for transcript-to-yaml',
    )

    parser.add_argument(
        '--avatar-video',
        metavar='PATH',
        default='examples/heygen-article-50590.mp4',
        help='Default avatar video path for generated deck',
    )

    parser.add_argument(
        '--narration-audio',
        metavar='PATH',
        default='examples/short-script-50590.mp3',
        help='Default narration audio path for generated deck',
    )

    parser.add_argument(
        '--variants',
        metavar='NAMES',
        help='Comma-separated media variants for transcript-to-yaml (or "all")',
    )

    return parser.parse_args()


def handle_template_show_command(template_name):
    """Print fully resolved slide_style for a theme template."""
    if not template_name:
        print("Error: Template name required")
        print("Usage: praisonaippt template <name>")
        return 1
    try:
        resolved = resolve_template_style(template_name)
    except SchemaError as e:
        print(f"Error: {e}")
        return 1
    import yaml
    print(yaml.dump(resolved, allow_unicode=True, sort_keys=False, default_flow_style=False))
    return 0


def handle_list_slides_command(args):
    """Handle list-slides command: print numbered slide outline from a PPTX."""
    if not args.input_file:
        print("Error: Input file required for list-slides command")
        print("Usage: praisonaippt list-slides <file.pptx>")
        return 1
    return print_slide_outline(args.input_file)


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


def parse_video_options(args, data: Optional[dict] = None) -> VideoOptions:
    """Build VideoOptions from CLI flags, optional JSON, and deck YAML."""
    opts = VideoOptions()
    if data and data.get("video_export"):
        opts = VideoOptions.from_dict(data["video_export"], data)
    if getattr(args, "video_options", None):
        opts = VideoOptions.from_dict(json.loads(args.video_options), data)
    if getattr(args, "video_backend", None) is not None:
        opts.backend = args.video_backend
    if getattr(args, "video_preset", None) is not None:
        opts.preset = args.video_preset
        if opts.preset in {"draft", "standard", "high", "4k"}:
            from .video_exporter import _PRESETS
            p = _PRESETS[opts.preset]
            opts.width, opts.height, opts.fps, opts.dpi = (
                p["width"], p["height"], p["fps"], p["dpi"],
            )
    if getattr(args, "narration_mode", None) is not None:
        opts.narration_mode = args.narration_mode
    if getattr(args, "video_output", None):
        opts.output_path = args.video_output
    if getattr(args, "keep_temp", False):
        opts.keep_temp = True
    sr = getattr(args, "slide_range", None)
    if sr:
        parts = sr.split("-", 1)
        if len(parts) == 2:
            opts.slide_range = (int(parts[0]), int(parts[1]))
    return opts


def parse_slide_image_options(args) -> SlideImageOptions:
    """Build SlideImageOptions from CLI flags."""
    opts = SlideImageOptions(
        dpi=max(72, int(getattr(args, "slide_images_dpi", 192) or 192)),
        jpeg_quality=max(1, min(int(getattr(args, "slide_images_quality", 90) or 90), 100)),
        keep_pdf=bool(getattr(args, "convert_pdf", False)),
    )
    sr = getattr(args, "slide_range", None)
    if sr:
        parts = sr.split("-", 1)
        if len(parts) == 2:
            opts.slide_range = (int(parts[0]), int(parts[1]))
    return opts


def handle_export_slide_jpegs_command(args, *, pptx_path: Optional[str] = None, pdf_path: Optional[str] = None) -> int:
    """Export JPEG for each slide from a PPTX (standalone command or build flag)."""
    inp = pptx_path or args.input_file
    if not inp:
        print("Error: Input PPTX required for export-slide-jpegs")
        print("Usage: praisonaippt export-slide-jpegs deck.pptx [--slide-images-dir out/]")
        return 1
    if not Path(inp).is_file():
        print(f"Error: File not found: {inp}")
        return 1
    out_dir = getattr(args, "slide_images_dir", None) or str(default_slide_images_dir(inp))
    opts = parse_slide_image_options(args)
    if pdf_path and Path(pdf_path).is_file():
        opts.keep_pdf = True
    print(f"Exporting slide JPEGs from {inp} …")
    try:
        paths = export_pptx_slide_jpegs(
            inp,
            out_dir,
            pdf_path=pdf_path if pdf_path and Path(pdf_path).is_file() else None,
            options=opts,
            pdf_backend=getattr(args, "pdf_backend", "auto"),
            pdf_options=parse_pdf_options(getattr(args, "pdf_options", None)),
        )
    except Exception as e:
        print(f"Error: Slide JPEG export failed: {e}")
        return 1
    print(f"✓ {len(paths)} slide JPEG(s) in {out_dir}")
    for p in paths:
        print(f"  {p}")
    return 0


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

            try:
                data = validate_verses(data)
            except SchemaError as e:
                print(f"Error: Invalid schema in '{input_path}': {e}")
                return 1

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


def handle_transcript_to_yaml_command(args):
    """Generate HeyGen article deck YAML from Whisper transcript JSON."""
    from .transcript_loader import (
        generate_decks,
        generate_media_variants,
        load_whisper_json,
        build_deck_yaml,
        write_deck_yaml,
        MEDIA_VARIANTS,
    )
    from .audio_align import align_deck, write_word_srt

    json_path = args.input_file or args.input
    if not json_path:
        print("Error: Whisper JSON required for transcript-to-yaml")
        print("Usage: praisonaippt transcript-to-yaml -i timestamps.json -o prefix")
        return 1

    if not Path(json_path).is_file():
        print(f"Error: File not found: {json_path}")
        return 1

    out_prefix = args.output or "examples/heygen-article-50590"
    mode = getattr(args, "transcript_mode", None)
    align_raw = (getattr(args, "align", None) or "").strip()
    align_modes = [m.strip() for m in align_raw.split(",") if m.strip()]
    audio_path = getattr(args, "transcript_audio", None) or getattr(args, "narration_audio", None)

    paths: list = []
    variants_raw = (getattr(args, "variants", None) or "").strip()
    if variants_raw:
        names = list(MEDIA_VARIANTS.keys()) if variants_raw.lower() == "all" else [
            v.strip() for v in variants_raw.split(",") if v.strip()
        ]
        out_dir = Path(out_prefix).parent
        paths.extend(generate_media_variants(
            json_path,
            out_dir,
            mode="thematic",
            avatar_video_path=getattr(args, "avatar_video", "examples/heygen-article-50590.mp4"),
            audio_path=getattr(args, "narration_audio", "examples/short-script-50590.mp3"),
            presentation_title=getattr(args, "transcript_title", "AI Agents: A Serious Upgrade"),
            variants=names,
        ))

    if mode or not variants_raw:
        deck_mode = mode or "both"
        paths.extend(generate_decks(
            json_path,
            out_prefix,
            mode=deck_mode,
            avatar_video_path=getattr(args, "avatar_video", "examples/heygen-article-50590.mp4"),
            audio_path=getattr(args, "narration_audio", "examples/short-script-50590.mp3"),
            presentation_title=getattr(args, "transcript_title", "AI Agents: A Serious Upgrade"),
        ))

    data = load_whisper_json(json_path)

    if align_modes and audio_path and Path(audio_path).is_file():
        import yaml

        samples = None
        sr = 16000
        for p in paths:
            deck = yaml.safe_load(p.read_text(encoding="utf-8"))
            align_deck(deck, data, audio_path, align_modes)
            write_deck_yaml(deck, p)
            print(f"✓ Aligned {p.name} ({', '.join(align_modes)})")
        if "karaoke" in align_modes:
            try:
                from .audio_align import decode_mono_pcm
                samples, sr = decode_mono_pcm(audio_path)
            except Exception:
                samples = None
            word_srt = Path(out_prefix).parent / f"{Path(out_prefix).name}-words.srt"
            write_word_srt(data.words, word_srt, samples=samples, sample_rate=sr)
            print(f"✓ Word SRT: {word_srt}")
    elif align_modes:
        print("Warning: --align ignored; provide --transcript-audio with existing file")

    for p in paths:
        print(f"✓ Wrote {p}")
    return 0


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

        try:
            data = validate_verses(data)
        except SchemaError as e:
            print(f"Error: Invalid schema in '{input_path}': {e}")
            return 1

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


def handle_convert_video_command(args, data: Optional[dict] = None):
    """Handle standalone convert-video command or --check preflight."""
    if getattr(args, "check", False):
        print("Video export dependency check:")
        code = print_tool_check_report()
        enc = pick_video_encoder()
        print(f"  encoder: {enc}")
        return code

    if not args.input_file:
        print("Error: Input file required for convert-video command")
        print("Usage: praisonaippt convert-video <file.pptx> [--video-output out.mp4]")
        print("       praisonaippt convert-video --check")
        return 1

    if not Path(args.input_file).exists():
        print(f"Error: Input file not found: {args.input_file}")
        return 1

    if not args.input_file.lower().endswith(('.pptx', '.ppt')):
        print("Error: Input file must be a PowerPoint presentation")
        return 1

    if args.video_backend == "powerpoint":
        print("Error: PowerPoint backend is not implemented (Phase 3, on-prem Windows only)")
        return 1

    try:
        if data is None:
            data = load_deck_sidecar(args.input_file)
            if data:
                print(f"Using deck sidecar: {data.get('_source_file')}")
        opts = parse_video_options(args, data)
        if args.video_output:
            video_path = args.video_output
        else:
            video_path = opts.output_path or str(Path(args.input_file).with_suffix(".mp4"))

        print(f"Converting {args.input_file} to video...")
        result = convert_pptx_to_video(
            args.input_file,
            video_path,
            data=data,
            options=opts,
        )
        print(f"✓ Successfully converted to: {result}")
        srt = Path(result).with_suffix(".srt")
        if srt.is_file():
            print(f"✓ Captions sidecar: {srt}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
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

    # Handle standalone convert-video command
    if args.command == 'convert-video':
        return handle_convert_video_command(args)

    if getattr(args, "check", False) and not args.command:
        print("Video export dependency check:")
        code = print_tool_check_report()
        print(f"  encoder: {pick_video_encoder()}")
        return code

    # Handle convert-json command
    if args.command == 'convert-json':
        return handle_convert_json_command(args)
    
    # Handle convert-yaml command
    if args.command == 'convert-yaml':
        return handle_convert_yaml_command(args)

    if args.command == 'transcript-to-yaml':
        return handle_transcript_to_yaml_command(args)

    if args.command == 'list-slides':
        return handle_list_slides_command(args)

    if args.command == 'export-slide-jpegs':
        return handle_export_slide_jpegs_command(args)

    if args.command == 'template':
        return handle_template_show_command(args.input_file)

    # List templates if requested
    if args.list_templates:
        entries = list_templates()
        if entries:
            print("Available style templates:")
            for entry in entries:
                line = f"  - {entry['name']}"
                if entry.get('description'):
                    line += f" — {entry['description']}"
                if entry.get('extends'):
                    line += f" (extends {entry['extends']})"
                print(line)
            print("\nUse with: praisonaippt -i deck.yaml --template <name>")
            print("Show resolved style: praisonaippt template <name>")
        else:
            print("No templates found.")
        return 0
    
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
    data = load_verses_from_file(input_file, template=getattr(args, 'template', None))
    
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

    if not getattr(args, 'no_list_slides', False):
        print()
        print_slide_outline(output_file)

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

    if getattr(args, "export_slide_jpegs", False):
        rc = handle_export_slide_jpegs_command(args, pptx_path=output_file, pdf_path=pdf_path)
        if rc != 0:
            return rc

    # Convert to video if requested (reuse PDF when both flags set)
    if getattr(args, "convert_video", False):
        try:
            if args.video_backend == "powerpoint":
                print("Error: PowerPoint backend is not implemented (Phase 3, on-prem Windows only)")
                return 1
            opts = parse_video_options(args, data)
            if args.video_output:
                video_path = args.video_output
            else:
                video_path = opts.output_path or str(Path(output_file).with_suffix(".mp4"))
            print("Converting to video...")
            result = convert_deck_to_video(
                data,
                output_file,
                video_options=opts,
                pdf_path=pdf_path,
                custom_title=args.title,
            )
            print(f"✓ Video created: {result}")
            srt = Path(result).with_suffix(".srt")
            if srt.is_file():
                print(f"✓ Captions sidecar: {srt}")
        except Exception as e:
            print(f"Warning: Video conversion failed: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
