#!/usr/bin/env python3
"""
Wrapper script for markitdown conversion.
Usage: python scripts/convert_to_markdown.py input_file output_file
"""

import sys
from pathlib import Path

try:
    from markitdown import MarkItDown
except ImportError:
    print("Error: markitdown not installed. Run: pip install 'markitdown[all]'")
    sys.exit(1)


def convert_to_markdown(input_path: str, output_path: str = None):
    """Convert a file to markdown using MarkItDown."""
    input_file = Path(input_path)
    
    if not input_file.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    # Initialize MarkItDown
    md = MarkItDown()
    
    # Convert the file
    try:
        result = md.convert(str(input_file))
        markdown_content = result.text_content
    except Exception as e:
        print(f"Error converting file: {e}")
        sys.exit(1)
    
    # Output to file or stdout
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown_content, encoding='utf-8')
        print(f"Converted {input_path} -> {output_path}")
    else:
        print(markdown_content)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/convert_to_markdown.py input_file [output_file]")
        print("  If output_file is omitted, prints to stdout")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    convert_to_markdown(input_file, output_file)