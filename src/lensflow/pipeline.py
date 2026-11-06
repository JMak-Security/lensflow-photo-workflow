"""Validated, local-only photo export pipeline."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from lensflow import __version__
from lensflow.imaging import discover_images, inspect_image, load_oriented_rgb
from lensflow.models import ExportRecord, ImageRecord, RunManifest

CONTACT_WIDTH = 240
CONTACT_HEIGHT = 180
LABEL_HEIGHT = 24
CONTACT_COLUMNS_MAX = 8


def _validate_options(max_edge: int, quality: int, columns: int) -> None:
    if not 1 <= max_edge <= 8192:
        raise ValueError("max_edge must be between 1 and 8192")
    if not 50 <= quality <= 95:
        raise ValueError("quality must be between 50 and 95")
    if not 1 <= columns <= CONTACT_COLUMNS_MAX:
        raise ValueError(f"columns must be between 1 and {CONTACT_COLUMNS_MAX}")


def _ensure_disjoint(source_dir: Path, output_dir: Path) -> None:
    if (
        source_dir == output_dir
        or source_dir in output_dir.parents
        or output_dir in source_dir.parents
    ):
        raise ValueError("source and output directories must not overlap")


def _label_for(name: str) -> str:
    ascii_name = name.encode("ascii", "backslashreplace").decode("ascii")
    if len(ascii_name) > 32:
        return ascii_name[:29] + "..."
    return ascii_name


def _save_jpeg(image: Image.Image, path: Path, quality: int) -> str:
    import io

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality, optimize=False, progressive=False)
    content = buffer.getvalue()
    path.write_bytes(content)
    return hashlib.sha256(content).hexdigest()


def _add_to_contact_sheet(
    sheet: Image.Image,
    image: Image.Image,
    name: str,
    index: int,
    columns: int,
) -> None:
    row, column = divmod(index, columns)
    left = column * CONTACT_WIDTH
    top = row * (CONTACT_HEIGHT + LABEL_HEIGHT)
    thumbnail = image.copy()
    thumbnail.thumbnail((CONTACT_WIDTH - 12, CONTACT_HEIGHT - 12), Image.Resampling.LANCZOS)
    x = left + (CONTACT_WIDTH - thumbnail.width) // 2
    y = top + (CONTACT_HEIGHT - thumbnail.height) // 2
    sheet.paste(thumbnail, (x, y))
    draw = ImageDraw.Draw(sheet)
    draw.text(
        (left + 6, top + CONTACT_HEIGHT + 3),
        _label_for(name),
        fill=(20, 20, 20),
        font=ImageFont.load_default(),
    )


def _export_one(
    record: ImageRecord,
    stage: Path,
    index: int,
    max_edge: int,
    quality: int,
) -> tuple[ExportRecord, Image.Image]:
    image = load_oriented_rgb(record)
    image.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
    output_name = f"asset_{index:03d}.jpg"
    output_sha256 = _save_jpeg(image, stage / "exports" / output_name, quality)
    export_record = ExportRecord(
        source_name=record.path.name,
        source_sha256=record.source_sha256,
        source_format=record.source_format,
        source_width=record.source_width,
        source_height=record.source_height,
        output_name=output_name,
        output_width=image.width,
        output_height=image.height,
        output_sha256=output_sha256,
    )
    return export_record, image


def run_workflow(
    source_dir: Path,
    output_dir: Path,
    *,
    max_edge: int = 1600,
    quality: int = 85,
    columns: int = 4,
) -> RunManifest:
    _validate_options(max_edge, quality, columns)
    source = source_dir.resolve(strict=True)
    images, ignored_files = discover_images(source)
    if output_dir.is_symlink():
        raise ValueError("output path must not be a symlink")
    output = output_dir.resolve(strict=False)
    _ensure_disjoint(source, output)
    if output.exists():
        raise ValueError(f"output directory already exists: {output}")

    records = [inspect_image(path) for path in images]

    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=output.parent))
    try:
        exports_dir = stage / "exports"
        exports_dir.mkdir()
        rows = (len(records) + columns - 1) // columns
        sheet = Image.new(
            "RGB",
            (columns * CONTACT_WIDTH, rows * (CONTACT_HEIGHT + LABEL_HEIGHT)),
            (245, 245, 245),
        )
        exported: list[ExportRecord] = []
        for index, record in enumerate(records):
            exported_record, contact_image = _export_one(
                record, stage, index + 1, max_edge, quality
            )
            exported.append(exported_record)
            _add_to_contact_sheet(sheet, contact_image, record.path.name, index, columns)
            contact_image.close()

        contact_sheet_name = "contact_sheet.jpg"
        _save_jpeg(sheet, stage / contact_sheet_name, quality)
        sheet.close()
        manifest: RunManifest = {
            "application": "LensFlow",
            "version": __version__,
            "settings": {
                "max_edge": max_edge,
                "jpeg_quality": quality,
                "contact_sheet_columns": columns,
                "metadata_stripped": True,
            },
            "images": [
                {
                    "source_name": item.source_name,
                    "source_sha256": item.source_sha256,
                    "source_format": item.source_format,
                    "source_dimensions": [item.source_width, item.source_height],
                    "output_name": item.output_name,
                    "output_dimensions": [item.output_width, item.output_height],
                    "output_sha256": item.output_sha256,
                }
                for item in exported
            ],
            "ignored_files": ignored_files,
            "contact_sheet": contact_sheet_name,
        }
        (stage / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
        )
        os.replace(stage, output)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return manifest
