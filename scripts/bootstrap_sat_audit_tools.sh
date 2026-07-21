#!/usr/bin/env bash
set -euo pipefail

workspace_root="$(cd "$(dirname "$0")/.." && pwd)"
tool_root="$workspace_root/.venv/sat-audit-tools"
cadical_root="$tool_root/cadical"
drat_root="$tool_root/drat-trim"
cadical_commit="c60730422e758ef1cebe7aeddf2dda31c996bf04"
drat_commit="2e3b2dc0ecf938addbd779d42877b6ed69d9a985"

mkdir -p "$tool_root"

if [[ ! -d "$cadical_root/.git" ]]; then
  git clone --filter=blob:none --no-checkout https://github.com/arminbiere/cadical.git "$cadical_root"
fi
git -C "$cadical_root" fetch --depth 1 origin "$cadical_commit"
git -C "$cadical_root" checkout --detach "$cadical_commit"
actual_cadical="$(git -C "$cadical_root" rev-parse HEAD)"
[[ "$actual_cadical" == "$cadical_commit" ]]
if [[ ! -x "$cadical_root/build/cadical" ]]; then
  (cd "$cadical_root" && ./configure -O3 && make -C build -j2)
fi

if [[ ! -d "$drat_root/.git" ]]; then
  git clone --filter=blob:none --no-checkout https://github.com/marijnheule/drat-trim.git "$drat_root"
fi
git -C "$drat_root" fetch --depth 1 origin "$drat_commit"
git -C "$drat_root" checkout --detach "$drat_commit"
actual_drat="$(git -C "$drat_root" rev-parse HEAD)"
[[ "$actual_drat" == "$drat_commit" ]]
if [[ ! -x "$drat_root/drat-trim" ]]; then
  make -C "$drat_root" -j2
fi

"$cadical_root/build/cadical" --version
"$drat_root/drat-trim" 2>&1 | head -1 || true
printf 'cadical_commit=%s\n' "$actual_cadical"
printf 'drat_trim_commit=%s\n' "$actual_drat"
