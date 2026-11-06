"""Reproducible, synthetic end-to-end batch throughput benchmark."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import statistics
import tempfile
import time
from pathlib import Path

import PIL

from lensflow.pipeline import run_workflow
from lensflow.synthetic import generate_sample_set


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", type=int, default=100)
    parser.add_argument("--runs", type=int, default=3)
    arguments = parser.parse_args()
    if not 1 <= arguments.images <= 500:
        parser.error("--images must be between 1 and 500")
    if not 1 <= arguments.runs <= 10:
        parser.error("--runs must be between 1 and 10")

    durations: list[float] = []
    with tempfile.TemporaryDirectory(prefix="lensflow-benchmark-") as temporary:
        root = Path(temporary)
        patterns = generate_sample_set(root / "patterns", count=20)
        source = root / "source"
        source.mkdir()
        for index in range(arguments.images):
            shutil.copyfile(
                patterns[index % len(patterns)],
                source / f"synthetic_{index + 1:04d}.png",
            )
        for run in range(arguments.runs):
            started = time.perf_counter()
            manifest = run_workflow(
                source,
                root / f"output-{run + 1}",
                max_edge=1000,
                quality=85,
                columns=4,
            )
            durations.append(time.perf_counter() - started)
            if len(manifest["images"]) != arguments.images:
                raise RuntimeError("benchmark processed an unexpected image count")

    median_seconds = statistics.median(durations)
    print(
        json.dumps(
            {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "pillow": PIL.__version__,
                "images": arguments.images,
                "runs": arguments.runs,
                "seconds": [round(value, 6) for value in durations],
                "median_seconds": round(median_seconds, 6),
                "median_images_per_second": round(arguments.images / median_seconds, 2),
                "settings": {"max_edge": 1000, "jpeg_quality": 85, "columns": 4},
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
