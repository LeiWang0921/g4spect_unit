#!/usr/bin/env bash
set -eo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/geant4_10.5/install/bin/geant4.sh
set -u

mkdir -p "$PROJECT_DIR/build" "$PROJECT_DIR/output"
cd "$PROJECT_DIR/build"
cmake -DGeant4_DIR=/opt/geant4_10.5/install/lib/Geant4-10.5.1 ..
cmake --build . -j2
./G4SPECT ../mac/tc99m_beam_smoke.mac
test -s "$PROJECT_DIR/output/spect_tc99m_smoke.root"
