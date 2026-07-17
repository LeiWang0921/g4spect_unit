# MIRD analytical human phantom design

## Goal

Replace the current default DICOM example slice phantom for visualization-oriented human geometry with a recognizable, clinical-scale analytical human phantom. The human phantom is used as a gamma attenuation/scatter object between the source and SPECT detector, not as a sensitive detector and not as a ROOT output source.

## Selected Approach

Use a simplified MIRD-style analytical outer body built directly in `g4spect_unit`, inspired by Geant4 `examples/advanced/human_phantom`.

This avoids relying on unavailable `DICOM_HEAD` data and avoids importing the full human_phantom application, messenger, scoring, organ sensitivity, GDML, and analysis code. The implementation should build only the outer body envelope needed for attenuation and visualization.

## Geometry

Add a new optional `SpectMirdHumanPhantom` geometry module:

- `Trunk`: elliptical tube, approximately MIRD adult trunk scale.
- `Head`: simplified head envelope using an ellipsoid/tube combination or a single ellipsoid if that is enough for a stable first pass.
- `Legs`: two simplified elliptical tubes or capsules to make the body recognizable as a whole-body phantom.
- Optional shoulders/arms can be added only if needed for visual recognizability and without creating many volumes.

Default placement should put the approximate torso/source region near `(0, 0, 0)` so the GPS source starts inside human-equivalent material. The detector remains along `+z`, with its front distance controlled by `G4SPECT_DETECTOR_DISTANCE_MM`.

## Materials

Use low-risk tissue-equivalent materials for the first implementation:

- Main soft tissue: `G4_WATER` or `G4_TISSUE_SOFT_ICRP` if available.
- Bone-specific internal detail is intentionally not modeled in this first pass.

The purpose is attenuation/scatter realism at the body-envelope level, not organ dose or organ-specific energy deposition.

## Runtime Control

Add an independent enable switch:

- Command line: `--human-phantom`
- Environment: `G4SPECT_ENABLE_HUMAN_PHANTOM=1`

Keep existing DICOM phantom support available but do not enable both by default. If both `--human-phantom` and `--dicom-phantom` are requested, fail fast with a clear message or prefer human phantom with a warning; implementation should choose one explicit behavior and document it.

## Visualization

Only the outer human shell should be visible in Blender/VRML:

- Use a small number of semi-transparent solids.
- Do not show internal organs.
- Do not create per-voxel objects.
- Keep object names stable, for example `HumanPhantom_Trunk_phys`, `HumanPhantom_Head_phys`, `HumanPhantom_LeftLeg_phys`, `HumanPhantom_RightLeg_phys`.

This keeps Blender responsive and gives a recognizable body outline.

## Output Contract

No human phantom volume is a sensitive detector. ROOT output remains LYSO-only:

- `tree_chroma`
- `lysoHitsCollection`
- `LYSO_phys`

## Tests

Add/update tests to verify:

- `SpectMirdHumanPhantom.hh/.cc` exist and are included in CMake.
- `G4SPECT.cc` parses `--human-phantom` and `G4SPECT_ENABLE_HUMAN_PHANTOM`.
- `SpectDetectorConstruction` constructs the human phantom conditionally.
- Human phantom source does not contain `SetSensitiveDetector` or dose scorer code.
- Stable physical volume names are present for visualization grouping.
- `RUNNING_G4SPECT.md` documents human phantom usage and the ShowAllBeam isotropic visualization workflow.

## Non-Goals

- Full CT voxel realism.
- Internal organ scoring.
- Organ-level ROOT output.
- DICOM_HEAD download/integration.
- ORNL/GDML phantom support.
