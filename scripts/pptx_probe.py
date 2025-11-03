#!/usr/bin/env python3
"""
Quick metadata probe for PPTX templates.

Generates JSON containing slide count and core document properties. This is
used by the Agno template-intake agent so downstream stages know the
template basics before heavy processing begins.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from zipfile import ZipFile, BadZipFile
import xml.etree.ElementTree as ET


CORE_NS = {
    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "dcmitype": "http://purl.org/dc/dcmitype/",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}


def _read_xml(zip_file: ZipFile, path: str) -> Optional[ET.Element]:
    """Return parsed XML element if the file exists, else None."""
    try:
        with zip_file.open(path) as fh:
            data = fh.read()
    except KeyError:
        return None

    # PowerPoint core XML files are UTF-8
    return ET.fromstring(data)


def _extract_core_props(root: Optional[ET.Element]) -> Dict[str, Any]:
    """Extract document core properties such as title or subject."""
    if root is None:
        return {}

    props: Dict[str, Any] = {}
    for tag, key in (
        ("dc:title", "title"),
        ("dc:subject", "subject"),
        ("dc:creator", "author"),
        ("cp:lastModifiedBy", "last_modified_by"),
        ("dc:description", "description"),
        ("cp:revision", "revision"),
        ("cp:category", "category"),
        ("cp:keywords", "keywords"),
        ("dcterms:created", "created"),
        ("dcterms:modified", "modified"),
    ):
        elem = root.find(tag, CORE_NS)
        if elem is None:
            continue
        text = elem.text or ""
        if text:
            props[key] = text
    return props


def probe_pptx(input_path: Path) -> Dict[str, Any]:
    """Return metadata dictionary for the PPTX file."""
    try:
        with ZipFile(input_path) as zf:
            slide_files: List[str] = sorted(
                name
                for name in zf.namelist()
                if name.startswith("ppt/slides/slide") and name.endswith(".xml")
            )
            core_props = _extract_core_props(_read_xml(zf, "docProps/core.xml"))
    except BadZipFile as exc:
        raise ValueError(f"{input_path} is not a valid PPTX archive") from exc

    metadata: Dict[str, Any] = {
        "template_path": str(input_path.resolve()),
        "slide_count": len(slide_files),
        "slide_files": slide_files,
    }
    metadata.update(core_props)
    return metadata


def write_metadata(metadata: Dict[str, Any], output_path: Path) -> None:
    """Persist metadata dictionary as pretty-printed JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        print(
            "Usage: python scripts/pptx_probe.py <template.pptx> <output.json>",
            file=sys.stderr,
        )
        return 1

    template_path = Path(argv[1]).expanduser().resolve()
    output_path = Path(argv[2]).expanduser()

    if not template_path.exists():
        print(f"Template not found: {template_path}", file=sys.stderr)
        return 1

    try:
        metadata = probe_pptx(template_path)
    except ValueError as err:
        print(str(err), file=sys.stderr)
        return 1

    write_metadata(metadata, output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
