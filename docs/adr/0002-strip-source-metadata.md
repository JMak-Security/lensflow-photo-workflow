# ADR 0002: Do not propagate embedded source metadata

- Status: Accepted
- Date: 2026-11-06

## Context

Photo metadata can include device details, capture times, and location information. No user request
was made to preserve it in exports.

## Decision

Apply EXIF orientation to pixels, then create fresh RGB JPEG outputs without copying EXIF, ICC, or
other source metadata. Never inspect or report GPS coordinates.

## Consequences

- Exported previews reduce accidental metadata disclosure.
- Color profiles and capture metadata are not preserved; the workflow is not a print master.
- Tests verify that source metadata does not appear in generated JPEG exports.
