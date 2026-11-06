"""Command-line entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lensflow.pipeline import run_workflow
from lensflow.synthetic import generate_sample_set


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lensflow",
        description="Create metadata-stripped JPEG exports and a contact sheet locally.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="process a flat directory of JPEG and PNG files")
    build.add_argument("source", type=Path)
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--max-edge", type=int, default=1600)
    build.add_argument("--quality", type=int, default=85)
    build.add_argument("--columns", type=int, default=4)
    sample = commands.add_parser("sample", help="generate deterministic abstract sample images")
    sample.add_argument("--output-dir", type=Path, required=True)
    sample.add_argument("--count", type=int, default=6)
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    try:
        if arguments.command == "sample":
            generated = generate_sample_set(arguments.output_dir, count=arguments.count)
            print(f"Generated {len(generated)} synthetic images in {arguments.output_dir}")
            return 0
        manifest = run_workflow(
            arguments.source,
            arguments.output,
            max_edge=arguments.max_edge,
            quality=arguments.quality,
            columns=arguments.columns,
        )
    except (OSError, ValueError) as exc:
        print(f"lensflow: error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "processed": len(manifest["images"]),
                "output": str(arguments.output),
                "contact_sheet": str(arguments.output / "contact_sheet.jpg"),
                "manifest": str(arguments.output / "manifest.json"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
