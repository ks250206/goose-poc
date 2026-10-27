#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
export PATH="$PWD/.venv/bin:$HOME/.cargo/bin:$PATH"
command -v rustc >/dev/null || { echo 'Install Rust via rustup (https://rustup.rs) first.' >&2; exit 1; }
mkdir -p .tools
if [ ! -d .tools/goose ]; then git clone https://github.com/aardappel/goose.git .tools/goose; fi
git -C .tools/goose checkout 64d62fc7f148eadaed9b1c69be0c33d1da97c82f
cmake -S .tools/goose -B .tools/goose/build -DCMAKE_BUILD_TYPE=Release
cmake --build .tools/goose/build -j "${BUILD_JOBS:-2}"
.tools/goose/build/goose build src/sf.goose --cc gcc
rustc --edition=2021 -C opt-level=2 src/sf.rs -o src/sf-rust
