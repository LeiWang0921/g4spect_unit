# G4 SPECT Unit

Minimal Geant4 SPECT detector-unit prototype for producing LYSO energy-deposition
records that can later be converted into optical photons in Chroma.

Geometry, along the gamma direction:

```text
Tc-99m source -> Pb parallel-hole collimator -> LYSO -> optical gel -> SiPM slab
```

The current source position is the world origin `(0, 0, 0)`. The detector stack
is placed along `+z`: a 64 mm x 64 mm local clinical-like patch with a
35 mm-thick Pb collimator, 1.5 mm square apertures on a 1.7 mm pitch, a
64 mm x 64 mm x 10 mm LYSO crystal, a 0.5 mm optical gel layer, and a
1 mm SiPM slab.
The collimator is modeled as an air envelope containing placed Pb septa and
border bars, so the holes are air gaps without nested boolean subtraction.

The Geant4 stage intentionally records energy deposits instead of generating
scintillation optical photons. The ROOT output tree is named `tree_chroma` and
uses the same column names expected by the existing Chroma ROOT reader.

## Build and Smoke Test

```bash
source /opt/geant4_10.5/install/bin/geant4.sh
mkdir -p build output
cd build
cmake -DGeant4_DIR=/opt/geant4_10.5/install/lib/Geant4-10.5.1 ..
cmake --build . -j2
./G4SPECT ../mac/tc99m_beam_smoke.mac
```

Clinical SPECT commonly uses Tc-99m, modeled here as a 140.5 keV gamma source.
`mac/tc99m_beam_smoke.mac` is a directed smoke test. `mac/tc99m_point_iso.mac`
is the more physical isotropic point-source macro and should be run with more
events because the collimator rejects most gammas.
