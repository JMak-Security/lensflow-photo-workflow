# ADR 0003: Generate synthetic sample images

- Status: Accepted
- Date: 2026-11-06

## Context

No personal photographs or licensed image assets were supplied. Photographic examples could imply
access to user assets or introduce rights uncertainty.

## Decision

Create sample PNGs from deterministic geometric patterns using the project itself. Label them as
synthetic and avoid people, recognizable places, or third-party assets.

## Consequences

- Demo and benchmark inputs are reproducible and clearly non-photographic.
- Results do not demonstrate work on real photography or production customer images.
- The generator is tested and its output is not counted as externally sourced imagery.
