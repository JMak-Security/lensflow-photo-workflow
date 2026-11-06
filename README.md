# LensFlow Photo Workflow

LensFlow is a local command-line utility for validating a flat folder of JPEG/PNG images,
applying EXIF orientation, exporting resized JPEGs without source metadata, and generating a
labeled contact sheet plus a SHA-256 provenance manifest.

This project uses deterministic abstract sample images only. It does not claim RAW development,
professional retouching, color-managed printing, or experience with personal or commercial photo
collections.

## Requirements

- Python 3.12+
- JPEG and PNG inputs; no recursive directory traversal
- Inputs are limited to 500 files, 50 MiB per file, and 100 megapixels per image

## Install and run

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
lensflow build samples\synthetic-set --output output\synthetic-run
```

The repository already includes the deterministic synthetic example images. To generate another
set, choose a new or empty folder with `lensflow sample --output-dir samples\generated-demo`,
then use that folder as the `build` input.

The output path must not already exist. The output folder contains:

- `exports\asset_NNN.jpg` — oriented, non-upscaled JPEG exports
- `contact_sheet.jpg` — labeled overview in deterministic input order
- `manifest.json` — settings, source/output dimensions, and SHA-256 digests

The manifest records source filenames but not absolute input paths. Source EXIF, ICC, and other
image metadata are not copied to the exports. Transparent PNG pixels are composited onto white.
The source files are never modified. The destination is assembled in a temporary sibling folder
and renamed into place only after successful processing.

Options:

```powershell
lensflow build INPUT_FOLDER --output OUTPUT_FOLDER --max-edge 1600 --quality 85 --columns 4
```

`max-edge` is 1–8192 pixels, JPEG quality is 50–95, and contact-sheet columns are 1–8.
Unsupported file extensions are ignored and listed in the manifest. Invalid, oversized, changed,
or symlinked supported images cause an explicit error and prevent final output creation.

## Docker

```powershell
New-Item -ItemType Directory -Force output
docker compose run --rm lensflow
```

Compose mounts the bundled synthetic samples read-only and writes under `output\synthetic-run`.
Because LensFlow never overwrites an existing output, set a new run name before repeating the
command, for example `$env:LENSFLOW_OUTPUT_NAME = "synthetic-run-2"`.
The container runs as an unprivileged user, drops Linux capabilities, has no network, uses a
read-only root filesystem, and exposes only a temporary writable `/tmp` plus the output mount.

## Development checks

```powershell
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy
pytest --cov --cov-report=term-missing
python -m build
pip-audit
cyclonedx-py environment --pyproject pyproject.toml --of JSON --output-file sbom.json
```

## Scope and privacy

LensFlow runs offline and does not upload images or call external services. It is an export helper,
not an archival system: keep original files and backups. Metadata stripping reduces what the
generated JPEGs disclose but is not a guarantee of anonymity. Input size and pixel limits reduce
resource-exhaustion risk but do not make untrusted image parsing risk-free.

See [DESIGN.md](DESIGN.md) and the [ADRs](docs/adr/) for design decisions.
