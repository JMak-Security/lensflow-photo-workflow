# Security

## Supported scope

LensFlow is a local-only batch image utility. It supports non-recursive JPEG and PNG inputs and
does not make network requests. Treat untrusted images as potentially hostile.

The utility enforces file-count, input-byte, and decoded-pixel limits, rejects supported image
symlinks, verifies images before creating output, detects source changes between validation and
processing, strips source metadata from generated JPEGs, and writes to a new output directory.
These controls reduce risk; they do not prove that image parsing is safe for every malicious file.

## Reporting

Please report security issues privately to the repository maintainer rather than including
unpatched exploit details in a public issue.
