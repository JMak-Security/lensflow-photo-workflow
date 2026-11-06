from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from lensflow.cli import main


def test_cli_sample_and_build_commands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    samples = tmp_path / "samples"
    monkeypatch.setattr(
        "sys.argv",
        ["lensflow", "sample", "--output-dir", str(samples), "--count", "1"],
    )
    assert main() == 0
    assert "Generated 1 synthetic images" in capsys.readouterr().out

    output = tmp_path / "exports"
    monkeypatch.setattr(
        "sys.argv",
        ["lensflow", "build", str(samples), "--output", str(output)],
    )
    assert main() == 0
    assert '"processed": 1' in capsys.readouterr().out
    exported = Image.open(output / "exports" / "asset_001.jpg")
    assert exported.format == "JPEG"
    exported.close()


def test_cli_reports_errors_with_nonzero_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setattr(
        "sys.argv",
        ["lensflow", "build", str(empty), "--output", str(tmp_path / "output")],
    )
    assert main() == 2
    assert "no supported JPEG or PNG images" in capsys.readouterr().err
