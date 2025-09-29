#!/usr/bin/env python3

import argparse
import os
import sys
from pathlib import Path

try:
    from docx import Document
except ImportError:
    print("Error: python-docx library is required. Install it with: pip install python-docx")
    sys.exit(1)

try:
    import mammoth
except ImportError:
    print("Error: mammoth library is required. Install it with: pip install mammoth")
    sys.exit(1)


def convert_docx_to_md(docx_path, output_dir='MD', use_mammoth=True):
    """
    Convert a Word document to Markdown format.
    
    Args:
        docx_path (str): Path to the .docx file
        output_dir (str): Directory to save the .md file (default: 'MD')
        use_mammoth (bool): Use mammoth library for better formatting
    
    Returns:
        str: Path to the created markdown file
    """
    docx_file = Path(docx_path)
    
    if not docx_file.exists():
        raise FileNotFoundError(f"File not found: {docx_path}")
    
    if not docx_file.suffix.lower() == '.docx':
        raise ValueError(f"File is not a .docx file: {docx_path}")
    
    # Determine output path - always use output_dir (default is 'MD')
    output_path = Path(output_dir) / f"{docx_file.stem}.md"
    os.makedirs(output_dir, exist_ok=True)
    
    if use_mammoth:
        # Use mammoth for better HTML to Markdown conversion
        with open(docx_path, "rb") as docx_file_handle:
            result = mammoth.convert_to_markdown(docx_file_handle)
            markdown_content = result.value
            
            if result.messages:
                print(f"Conversion warnings for {docx_path}:")
                for message in result.messages:
                    print(f"  - {message}")
    else:
        # Use python-docx (basic text extraction)
        doc = Document(docx_path)
        markdown_content = ""
        
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if text:
                # Basic heading detection based on style
                if paragraph.style.name.startswith('Heading'):
                    level = paragraph.style.name.split()[-1]
                    if level.isdigit():
                        markdown_content += f"{'#' * int(level)} {text}\n\n"
                    else:
                        markdown_content += f"# {text}\n\n"
                else:
                    markdown_content += f"{text}\n\n"
    
    # Write markdown file
    with open(output_path, 'w', encoding='utf-8') as md_file:
        md_file.write(markdown_content)
    
    return str(output_path)


def find_docx_files(directory):
    """Find all .docx files in the specified directory."""
    directory = Path(directory)
    return list(directory.glob("*.docx"))


def main():
    parser = argparse.ArgumentParser(
        description="Convert Word documents (.docx) to Markdown (.md) files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Convert all .docx files in current directory
  %(prog)s -d /path/to/docs          # Convert all .docx files in specified directory
  %(prog)s -o /path/to/output        # Save .md files to specified output directory
  %(prog)s -f file.docx              # Convert specific file
  %(prog)s --basic                   # Use basic conversion (python-docx only)
        """
    )
    
    parser.add_argument(
        '-d', '--directory',
        default='.',
        help='Directory to search for .docx files (default: current directory)'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='MD',
        help='Output directory for .md files (default: MD directory)'
    )
    
    parser.add_argument(
        '-f', '--file',
        help='Convert specific .docx file instead of all files in directory'
    )
    
    parser.add_argument(
        '--basic',
        action='store_true',
        help='Use basic conversion with python-docx (instead of mammoth)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Determine files to convert
    if args.file:
        docx_files = [Path(args.file)]
        if not docx_files[0].exists():
            print(f"Error: File not found: {args.file}")
            sys.exit(1)
    else:
        docx_files = find_docx_files(args.directory)
        if not docx_files:
            print(f"No .docx files found in directory: {args.directory}")
            sys.exit(1)
    
    print(f"Found {len(docx_files)} .docx file(s) to convert:")
    for file in docx_files:
        print(f"  - {file}")
    
    # Convert files
    converted_files = []
    failed_files = []
    
    for docx_file in docx_files:
        try:
            if args.verbose:
                print(f"\nConverting: {docx_file}")
            
            output_file = convert_docx_to_md(
                str(docx_file),
                args.output,
                use_mammoth=not args.basic
            )
            
            converted_files.append(output_file)
            print(f"✓ Converted: {docx_file.name} -> {Path(output_file).name}")
            
        except Exception as e:
            failed_files.append((str(docx_file), str(e)))
            print(f"✗ Failed to convert {docx_file.name}: {e}")
    
    # Summary
    print(f"\nConversion complete:")
    print(f"  Successfully converted: {len(converted_files)} files")
    print(f"  Failed conversions: {len(failed_files)} files")
    
    if failed_files:
        print("\nFailed files:")
        for file, error in failed_files:
            print(f"  - {file}: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()