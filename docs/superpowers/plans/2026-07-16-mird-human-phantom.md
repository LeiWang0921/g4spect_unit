# MIRD Human Phantom Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a recognizable, low-memory, MIRD-style analytical human phantom to `g4spect_unit` for gamma attenuation/scatter studies.

**Architecture:** Implement a new optional `SpectMirdHumanPhantom` geometry module that creates only semi-transparent outer body solids. `G4SPECT.cc` parses `--human-phantom` and passes a boolean into `SpectDetectorConstruction`, which constructs either no phantom, the existing DICOM phantom, or the new analytical human phantom.

**Tech Stack:** Geant4 10.5 C++, existing `unittest` static tests, existing VRML/OBJ export workflow.

## Global Constraints

- The human phantom is not a sensitive detector.
- ROOT output remains LYSO-only in `tree_chroma`.
- Internal organs are not modeled or visualized in this first implementation.
- Visualization uses stable physical volume names and a small number of solids.
- `ShowAllBeam` with `/gps/ang/type iso` is the default human-phantom visualization workflow.

---

### Task 1: Add Tests For Human Phantom Integration

**Files:**
- Modify: `tests/test_detector_geometry_config.py`

**Interfaces:**
- Produces expected symbols: `SpectMirdHumanPhantom.hh`, `SpectMirdHumanPhantom.cc`, `--human-phantom`, `G4SPECT_ENABLE_HUMAN_PHANTOM`, `HumanPhantom_Trunk_phys`, `HumanPhantom_Head_phys`, `HumanPhantom_LeftLeg_phys`, `HumanPhantom_RightLeg_phys`.

- [ ] **Step 1: Write the failing test**

Add assertions that the new module exists, is conditionally constructed, has stable physical volume names, uses a tissue-equivalent material, and does not call `SetSensitiveDetector`.

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m unittest tests.test_detector_geometry_config.DetectorGeometryConfigTest.test_mird_human_phantom_is_optional_outer_geometry_not_sensitive_output -v
```

Expected: fail because the new module and flags do not exist.

### Task 2: Implement MIRD Outer Phantom Geometry

**Files:**
- Create: `include/SpectMirdHumanPhantom.hh`
- Create: `src/SpectMirdHumanPhantom.cc`
- Modify: `src/SpectDetectorConstruction.cc`
- Modify: `include/SpectDetectorConstruction.hh`
- Modify: `G4SPECT.cc`
- Modify: `CMakeLists.txt`

**Interfaces:**
- `SpectMirdHumanPhantom::Construct(G4LogicalVolume* worldLogical)`
- `SpectDetectorConstruction(G4bool enableDicomPhantom = false, G4bool enableHumanPhantom = false)`

- [ ] **Step 1: Implement `SpectMirdHumanPhantom`**

Create low-volume outer-body solids:

- trunk: `G4EllipticalTube`, semi-transparent soft tissue
- head: `G4Ellipsoid`, semi-transparent soft tissue
- left/right legs: `G4EllipticalTube`, semi-transparent soft tissue

- [ ] **Step 2: Wire flags through main and detector construction**

Parse `--human-phantom` and `G4SPECT_ENABLE_HUMAN_PHANTOM`. If both DICOM and MIRD human phantom are requested, fail fast with a clear error.

- [ ] **Step 3: Run tests**

Run:

```bash
python3 -m unittest tests.test_detector_geometry_config tests.test_vrml_to_obj -v
```

Expected: all tests pass.

### Task 3: Build, Export, And Document

**Files:**
- Modify: `RUNNING_G4SPECT.md`

**Interfaces:**
- Visualization command:

```bash
G4VRMLFILE_MAX_FILE_NUM=1 ./G4SPECT --human-phantom ../mac/export_geometry_tracks_ShowAllBeam.mac
python3 ../tools/vrml_to_obj.py
```

- [ ] **Step 1: Build on Geant4 server**

Run:

```bash
cd /RHEL7/home/lwang2/g4spect_unit/build
source /opt/geant4_10.5/install/bin/geant4.sh
cmake --build . -j2
```

- [ ] **Step 2: Run smoke test**

Run:

```bash
./G4SPECT --human-phantom ../mac/tc99m_beam_smoke.mac
```

- [ ] **Step 3: Export ShowAllBeam iso 3D view**

Run:

```bash
G4VRMLFILE_MAX_FILE_NUM=1 ./G4SPECT --human-phantom ../mac/export_geometry_tracks_ShowAllBeam.mac
python3 ../tools/vrml_to_obj.py
```

- [ ] **Step 4: Commit and push**

Commit all source, tests, and docs to `main`, then push to `origin/main`.
