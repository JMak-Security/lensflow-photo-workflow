# ADR 0001: Support JPEG and PNG only

- Status: Accepted
- Date: 2026-11-06

## Context

No camera files, workflow requirements, or sample photos were supplied. RAW decoding and
camera-specific color workflows would be speculative.

## Decision

Support only JPEG and PNG inputs for a local contact-sheet and resized-export workflow. Do not claim
RAW development, color-managed print output, or retouching.

## Consequences

- The supported input contract is simple and testable.
- Other file formats are reported as ignored; a batch with no supported images fails explicitly.
- Users must process RAW files in an appropriate raw-development application first.
