#!/usr/bin/env bash
set -euo pipefail

src_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
target_dir="${HOME}/.codex/skills/benchmark-dialogs"

mkdir -p "${target_dir}"
cp "${src_dir}/SKILL.md" "${target_dir}/SKILL.md"
cp "${src_dir}/README.md" "${target_dir}/README.md"
cp "${src_dir}/DESIGN.md" "${target_dir}/DESIGN.md"

echo "Installed benchmark-dialogs skill to ${target_dir}"
