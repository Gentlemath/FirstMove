#!/bin/bash

set -euo pipefail

# Back to repo root assuming script is run from repo root.
cd "$(dirname "$0")/.."

# Print backend version using Python path.
PYTHONPATH=backend python - <<'PY'
from app import __version__
print('backend version:', __version__)
PY

# Print frontend version
echo 'frontend version:' $(jq -r '.version' frontend/package.json)
