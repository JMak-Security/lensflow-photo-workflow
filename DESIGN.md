# LensFlow Photo Workflow

## Status and scope

Design baseline for Project 8. The referenced `Qoder_Master_Prompt_9_Projects_Senior.md` is not
present in this workspace, so the project scope is conservatively inferred from its name and the
portfolio log. No personal photographs were supplied; sample imagery will be generated patterns
and visibly labeled synthetic.

LensFlow is a local batch utility for cataloging JPEG/PNG files, generating consistent resized JPEG
exports, and composing a contact sheet. It preserves source files and re-encodes exports without
copying EXIF metadata.

## Inputs and outputs

- Non-recursive folder scan of `.jpg`, `.jpeg`, and `.png` files.
- Maximum 500 images, 50 MiB per file, and 100 megapixels per decoded image.
- Deterministic lexicographic input ordering and deterministic `asset_001.jpg` output names.
- A new output directory containing resized JPEGs, a contact sheet, and a provenance manifest.
- The manifest records input filenames, SHA-256 digests, dimensions, output names, and explicitly
  states that embedded metadata was not copied.

## Workflow

1. Validate paths and the complete supported input set before creating outputs.
2. Decode with Pillow and apply EXIF orientation in memory.
3. Convert to RGB, resize without upscaling beyond the selected maximum edge, and encode JPEG at
   the configured quality.
4. Build a labeled contact sheet from the same oriented source pixels.
5. Write outputs locally; do not modify or delete source images.

## Security and privacy boundaries

- No network access, cloud upload, facial recognition, geolocation extraction, or RAW development.
- Reject symlinked input files and output directories that overlap the source directory.
- Respect explicit file, image-count, and pixel-count limits; treat decompression-bomb warnings as
  errors.
- Re-encoding deliberately omits EXIF and other source metadata from exports.
- Synthetic example files are generated geometric patterns, not photographs of people or places.

## Assumptions

- JPEG and PNG are sufficient for a conservative first workflow; camera RAW formats are out of
  scope.
- Since no real image set was supplied, all examples and measurements use generated test images.
- This tool demonstrates image-processing workflow mechanics, not professional retouching or
  color-managed print production.
