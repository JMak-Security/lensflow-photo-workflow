"""Image workflow data models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict


@dataclass(frozen=True)
class ImageRecord:
    path: Path
    source_sha256: str
    source_format: str
    source_width: int
    source_height: int
    oriented_width: int
    oriented_height: int


@dataclass(frozen=True)
class ExportRecord:
    source_name: str
    source_sha256: str
    source_format: str
    source_width: int
    source_height: int
    output_name: str
    output_width: int
    output_height: int
    output_sha256: str


class ImageManifest(TypedDict):
    source_name: str
    source_sha256: str
    source_format: str
    source_dimensions: list[int]
    output_name: str
    output_dimensions: list[int]
    output_sha256: str


class SettingsManifest(TypedDict):
    max_edge: int
    jpeg_quality: int
    contact_sheet_columns: int
    metadata_stripped: bool


class RunManifest(TypedDict):
    application: str
    version: str
    settings: SettingsManifest
    images: list[ImageManifest]
    ignored_files: list[str]
    contact_sheet: str
