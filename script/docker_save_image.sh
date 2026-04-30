#!/usr/bin/env bash
# Build the benchmark image and write a tarball under Images/.
# Usage (from repo root): ./script/docker_save_image.sh
# Optional: IMAGE_VERSION=0.2.0 ./script/docker_save_image.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

if [[ -n "${IMAGE_VERSION:-}" ]]; then
  VERSION="${IMAGE_VERSION}"
else
  VERSION="$(
    grep -E '^version[[:space:]]*=[[:space:]]*"' pyproject.toml \
      | head -1 \
      | sed -E 's/^version[[:space:]]*=[[:space:]]*"([^"]+)".*/\1/'
  )"
fi

if [[ -z "${VERSION}" ]]; then
  echo "Could not read version from pyproject.toml" >&2
  exit 1
fi

TAG="${DOCKER_IMAGE_NAME:-dataclaw}:${VERSION}"
OUT_DIR="${OUT_DIR:-${ROOT}/Images}"
TAR_BASENAME="${TAR_BASENAME:-dataclaw_ubuntu_v${VERSION}.tar}"
COMPRESS="${COMPRESS:-0}"

mkdir -p "${OUT_DIR}"
TAR_PATH="${OUT_DIR}/${TAR_BASENAME}"

echo "Building image ${TAG}..."
docker build -t "${TAG}" "${ROOT}"

echo "Saving to ${TAR_PATH}..."
docker save -o "${TAR_PATH}" "${TAG}"

if [[ "${COMPRESS}" == "1" ]]; then
  echo "Compressing..."
  gzip -f "${TAR_PATH}"
  TAR_PATH="${TAR_PATH}.gz"
fi

echo ""
echo "Done: ${TAR_PATH}"
echo "Publish: upload this file (e.g. Hugging Face dataset repo)."
echo "Consumer: docker load -i $(basename "${TAR_PATH}")"
echo "Run:      python dataclaw/eval/run_batch.py --model <model_id>"
