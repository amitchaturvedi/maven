#!/usr/bin/env bash
set -euo pipefail

# Creates a zip archive of the repository at HEAD.
# Usage: tools/create_source_zip.sh [output.zip]

OUTPUT_PATH=${1:-source.zip}

git archive --format=zip --output "$OUTPUT_PATH" HEAD

echo "Created archive at $OUTPUT_PATH"
