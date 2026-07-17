import re
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def read_text(relative_path):
    return (REPO / relative_path).read_text(encoding="utf-8")


class DetectorGeometryConfigTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.detector = read_text("src/SpectDetectorConstruction.cc")
        cls.header = read_text("include/SpectDetectorConstruction.hh")
        cls.event_action = read_text("src/SpectEventAction.cc")
        cls.sensitive_detector = read_text("src/SpectSensitiveDetector.cc")
        cls.run_action = read_text("src/SpectRunAction.cc")
        cls.main = read_text("G4SPECT.cc")
        cls.cmake = read_text("CMakeLists.txt")
        cls.dicom_header_path = REPO / "include" / "SpectDicomPhantom.hh"
        cls.dicom_source_path = REPO / "src" / "SpectDicomPhantom.cc"
        cls.dicom_header = (
            cls.dicom_header_path.read_text(encoding="utf-8")
            if cls.dicom_header_path.exists()
            else ""
        )
        cls.dicom_source = (
            cls.dicom_source_path.read_text(encoding="utf-8")
            if cls.dicom_source_path.exists()
            else ""
        )
        cls.macros = {
            path.name: path.read_text(encoding="utf-8")
            for path in (REPO / "mac").glob("*.mac")
        }
        cls.readme = read_text("README.md")
        cls.running = read_text("RUNNING_G4SPECT.md")
        cls.html = read_text("visualization/SPECT_geometry_3D.html")

    def assertContainsRegex(self, text, pattern):
        self.assertRegex(text, re.compile(pattern, re.MULTILINE))

    def test_detector_uses_lyso_material_and_sensitive_volume_names(self):
        combined = "\n".join(
            [
                self.detector,
                self.header,
                self.event_action,
                self.sensitive_detector,
                self.run_action,
            ]
        )

        self.assertIn("BuildLYSO", self.detector)
        self.assertIn('new G4Material("LYSO", 7.10*g/cm3, 4)', self.detector)
        self.assertIn('new G4Box("LYSO_solid"', self.detector)
        self.assertIn('"LYSO_log"', self.detector)
        self.assertIn('"LYSO_phys"', self.detector)
        self.assertIn("/SPECT/LYSOSD", self.detector)
        self.assertIn("lysoHitsCollection", self.sensitive_detector)
        self.assertIn("lysoHitsCollection", self.event_action)
        self.assertIn("LYSO energy-deposition hits for Chroma", self.run_action)

        self.assertNotIn("BuildLSO", combined)
        self.assertNotIn("fLSO", combined)
        self.assertNotIn("lsoHitsCollection", combined)

    def test_detector_geometry_matches_clinical_like_patch(self):
        self.assertContainsRegex(self.detector, r"detectorXY\s*=\s*64\.0\*mm")
        self.assertContainsRegex(self.detector, r"lysoThickness\s*=\s*10\.0\*mm")
        self.assertIn("G4SPECT_DETECTOR_DISTANCE_MM", self.detector)
        self.assertContainsRegex(self.detector, r"return\s+1000\.0\s*\*\s*mm")
        self.assertContainsRegex(
            self.detector,
            r"detectorFrontZ\s*\+\s*detectorStackFrontOffset\s*\+\s*lysoThickness/2\.0",
        )
        self.assertContainsRegex(
            self.detector,
            r"detectorFrontZ\s*\+\s*detectorStackFrontOffset\s*\+\s*lysoThickness\s*\+\s*gelThickness/2\.0",
        )
        self.assertContainsRegex(
            self.detector,
            r"detectorFrontZ\s*\+\s*detectorStackFrontOffset\s*\+\s*lysoThickness\s*\+\s*gelThickness\s*\n\s*\+\s*sipmThickness/2\.0",
        )
        self.assertContainsRegex(self.detector, r"collimatorXY\s*=\s*64\.0\*mm")
        self.assertContainsRegex(self.detector, r"collimatorLength\s*=\s*35\.0\*mm")
        self.assertIn("G4SPECT_ENABLE_COLLIMATOR", self.detector)
        self.assertContainsRegex(
            self.detector,
            r"detectorStackFrontOffset\s*=\s*enableCollimator\s*\?\s*collimatorLength\s*:\s*0\.0\*mm",
        )
        self.assertContainsRegex(
            self.detector,
            r"collimatorCenterZ\s*=\s*detectorFrontZ\s*\+\s*collimatorLength/2\.0",
        )
        self.assertContainsRegex(self.detector, r"holeSize\s*=\s*1\.5\*mm")
        self.assertContainsRegex(self.detector, r"septumThickness\s*=\s*0\.2\*mm")
        self.assertContainsRegex(self.detector, r"halfGrid\s*=\s*18")
        self.assertContainsRegex(self.detector, r"pitch\s*=\s*1\.7\*mm")

    def test_collimator_is_optional_and_uses_placed_lead_septa(self):
        self.assertIn("CollimatorEnabled", self.detector)
        self.assertIn("if (enableCollimator)", self.detector)
        self.assertNotIn("G4SubtractionSolid", self.detector)
        self.assertNotIn("G4SubtractionSolid", self.header)
        self.assertIn('"Collimator_envelope_log"', self.detector)
        self.assertIn('"Collimator_inner_vertical_septum_log"', self.detector)
        self.assertIn('"Collimator_inner_horizontal_septum_log"', self.detector)
        self.assertIn('"Collimator_border_side_log"', self.detector)
        self.assertIn("fWorldMaterial", self.detector)

    def test_macros_use_source_origin_and_lyso_filter(self):
        for name, text in self.macros.items():
            if "/gps/pos/centre" in text:
                self.assertIn("/gps/pos/centre 0 0 0 mm", text, name)

        for name in (
            "export_geometry_tracks_ShowAllBeam.mac",
            "export_geometry_tracks_ShowDetectedBeam.mac",
        ):
            self.assertIn("/vis/scene/add/axes 0 0 0 10 mm", self.macros[name], name)

        detected = self.macros["export_geometry_tracks_ShowDetectedBeam.mac"]
        self.assertIn(
            "/vis/filtering/trajectories/encounteredVolumeFilter-0/add LYSO_phys",
            detected,
        )
        self.assertIn("/gps/ang/type beam1d", detected)
        self.assertIn("/gps/direction 0 0 1", detected)
        self.assertNotIn("LSO_phys", detected)

    def test_docs_and_local_view_reference_lyso_geometry(self):
        for label, text in {
            "README.md": self.readme,
            "RUNNING_G4SPECT.md": self.running,
            "SPECT_geometry_3D.html": self.html,
        }.items():
            self.assertIn("LYSO", text, label)
            self.assertIn("64 mm", text, label)
            self.assertIn("35 mm", text, label)

        self.assertIn("1.5 mm", self.running)
        self.assertIn("1.7 mm", self.running)
        self.assertIn("LYSO_phys", self.running)
        self.assertIn("LYSO sensitive volume", self.html)

    def test_dicom_phantom_is_optional_geometry_not_sensitive_output(self):
        self.assertTrue(self.dicom_header_path.exists())
        self.assertTrue(self.dicom_source_path.exists())
        self.assertIn("SpectDicomPhantom.cc", self.cmake)
        self.assertIn("#include \"SpectDicomPhantom.hh\"", self.detector)
        self.assertIn("SpectDetectorConstruction(G4bool enableDicomPhantom", self.header)
        self.assertIn("SpectDicomPhantom dicomPhantom", self.detector)
        self.assertIn("dicomPhantom.Construct", self.detector)
        self.assertIn("--dicom-phantom", self.main)
        self.assertIn("G4SPECT_ENABLE_DICOM_PHANTOM", self.main)
        self.assertIn("G4SPECT_DICOM_PATH", self.dicom_source)
        self.assertIn("DICOM_PhantomContainer_phys", self.dicom_source)
        self.assertIn("DICOM_PhantomVoxel_phys", self.dicom_source)
        self.assertIn("G4PVParameterised", self.dicom_source)
        self.assertIn("G4PhantomParameterisation", self.dicom_source)
        self.assertNotIn("SetSensitiveDetector", self.dicom_source)
        self.assertNotIn("G4PSDoseDeposit", self.dicom_source)

    def test_dicom_phantom_run_docs_explain_lyso_only_output(self):
        self.assertIn("--dicom-phantom", self.running)
        self.assertIn("DICOM", self.running)
        self.assertIn("人体", self.running)
        self.assertIn("LYSO", self.running)
        self.assertIn("tree_chroma", self.running)
        self.assertIn("G4SPECT_ENABLE_COLLIMATOR", self.running)
        self.assertIn("默认不构建准直器", self.running)

    def test_dicom_voxel_visualization_is_opt_in_to_keep_blender_responsive(self):
        self.assertIn("G4SPECT_SHOW_DICOM_VOXELS", self.dicom_source)
        self.assertIn("showDicomVoxels", self.dicom_source)
        self.assertIn("voxelVis->SetVisibility(showDicomVoxels)", self.dicom_source)
        self.assertIn("voxelVis->SetForceSolid(showDicomVoxels)", self.dicom_source)
        self.assertIn("默认不显示每个 DICOM voxel", self.running)
        self.assertIn("G4SPECT_SHOW_DICOM_VOXELS=1", self.running)


if __name__ == "__main__":
    unittest.main()
