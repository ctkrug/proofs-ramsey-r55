#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

check_sha256() {
  local expected="$1"
  local path="$2"
  local actual
  actual="$(sha256sum "$path" | awk '{print $1}')"
  if [[ "$actual" != "$expected" ]]; then
    echo "immutable input hash mismatch: $path" >&2
    exit 65
  fi
}

for arg in "$@"; do
  if [[ "$arg" == "--host-seconds" || "$arg" == --host-seconds=* ]]; then
    echo "the locked wrapper owns --host-seconds" >&2
    exit 64
  fi
done

check_sha256 "d571103060c50a82bc6b7d41c7affabc4062ef975750da397bacf93ae81623dc" scripts/run_known_class_embedding_census.py
check_sha256 "01b3953b1db6a65737e4fb4ee176a88b7c8c8ed26a374c410cf274fe2500739a" scripts/enumerate_core_embeddings_bitset.py
check_sha256 "c4491591b16394e11d3bf0b907eea8c65a73308e8a2a366e5d594532c7010aaf" scripts/enumerate_core_embeddings_networkx.py
check_sha256 "067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb" sources/r55_42some.g6

git diff --quiet HEAD -- \
  scripts/run_known_class_embedding_census.py \
  scripts/enumerate_core_embeddings_bitset.py \
  scripts/enumerate_core_embeddings_networkx.py \
  sources/r55_42some.g6 || {
    echo "protected census inputs differ from the committed revision" >&2
    exit 65
  }

exec python3 scripts/run_known_class_embedding_census.py "$@" --host-seconds 30
