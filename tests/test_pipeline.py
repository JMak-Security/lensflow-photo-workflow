from __future__ import annotations

import json
from pathlib import Path
from typing import NoReturn

import pytest
from PIL import Image

import lensflow.imaging as imaging
import lensflow.pipeline as pipeline
from lensflow.imaging import inspect_image, load_oriented_rgb
from lensflow.pipeline import run_workflow
from lensflow.synthetic import generate_sample_set


def _write_png(path: Path, size: tuple[int, int] = (80, 40)) -> None:
    image = Image.new("RGBA", size, (20, 40, 60, 255))
    image.save(path, format="PNG")


def test_pipeline_orders_images_exports_and_strips_metadata(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    transparent = Image.new("RGBA", (80, 40), (20, 40, 60, 0))
    transparent.save(source / "zeta.png", format="PNG")
    transparent.close()
    image = Image.new("RGB", (40, 80), (200, 30, 50))
    image.save(source / "Alpha.JPG", format="JPEG", quality=90)
    (source / "notes.txt").write_text("ignored", encoding="utf-8")

    output = tmp_path / "output" / "run"
    manifest = run_workflow(source, output, max_edge=30, quality=80, columns=2)

    assert [item["source_name"] for item in manifest["images"]] == ["Alpha.JPG", "zeta.png"]
    assert manifest["ignored_files"] == ["notes.txt"]
    assert manifest["settings"]["metadata_stripped"] is True
    assert (output / "contact_sheet.jpg").is_file()
    assert json.loads((output / "manifest.json").read_text(encoding="utf-8")) == manifest
    for item in manifest["images"]:
        exported = Image.open(output / "exports" / item["output_name"])
        assert max(exported.size) <= 30
        assert not exported.getexif()
        assert "icc_profile" not in exported.info
        exported.close()
    alpha_export = Image.open(output / "exports" / "asset_002.jpg")
    assert alpha_export.getpixel((0, 0)) == (255, 255, 255)
    alpha_export.close()


def test_exif_orientation_is_applied_and_metadata_removed(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    exif = Image.Exif()
    exif[274] = 6
    image = Image.new("RGB", (20, 10), (40, 100, 160))
    image.save(source / "rotated.jpg", format="JPEG", exif=exif)

    manifest = run_workflow(source, tmp_path / "out", max_edge=100)

    assert manifest["images"][0]["source_dimensions"] == [20, 10]
    assert manifest["images"][0]["output_dimensions"] == [10, 20]
    exported = Image.open(tmp_path / "out" / "exports" / "image_001.jpg")
    assert exported.getexif().get(274) is None
    exported.close()


def test_rejects_bad_options_overlapping_paths_and_existing_output(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    _write_png(source / "image.png")

    with pytest.raises(ValueError, match="max_edge"):
        run_workflow(source, tmp_path / "bad", max_edge=0)
    with pytest.raises(ValueError, match="must not overlap"):
        run_workflow(source, source / "out")
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(ValueError, match="already exists"):
        run_workflow(source, existing)


def test_rejects_corrupt_images_without_creating_output(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "broken.png").write_bytes(b"not an image")
    output = tmp_path / "out"

    with pytest.raises(ValueError, match="unable to verify"):
        run_workflow(source, output)
    assert not output.exists()


def test_detects_source_changes_after_validation(tmp_path: Path) -> None:
    path = tmp_path / "image.png"
    _write_png(path)
    record = inspect_image(path)
    path.write_bytes(b"changed")

    with pytest.raises(ValueError, match="source changed"):
        load_oriented_rgb(record)


def test_synthetic_samples_are_deterministic_and_do_not_overwrite(tmp_path: Path) -> None:
    output = tmp_path / "samples"
    first = generate_sample_set(output, count=2)
    hashes = [inspect_image(path).source_sha256 for path in first]

    second_output = tmp_path / "samples-again"
    second = generate_sample_set(second_output, count=2)
    assert [inspect_image(path).source_sha256 for path in second] == hashes
    with pytest.raises(ValueError, match="new or empty"):
        generate_sample_set(output)
    with pytest.raises(ValueError, match="count"):
        generate_sample_set(tmp_path / "invalid", count=0)


def test_load_oriented_rgb_returns_metadata_free_rgb(tmp_path: Path) -> None:
    path = tmp_path / "input.png"
    _write_png(path)
    clean = load_oriented_rgb(inspect_image(path))
    assert clean.mode == "RGB"
    assert clean.info == {}
    clean.close()


def test_rejects_empty_source_and_non_directory(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    file_path = tmp_path / "file"
    file_path.write_text("not a folder", encoding="utf-8")
    with pytest.raises(ValueError, match="no supported"):
        imaging.discover_images(empty)
    with pytest.raises(ValueError, match="must be a directory"):
        imaging.discover_images(file_path)


def test_enforces_input_byte_and_file_count_limits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    oversized = source / "large.png"
    oversized.write_bytes(b"x" * 11)
    monkeypatch.setattr(imaging, "MAX_FILE_BYTES", 10)
    with pytest.raises(ValueError, match="byte limit"):
        inspect_image(oversized)

    monkeypatch.setattr(imaging, "MAX_FILE_BYTES", 1024)
    _write_png(source / "second.png")
    monkeypatch.setattr(imaging, "MAX_FILES", 1)
    with pytest.raises(ValueError, match="image limit"):
        imaging.discover_images(source)


def test_rejects_content_mismatch_and_symlinked_images(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "mismatch.png").write_bytes(b"not png content")
    with pytest.raises(ValueError, match="unable to verify"):
        inspect_image(source / "mismatch.png")

    target = source / "target.png"
    _write_png(target)
    alias = source / "alias.png"
    try:
        alias.symlink_to(target)
    except OSError:
        pytest.skip("symlink creation is not permitted")
    with pytest.raises(ValueError, match="symlinked"):
        imaging.discover_images(source)


def test_rejects_image_above_pixel_limit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "large.png"
    _write_png(source, (20, 20))
    monkeypatch.setattr(imaging, "MAX_IMAGE_PIXELS", 100)
    with pytest.raises(ValueError, match="pixel limit"):
        inspect_image(source)


def test_cleans_staging_directory_after_processing_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    _write_png(source / "image.png")
    output = tmp_path / "out"

    def fail(*args: object, **kwargs: object) -> NoReturn:
        raise RuntimeError("simulated encode failure")

    monkeypatch.setattr(pipeline, "_export_one", fail)
    with pytest.raises(RuntimeError, match="simulated encode failure"):
        run_workflow(source, output)
    assert not output.exists()
    assert not list(tmp_path.glob(".out.staging-*"))
