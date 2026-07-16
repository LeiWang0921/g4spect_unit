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
        self.assertContainsRegex(self.detector, r"lysoCenterZ\s*=\s*140\.0\*mm")
        self.assertContainsRegex(self.detector, r"gelCenterZ\s*=\s*145\.25\*mm")
        self.assertContainsRegex(self.detector, r"sipmCenterZ\s*=\s*146\.0\*mm")
        self.assertContainsRegex(self.detector, r"collimatorXY\s*=\s*64\.0\*mm")
        self.assertContainsRegex(self.detector, r"collimatorLength\s*=\s*35\.0\*mm")
        self.assertContainsRegex(self.detector, r"collimatorCenterZ\s*=\s*117\.5\*mm")
        self.assertContainsRegex(self.detector, r"holeSize\s*=\s*1\.5\*mm")
        self.assertContainsRegex(self.detector, r"septumThickness\s*=\s*0\.2\*mm")
        self.assertContainsRegex(self.detector, r"halfGrid\s*=\s*18")
        self.assertContainsRegex(self.detector, r"pitch\s*=\s*1\.7\*mm")

    def test_collimator_uses_placed_lead_septa_not_nested_booleans(self):
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


if __name__ == "__main__":
    unittest.main()
