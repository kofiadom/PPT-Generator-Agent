#!/usr/bin/env python3
"""
Helper wrapper around rearrange.py that accepts a JSON or plaintext mapping file.

The mapping file can contain either:
1. JSON array of integers, e.g. [0, 1, 2, 3]
2. JSON object with key "sequence" mapping to an array
3. Plain comma-separated integers (0,1,2,3)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from rearrange import rearrange_presentation


def parse_mapping(mapping_path: Path) -> List[int]:
    text = mapping_path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("Mapping file is empty")

    # Try JSON first
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "sequence" in data:
            seq = data["sequence"]
        else:
            seq = data
        if not isinstance(seq, list):
            raise ValueError
        return [int(x) for x in seq]
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: comma-separated string
    sequence = [s.strip() for s in text.split(",") if s.strip()]
    if not sequence:
        raise ValueError("Could not parse mapping file")
    return [int(x) for x in sequence]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rearrange slides using a mapping file."
    )
    parser.add_argument("template", help="Template PPTX path")
    parser.add_argument("output", help="Output PPTX path")
    parser.add_argument("mapping_file", help="Mapping file path")

    args = parser.parse_args()
    template_path = Path(args.template).resolve()
    output_path = Path(args.output).resolve()
    mapping_path = Path(args.mapping_file).resolve()

    if not mapping_path.exists():
        raise SystemExit(f"Mapping file not found: {mapping_path}")

    sequence = parse_mapping(mapping_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rearrange_presentation(template_path, output_path, sequence)


if __name__ == "__main__":
    main()
