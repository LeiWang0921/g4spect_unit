import importlib.util
from pathlib import Path
import tempfile
import os
import unittest


PROJECT_DIR = Path(__file__).resolve().parents[1]
CONVERTER = PROJECT_DIR / "tools" / "vrml_to_obj.py"


def load_converter():
    spec = importlib.util.spec_from_file_location("vrml_to_obj", CONVERTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VrmlToObjTests(unittest.TestCase):
    def _write_box_vrml(self, path, z_value):
        path.write_text(
            f"""#VRML V2.0 utf8
#---------- SOLID: LatestBox.0
Shape {{
  geometry IndexedFaceSet {{
    coord Coordinate {{
      point [
        0 0 {z_value},
        1 0 {z_value},
        0 1 {z_value},
      ]
    }}
    coordIndex [
      0, 1, 2, -1,
    ]
  }}
}}
""",
            encoding="utf-8",
        )

    def test_converts_geant4_indexed_face_sets_to_obj_objects(self):
        converter = load_converter()
        sample_vrml = """#VRML V2.0 utf8
#---------- SOLID: BoxA.0
Shape {
  appearance Appearance {
    material Material {
      diffuseColor 1 0 0
      transparency 0.25
    }
  }
  geometry IndexedFaceSet {
    coord Coordinate {
      point [
        0 0 0,
        1 0 0,
        1 1 0,
        0 1 0,
      ]
    }
    coordIndex [
      0, 1, 2, 3, -1,
    ]
  }
}
#---------- SOLID: BoxB.0
Shape {
  geometry IndexedFaceSet {
    coord Coordinate {
      point [
        0 0 1,
        1 0 1,
        0 1 1,
      ]
    }
    coordIndex [
      0, 1, 2, -1,
    ]
  }
}
"""

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            src = tmp_path / "sample.wrl"
            obj = tmp_path / "sample.obj"
            src.write_text(sample_vrml, encoding="utf-8")

            shapes = converter.parse_vrml(src)
            converter.write_obj(shapes, obj)

            obj_text = obj.read_text(encoding="utf-8")
            mtl_text = obj.with_suffix(".mtl").read_text(encoding="utf-8")

        self.assertEqual([shape.name for shape in shapes], ["BoxA.0", "BoxB.0"])
        self.assertEqual(sum(len(shape.points) for shape in shapes), 7)
        self.assertEqual(sum(len(shape.faces) for shape in shapes), 2)
        self.assertIn("o BoxA.0", obj_text)
        self.assertIn("o BoxB.0", obj_text)
        self.assertIn("f 1 2 3 4", obj_text)
        self.assertIn("f 5 6 7", obj_text)
        self.assertIn("newmtl BoxA_0", mtl_text)
        self.assertIn("Kd 1 0 0", mtl_text)

    def test_converts_geant4_indexed_line_sets_to_obj_lines(self):
        converter = load_converter()
        sample_vrml = """#VRML V2.0 utf8
#---------- SOLID: SourceAxes.0
Shape {
  appearance Appearance {
    material Material {
      diffuseColor 1 1 0
    }
  }
  geometry IndexedLineSet {
    coord Coordinate {
      point [
        0 0 0,
        0 0 10,
        1 0 0,
      ]
    }
    coordIndex [
      0, 1, -1,
      0, 2, -1,
    ]
  }
}
"""

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            src = tmp_path / "sample_lines.wrl"
            obj = tmp_path / "sample_lines.obj"
            src.write_text(sample_vrml, encoding="utf-8")

            shapes = converter.parse_vrml(src)
            converter.write_obj(shapes, obj)

            obj_text = obj.read_text(encoding="utf-8")
            mtl_text = obj.with_suffix(".mtl").read_text(encoding="utf-8")

        self.assertEqual([shape.name for shape in shapes], ["SourceAxes.0"])
        self.assertEqual(sum(len(shape.points) for shape in shapes), 3)
        self.assertEqual(sum(len(shape.lines) for shape in shapes), 2)
        self.assertIn("o SourceAxes.0", obj_text)
        self.assertIn("l 1 2", obj_text)
        self.assertIn("l 1 3", obj_text)
        self.assertIn("newmtl SourceAxes_0", mtl_text)
        self.assertIn("Kd 1 1 0", mtl_text)

    def test_converts_geant4_polylines_to_named_visible_trajectory_objects(self):
        converter = load_converter()
        sample_vrml = """#VRML V2.0 utf8
#---------- SOLID: G4AxesModel
Shape {
  appearance Appearance {
    material Material {
      diffuseColor 1 1 1
    }
  }
  geometry IndexedFaceSet {
    coord Coordinate {
      point [
        0 0 0,
        1 0 0,
        0 1 0,
      ]
    }
    coordIndex [
      0, 1, 2, -1,
    ]
  }
}
#---------- POLYLINE
Shape {
  appearance Appearance {
    material Material {
      diffuseColor 1 1 0
      emissiveColor 1 1 0
    }
  }
  geometry IndexedLineSet {
    coord Coordinate {
      point [
        0 0 0,
        0 0 135,
        0 0 140,
      ]
    }
    coordIndex [
      0, 1, 2, -1,
    ]
  }
}
#---------- 3D MARKER (Circle)
Anchor {
 description "(0  0  0)"
 children [
  Shape {
   appearance Appearance {
    material Material {
     diffuseColor 1 1 0
    }
   }
   geometry Sphere {
    radius 0.25
   }
  }
 ]
}
#---------- POLYLINE
Shape {
  appearance Appearance {
    material Material {
      diffuseColor 0 0 1
      emissiveColor 0 0 1
    }
  }
  geometry IndexedLineSet {
    coord Coordinate {
      point [
        0 0 140,
        0.1 0 140,
      ]
    }
    coordIndex [
      0, 1, -1,
    ]
  }
}
"""

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            src = tmp_path / "tracks.wrl"
            obj = tmp_path / "tracks.obj"
            src.write_text(sample_vrml, encoding="utf-8")

            shapes = converter.parse_vrml(src)
            converter.write_obj(shapes, obj)

            obj_text = obj.read_text(encoding="utf-8")
            mtl_text = obj.with_suffix(".mtl").read_text(encoding="utf-8")

        self.assertEqual(
            [shape.name for shape in shapes],
            ["G4AxesModel", "gamma_primary_001", "electron_001"],
        )
        self.assertIn("o gamma_primary_001", obj_text)
        self.assertIn("o electron_001", obj_text)
        self.assertIn("l ", obj_text)
        self.assertIn("f ", obj_text)
        self.assertIn("newmtl gamma_primary_001", mtl_text)
        self.assertIn("Kd 1 1 0", mtl_text)
        self.assertIn("newmtl electron_001", mtl_text)
        self.assertIn("Kd 0 0 1", mtl_text)

    def test_conversion_writes_blender_grouping_script_for_events(self):
        converter = load_converter()
        sample_vrml = """#VRML V2.0 utf8
#---------- SOLID: LYSO_phys.0
Shape {
  geometry IndexedFaceSet {
    coord Coordinate {
      point [
        0 0 0,
        1 0 0,
        0 1 0,
      ]
    }
    coordIndex [
      0, 1, 2, -1,
    ]
  }
}
#---------- SOLID: G4AxesModel
Shape {
  geometry IndexedFaceSet {
    coord Coordinate {
      point [
        0 0 0,
        1 0 0,
        0 1 0,
      ]
    }
    coordIndex [
      0, 1, 2, -1,
    ]
  }
}
#---------- POLYLINE
Shape {
  appearance Appearance {
    material Material {
      diffuseColor 1 1 0
    }
  }
  geometry IndexedLineSet {
    coord Coordinate {
      point [
        0 0 0,
        0 0 135,
      ]
    }
    coordIndex [
      0, 1, -1,
    ]
  }
}
#---------- POLYLINE
Shape {
  appearance Appearance {
    material Material {
      diffuseColor 0 0 1
    }
  }
  geometry IndexedLineSet {
    coord Coordinate {
      point [
        0 0 135,
        0.1 0 135,
      ]
    }
    coordIndex [
      0, 1, -1,
    ]
  }
}
#---------- POLYLINE
Shape {
  appearance Appearance {
    material Material {
      diffuseColor 1 1 0
    }
  }
  geometry IndexedLineSet {
    coord Coordinate {
      point [
        0 0 0,
        0 0 140,
      ]
    }
    coordIndex [
      0, 1, -1,
    ]
  }
}
"""

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            src = tmp_path / "tracks.wrl"
            obj = tmp_path / "tracks.obj"
            src.write_text(sample_vrml, encoding="utf-8")

            exit_code = converter.main(
                [str(src), str(obj)], default_copy_target=None
            )

            script = obj.with_name("import_tracks_blender.py")
            script_text = script.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertIn('"detector_geometry"', script_text)
        self.assertIn('"source_axes"', script_text)
        self.assertIn('"event_001"', script_text)
        self.assertIn('"event_002"', script_text)
        self.assertIn('"gamma_primary_001"', script_text)
        self.assertIn('"electron_001"', script_text)
        self.assertIn('"gamma_primary_002"', script_text)
        self.assertIn(str(obj.resolve()), script_text)
        self.assertIn("def resolve_obj_path()", script_text)

    def test_blender_import_script_preserves_detector_transparency(self):
        converter = load_converter()
        sample_vrml = """#VRML V2.0 utf8
#---------- SOLID: LYSO_phys.0
Shape {
  appearance Appearance {
    material Material {
      diffuseColor 0 0.7 1
      transparency 0.7
    }
  }
  geometry IndexedFaceSet {
    coord Coordinate {
      point [
        0 0 0,
        1 0 0,
        0 1 0,
      ]
    }
    coordIndex [
      0, 1, 2, -1,
    ]
  }
}
#---------- SOLID: OpticalGel_phys.0
Shape {
  appearance Appearance {
    material Material {
      diffuseColor 0.8 1 1
      transparency 0.7
    }
  }
  geometry IndexedFaceSet {
    coord Coordinate {
      point [
        0 0 1,
        1 0 1,
        0 1 1,
      ]
    }
    coordIndex [
      0, 1, 2, -1,
    ]
  }
}
"""

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            src = tmp_path / "transparent_detector.wrl"
            obj = tmp_path / "transparent_detector.obj"
            src.write_text(sample_vrml, encoding="utf-8")

            exit_code = converter.main(
                [str(src), str(obj)], default_copy_target=None
            )

            mtl_text = obj.with_suffix(".mtl").read_text(encoding="utf-8")
            script_text = obj.with_name("import_tracks_blender.py").read_text(
                encoding="utf-8"
            )

        self.assertEqual(exit_code, 0)
        self.assertIn("newmtl LYSO_phys_0", mtl_text)
        self.assertIn("d 0.3", mtl_text)
        self.assertIn("newmtl OpticalGel_phys_0", mtl_text)
        self.assertIn('"LYSO_phys_0": 0.300000', script_text)
        self.assertIn('"OpticalGel_phys_0": 0.300000', script_text)
        self.assertIn("def configure_material_transparency()", script_text)
        self.assertIn('material.blend_method = "BLEND"', script_text)
        self.assertIn("configure_material_transparency()", script_text)

    def test_default_line_tube_radius_is_thin(self):
        converter = load_converter()

        self.assertEqual(converter.LINE_TUBE_RADIUS, 0.005)

    def test_default_copy_target_uses_local_visualization_directory(self):
        converter = load_converter()

        self.assertEqual(
            converter.DEFAULT_COPY_TARGET,
            "Leiwa@10.90.70.110:/E:/SPECT/geometry_exports/",
        )
        self.assertEqual(
            converter.DEFAULT_LOCAL_EXPORT_DIR,
            r"E:\SPECT\geometry_exports",
        )

    def test_no_argument_mode_copies_latest_build_wrl_to_tracks_exports(self):
        converter = load_converter()

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            build = project / "build"
            tools = project / "tools"
            exports = project / "geometry_exports"
            build.mkdir()
            tools.mkdir()

            older = build / "g4_01.wrl"
            newer = build / "g4_02.wrl"
            self._write_box_vrml(older, 1)
            self._write_box_vrml(newer, 2)
            os.utime(older, (1000, 1000))
            os.utime(newer, (2000, 2000))

            script_path = tools / "vrml_to_obj.py"
            exit_code = converter.main(
                [], script_path=script_path, default_copy_target=None
            )

            copied_wrl = exports / "spect_geometry_tracks.wrl"
            obj = exports / "spect_geometry_tracks.obj"
            mtl = exports / "spect_geometry_tracks.mtl"

            self.assertEqual(exit_code, 0)
            self.assertTrue(copied_wrl.exists())
            self.assertTrue(obj.exists())
            self.assertTrue(mtl.exists())
            self.assertIn("0 0 2", copied_wrl.read_text(encoding="utf-8"))
            self.assertIn("v 0 0 2", obj.read_text(encoding="utf-8"))

    def test_no_argument_mode_prefers_stable_g4_00_wrl_when_present(self):
        converter = load_converter()

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            build = project / "build"
            tools = project / "tools"
            exports = project / "geometry_exports"
            build.mkdir()
            tools.mkdir()

            stable = build / "g4_00.wrl"
            newer = build / "g4_02.wrl"
            self._write_box_vrml(stable, 0)
            self._write_box_vrml(newer, 2)
            os.utime(stable, (1000, 1000))
            os.utime(newer, (2000, 2000))

            script_path = tools / "vrml_to_obj.py"
            exit_code = converter.main(
                [], script_path=script_path, default_copy_target=None
            )

            copied_wrl = exports / "spect_geometry_tracks.wrl"
            obj = exports / "spect_geometry_tracks.obj"

            self.assertEqual(exit_code, 0)
            self.assertIn("0 0 0", copied_wrl.read_text(encoding="utf-8"))
            self.assertIn("v 0 0 0", obj.read_text(encoding="utf-8"))

    def test_no_argument_mode_copies_to_default_target(self):
        converter = load_converter()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project = tmp_path / "project"
            build = project / "build"
            tools = project / "tools"
            destination = tmp_path / "local_exports"
            build.mkdir(parents=True)
            tools.mkdir()
            self._write_box_vrml(build / "g4_00.wrl", 5)

            script_path = tools / "vrml_to_obj.py"
            old_target = os.environ.pop("G4SPECT_COPY_TO", None)
            try:
                exit_code = converter.main(
                    [],
                    script_path=script_path,
                    default_copy_target=str(destination),
                )
            finally:
                if old_target is not None:
                    os.environ["G4SPECT_COPY_TO"] = old_target

            self.assertEqual(exit_code, 0)
            self.assertTrue((destination / "spect_geometry_tracks.wrl").exists())
            self.assertTrue((destination / "spect_geometry_tracks.obj").exists())
            self.assertTrue((destination / "spect_geometry_tracks.mtl").exists())
            self.assertIn(
                "v 0 0 5",
                (destination / "spect_geometry_tracks.obj").read_text(encoding="utf-8"),
            )

    def test_copy_to_copies_wrl_obj_and_mtl_after_conversion(self):
        converter = load_converter()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            src = tmp_path / "sample.wrl"
            obj = tmp_path / "sample.obj"
            destination = tmp_path / "local_exports"
            self._write_box_vrml(src, 3)

            exit_code = converter.main(
                [str(src), str(obj), "--copy-to", str(destination)]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue((destination / "sample.wrl").exists())
            self.assertTrue((destination / "sample.obj").exists())
            self.assertTrue((destination / "sample.mtl").exists())
            self.assertTrue((destination / "import_tracks_blender.py").exists())
            self.assertIn("0 0 3", (destination / "sample.wrl").read_text(encoding="utf-8"))
            self.assertIn("v 0 0 3", (destination / "sample.obj").read_text(encoding="utf-8"))

    def test_copy_to_can_be_set_with_environment_variable(self):
        converter = load_converter()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project = tmp_path / "project"
            build = project / "build"
            tools = project / "tools"
            destination = tmp_path / "local_exports"
            build.mkdir(parents=True)
            tools.mkdir()
            self._write_box_vrml(build / "g4_00.wrl", 4)

            script_path = tools / "vrml_to_obj.py"
            old_target = os.environ.get("G4SPECT_COPY_TO")
            os.environ["G4SPECT_COPY_TO"] = str(destination)
            try:
                exit_code = converter.main([], script_path=script_path)
            finally:
                if old_target is None:
                    os.environ.pop("G4SPECT_COPY_TO", None)
                else:
                    os.environ["G4SPECT_COPY_TO"] = old_target

            self.assertEqual(exit_code, 0)
            self.assertTrue((destination / "spect_geometry_tracks.wrl").exists())
            self.assertTrue((destination / "spect_geometry_tracks.obj").exists())
            self.assertTrue((destination / "spect_geometry_tracks.mtl").exists())
            self.assertIn(
                "v 0 0 4",
                (destination / "spect_geometry_tracks.obj").read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
