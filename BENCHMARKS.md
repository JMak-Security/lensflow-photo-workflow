# Benchmark

LensFlow is measured with `python scripts/benchmark.py --images 100 --runs 3`. The script creates
deterministic abstract PNG patterns, repeats them under distinct filenames, and times end-to-end
validation, export, contact-sheet, and manifest generation. Image generation and setup are excluded
from the timed runs. The median elapsed time and derived images/second are reported; this is a
local throughput observation, not a production-capacity guarantee.

## Measured result

On Windows 11 build 26300, Python 3.12.10, Pillow 13.0.0, and an AMD Ryzen 7 5825U, the
100-image / three-run benchmark completed in 3.750469, 4.084658, and 4.035733 seconds. Median
elapsed time was **4.035733 seconds**, or **24.78 images/second**. Inputs were 800 × 600 synthetic
PNGs (20 deterministic patterns repeated under distinct filenames); exports used a 1000-pixel
maximum edge, JPEG quality 85, and four contact-sheet columns. This is a local synthetic workload
measurement, not a production-capacity guarantee.
