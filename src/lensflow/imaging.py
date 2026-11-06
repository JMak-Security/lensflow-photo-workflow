"""Bounded local image discovery, verification, orientation, and metadata-stripping conversion."""

from __future__ import annotations

import hashlib
import io
import warnings
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from lensflow.models import ImageRecord

MAX_FILES = 500
MAX_FILE_BYTES = 50 * 1024 * 1024
MAX_IMAGE_PIXELS = 100_000_000
SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png"}

Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


def discover_images(source_dir: Path) -> tuple[list[Path], list[str]]:
    source = source_dir.resolve(strict=True)
    if not source.is_dir():
        raise ValueError("source path must be a directory")
    images: list[Path] = []
    ignored: list[str] = []
    for path in source.iterdir():
        if not path.is_file() and not path.is_symlink():
            continue
        if path.suffix.casefold() not in SUPPORTED_SUFFIXES:
            ignored.append(path.name)
            continue
        if path.is_symlink():
            raise ValueError(f"symlinked image input is not allowed: {path.name}")
        images.append(path)
    images.sort(key=lambda path: (path.name.casefold(), path.name))
    if not images:
        raise ValueError("source directory contains no supported JPEG or PNG images")
    if len(images) > MAX_FILES:
        raise ValueError(f"source directory exceeds the {MAX_FILES}-image limit")
    return images, sorted(ignored, key=str.casefold)


def _read_bounded(path: Path) -> bytes:
    with path.open("rb") as image_file:
        contents = image_file.read(MAX_FILE_BYTES + 1)
    if len(contents) > MAX_FILE_BYTES:
        raise ValueError(f"{path.name}: file exceeds the {MAX_FILE_BYTES}-byte limit")
    if not contents:
        raise ValueError(f"{path.name}: file is empty")
    return contents


def _inspect_bytes(contents: bytes, display_name: str) -> tuple[str, int, int, int, int]:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(contents)) as image:
                source_format = image.format or ""
                source_width, source_height = image.size
                if source_format not in {"JPEG", "PNG"}:
                    raise ValueError(f"{display_name}: file content is not JPEG or PNG")
                if source_width * source_height > MAX_IMAGE_PIXELS:
                    raise ValueError(
                        f"{display_name}: image exceeds the {MAX_IMAGE_PIXELS}-pixel limit"
                    )
                oriented = ImageOps.exif_transpose(image)
                oriented.load()
                oriented_width, oriented_height = oriented.size
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        OSError,
        SyntaxError,
        UnidentifiedImageError,
    ) as exc:
        raise ValueError(f"{display_name}: unable to verify image data: {exc}") from exc
    return source_format, source_width, source_height, oriented_width, oriented_height


def inspect_image(path: Path) -> ImageRecord:
    contents = _read_bounded(path)
    source_format, width, height, oriented_width, oriented_height = _inspect_bytes(
        contents, path.name
    )
    return ImageRecord(
        path=path,
        source_sha256=hashlib.sha256(contents).hexdigest(),
        source_format=source_format,
        source_width=width,
        source_height=height,
        oriented_width=oriented_width,
        oriented_height=oriented_height,
    )


def load_oriented_rgb(record: ImageRecord) -> Image.Image:
    contents = _read_bounded(record.path)
    if hashlib.sha256(contents).hexdigest() != record.source_sha256:
        raise ValueError(f"{record.path.name}: source changed after validation")
    try:
        with Image.open(io.BytesIO(contents)) as source:
            oriented = ImageOps.exif_transpose(source)
            oriented.load()
            if "A" in oriented.getbands() or "transparency" in oriented.info:
                rgba = oriented.convert("RGBA")
                background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
                rgb = Image.alpha_composite(background, rgba).convert("RGB")
            else:
                rgb = oriented.convert("RGB")
            clean = Image.new("RGB", rgb.size)
            clean.paste(rgb)
            return clean
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        OSError,
        SyntaxError,
        UnidentifiedImageError,
    ) as exc:
        raise ValueError(f"{record.path.name}: unable to decode image data: {exc}") from exc
