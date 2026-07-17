#!/usr/bin/env python3
"""Convert Geant4 VRML2FILE IndexedFaceSet/IndexedLineSet output to OBJ/MTL."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from textwrap import dedent


FLOAT_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
INT_RE = re.compile(r"-?\d+")
DEFAULT_BUILD_WRL = "g4_00.wrl"
COPY_TARGET_ENV = "G4SPECT_COPY_TO"
DEFAULT_COPY_TARGET = "Leiwa@10.90.70.110:/E:/SPECT/geometry_exports/"
DEFAULT_LOCAL_EXPORT_DIR = r"E:\SPECT\geometry_exports"
LINE_TUBE_RADIUS = 0.005
DICOM_PATH_ENV = "G4SPECT_DICOM_PATH"
DICOM_FILES_ENV = "G4SPECT_DICOM_FILES"
DICOM_PREVIEW_STRIDE_ENV = "G4SPECT_DICOM_PREVIEW_STRIDE"
DICOM_SHOW_VOXELS_ENV = "G4SPECT_SHOW_DICOM_VOXELS"
DEFAULT_DICOM_PATH = Path("/opt/geant4_10.5/examples/extended/medical/DICOM")
DEFAULT_DICOM_FILES = ("1.g4dcm", "2.g4dcm", "3.g4dcm")
DEFAULT_DICOM_PREVIEW_STRIDE = 8


class Shape:
    def __init__(self, name: str, kind: str = "solid") -> None:
        self.name = name
        self.kind = kind
        self.points: list[tuple[float, float, float]] = []
        self.faces: list[list[int]] = []
        self.lines: list[list[int]] = []
        self.diffuse: tuple[float, float, float] = (0.8, 0.8, 0.8)
        self.transparency: float = 0.0


class DicomSlice:
    def __init__(
        self,
        material_names: list[str],
        nx: int,
        ny: int,
        nz: int,
        min_x: float,
        max_x: float,
        min_y: float,
        max_y: float,
        min_z: float,
        max_z: float,
        material_ids: list[int],
    ) -> None:
        self.material_names = material_names
        self.nx = nx
        self.ny = ny
        self.nz = nz
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y
        self.min_z = min_z
        self.max_z = max_z
        self.material_ids = material_ids


def _floats(text: str) -> list[float]:
    return [float(match.group(0)) for match in FLOAT_RE.finditer(text)]


def _ints(text: str) -> list[int]:
    return [int(match.group(0)) for match in INT_RE.finditer(text)]


def _safe_name(name: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_]+", "_", name)
    return safe.strip("_") or "material"


def _env_flag_enabled(name: str) -> bool:
    value = os.environ.get(name, "")
    return bool(value) and value not in {"0", "false", "FALSE"}


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name, "")
    if not value:
        return default
    try:
        parsed = int(value)
    except ValueError:
        return default
    return max(1, parsed)


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _close_rgb(
    left: tuple[float, float, float], right: tuple[float, float, float]
) -> bool:
    return all(abs(a - b) < 1e-6 for a, b in zip(left, right))


def _is_source_point(point: tuple[float, float, float]) -> bool:
    x, y, z = point
    return abs(x) < 1e-6 and abs(y) < 1e-6 and abs(z) < 1e-6


def _name_polylines(shapes: list[Shape]) -> None:
    counters: dict[str, int] = {}
    for shape in shapes:
        if shape.kind != "polyline":
            continue

        if _close_rgb(shape.diffuse, (1.0, 1.0, 0.0)):
            if shape.points and _is_source_point(shape.points[0]):
                prefix = "gamma_primary"
            else:
                prefix = "gamma_secondary"
        elif _close_rgb(shape.diffuse, (0.0, 0.0, 1.0)):
            prefix = "electron"
        elif _close_rgb(shape.diffuse, (0.0, 1.0, 1.0)):
            prefix = "positron"
        else:
            prefix = "polyline"

        counters[prefix] = counters.get(prefix, 0) + 1
        shape.name = f"{prefix}_{counters[prefix]:03d}"


def parse_vrml(path: Path) -> list[Shape]:
    shapes: list[Shape] = []
    current: Shape | None = None
    in_points = False
    in_indices = False
    indices_are_lines = False
    index_group: list[int] = []
    polyline_index = 0

    def finish_shape() -> None:
        if current is not None and current.points and (current.faces or current.lines):
            shapes.append(current)

    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()

            if line.startswith("#---------- SOLID:"):
                finish_shape()
                current = Shape(line.split("SOLID:", 1)[1].strip())
                in_points = False
                in_indices = False
                indices_are_lines = False
                index_group = []
                continue

            if line.startswith("#---------- POLYLINE"):
                finish_shape()
                polyline_index += 1
                current = Shape(f"Polyline.{polyline_index}", kind="polyline")
                in_points = False
                in_indices = False
                indices_are_lines = True
                index_group = []
                continue

            if line.startswith("#---------- 3D MARKER"):
                finish_shape()
                current = None
                in_points = False
                in_indices = False
                indices_are_lines = False
                index_group = []
                continue

            if current is None:
                continue

            if line.startswith("diffuseColor"):
                values = _floats(line)
                if len(values) >= 3:
                    current.diffuse = (values[0], values[1], values[2])
                continue

            if line.startswith("transparency"):
                values = _floats(line)
                if values:
                    current.transparency = values[0]
                continue

            if "point [" in line:
                in_points = True
                continue

            if "geometry IndexedLineSet" in line:
                indices_are_lines = True
                continue

            if "geometry IndexedFaceSet" in line:
                indices_are_lines = False
                continue

            if "coordIndex [" in line:
                in_indices = True
                index_group = []
                continue

            if in_points:
                values = _floats(line)
                if len(values) >= 3:
                    current.points.append((values[0], values[1], values[2]))
                if "]" in line:
                    in_points = False
                continue

            if in_indices:
                for index in _ints(line):
                    if index == -1:
                        if indices_are_lines and len(index_group) >= 2:
                            current.lines.append(index_group)
                        elif not indices_are_lines and len(index_group) >= 3:
                            current.faces.append(index_group)
                        index_group = []
                    else:
                        index_group.append(index)
                if "]" in line:
                    if indices_are_lines and len(index_group) >= 2:
                        current.lines.append(index_group)
                    elif not indices_are_lines and len(index_group) >= 3:
                        current.faces.append(index_group)
                    index_group = []
                    in_indices = False

    finish_shape()
    _name_polylines(shapes)
    return shapes


def _read_g4dcm(path: Path) -> DicomSlice:
    tokens = path.read_text(encoding="utf-8").split()
    cursor = 0

    def next_token() -> str:
        nonlocal cursor
        if cursor >= len(tokens):
            raise ValueError(f"Unexpected end of DICOM phantom file: {path}")
        token = tokens[cursor]
        cursor += 1
        return token

    n_materials = int(next_token())
    material_names = [""] * n_materials
    for _ in range(n_materials):
        material_id = int(next_token())
        material_name = next_token()
        if material_id < 0 or material_id >= n_materials:
            raise ValueError(f"Invalid material ID in DICOM phantom file: {path}")
        material_names[material_id] = material_name

    nx = int(next_token())
    ny = int(next_token())
    nz = int(next_token())
    min_x = float(next_token())
    max_x = float(next_token())
    min_y = float(next_token())
    max_y = float(next_token())
    min_z = float(next_token())
    max_z = float(next_token())

    n_voxels = nx * ny * nz
    material_ids = [int(next_token()) for _ in range(n_voxels)]
    return DicomSlice(
        material_names,
        nx,
        ny,
        nz,
        min_x,
        max_x,
        min_y,
        max_y,
        min_z,
        max_z,
        material_ids,
    )


def _dicom_slice_paths() -> list[Path]:
    data_path = Path(os.environ.get(DICOM_PATH_ENV, str(DEFAULT_DICOM_PATH)))
    file_names = _split_csv(os.environ.get(DICOM_FILES_ENV, ""))
    if not file_names:
        file_names = list(DEFAULT_DICOM_FILES)
    return [data_path / file_name for file_name in file_names]


def _load_dicom_slices() -> list[DicomSlice]:
    paths = _dicom_slice_paths()
    if not paths or not all(path.exists() for path in paths):
        return []
    slices = [_read_g4dcm(path) for path in paths]
    slices.sort(key=lambda item: item.min_z)
    return slices


def _merge_dicom_slices(slices: list[DicomSlice]) -> DicomSlice:
    if not slices:
        raise ValueError("No DICOM slices to merge")
    first = slices[0]
    material_ids: list[int] = []
    total_nz = 0
    min_z = first.min_z
    max_z = first.max_z
    for item in slices:
        if (
            item.nx != first.nx
            or item.ny != first.ny
            or item.min_x != first.min_x
            or item.max_x != first.max_x
            or item.min_y != first.min_y
            or item.max_y != first.max_y
            or item.material_names != first.material_names
        ):
            raise ValueError("DICOM slices use inconsistent dimensions or materials")
        total_nz += item.nz
        min_z = min(min_z, item.min_z)
        max_z = max(max_z, item.max_z)
        material_ids.extend(item.material_ids)
    return DicomSlice(
        first.material_names,
        first.nx,
        first.ny,
        total_nz,
        first.min_x,
        first.max_x,
        first.min_y,
        first.max_y,
        min_z,
        max_z,
        material_ids,
    )


def _material_is_air(name: str) -> bool:
    normalized = name.strip().lower()
    return normalized in {"air", "g4_air"}


def _add_quad(
    shape: Shape,
    corners: list[tuple[float, float, float]],
) -> None:
    offset = len(shape.points)
    shape.points.extend(corners)
    shape.faces.append([offset, offset + 1, offset + 2, offset + 3])


def _build_dicom_preview_shape(dicom: DicomSlice, stride: int) -> Shape | None:
    air_material_ids = {
        index
        for index, material_name in enumerate(dicom.material_names)
        if _material_is_air(material_name)
    }
    if not air_material_ids:
        air_material_ids = {0}

    bins_x = math.ceil(dicom.nx / stride)
    bins_y = math.ceil(dicom.ny / stride)
    bins_z = math.ceil(dicom.nz / stride)
    occupied: set[tuple[int, int, int]] = set()

    def material_id_at(ix: int, iy: int, iz: int) -> int:
        index = iz * dicom.nx * dicom.ny + iy * dicom.nx + ix
        return dicom.material_ids[index]

    for bz in range(bins_z):
        z0 = bz * stride
        z1 = min((bz + 1) * stride, dicom.nz)
        for by in range(bins_y):
            y0 = by * stride
            y1 = min((by + 1) * stride, dicom.ny)
            for bx in range(bins_x):
                x0 = bx * stride
                x1 = min((bx + 1) * stride, dicom.nx)
                is_occupied = any(
                    material_id_at(ix, iy, iz) not in air_material_ids
                    for iz in range(z0, z1)
                    for iy in range(y0, y1)
                    for ix in range(x0, x1)
                )
                if is_occupied:
                    occupied.add((bx, by, bz))

    if not occupied:
        return None

    half_x = (dicom.max_x - dicom.min_x) * 0.5
    half_y = (dicom.max_y - dicom.min_y) * 0.5
    half_z = (dicom.max_z - dicom.min_z) * 0.5
    voxel_x = (dicom.max_x - dicom.min_x) / dicom.nx
    voxel_y = (dicom.max_y - dicom.min_y) / dicom.ny
    voxel_z = (dicom.max_z - dicom.min_z) / dicom.nz

    def bounds(bx: int, by: int, bz: int) -> tuple[float, float, float, float, float, float]:
        x0_index = bx * stride
        x1_index = min((bx + 1) * stride, dicom.nx)
        y0_index = by * stride
        y1_index = min((by + 1) * stride, dicom.ny)
        z0_index = bz * stride
        z1_index = min((bz + 1) * stride, dicom.nz)
        return (
            -half_x + x0_index * voxel_x,
            -half_x + x1_index * voxel_x,
            -half_y + y0_index * voxel_y,
            -half_y + y1_index * voxel_y,
            -half_z + z0_index * voxel_z,
            -half_z + z1_index * voxel_z,
        )

    shape = Shape("DICOM_PhantomPreview", kind="solid")
    shape.diffuse = (0.86, 0.63, 0.43)
    shape.transparency = 0.35
    neighbors = [
        (-1, 0, 0),
        (1, 0, 0),
        (0, -1, 0),
        (0, 1, 0),
        (0, 0, -1),
        (0, 0, 1),
    ]

    for bx, by, bz in sorted(occupied):
        x0, x1, y0, y1, z0, z1 = bounds(bx, by, bz)
        for dx, dy, dz in neighbors:
            if (bx + dx, by + dy, bz + dz) in occupied:
                continue
            if dx == -1:
                _add_quad(shape, [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)])
            elif dx == 1:
                _add_quad(shape, [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)])
            elif dy == -1:
                _add_quad(shape, [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)])
            elif dy == 1:
                _add_quad(shape, [(x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)])
            elif dz == -1:
                _add_quad(shape, [(x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)])
            elif dz == 1:
                _add_quad(shape, [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)])
    return shape


def add_dicom_preview_shape(shapes: list[Shape]) -> list[Shape]:
    has_dicom_container = any(
        shape.name.startswith("DICOM_PhantomContainer") for shape in shapes
    )
    if not has_dicom_container or _env_flag_enabled(DICOM_SHOW_VOXELS_ENV):
        return shapes

    slices = _load_dicom_slices()
    if not slices:
        return shapes
    preview = _build_dicom_preview_shape(
        _merge_dicom_slices(slices),
        _env_int(DICOM_PREVIEW_STRIDE_ENV, DEFAULT_DICOM_PREVIEW_STRIDE),
    )
    if preview is None:
        return shapes

    filtered = [
        shape
        for shape in shapes
        if not shape.name.startswith("DICOM_PhantomContainer")
    ]
    return filtered + [preview]


def _sub(
    left: tuple[float, float, float], right: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (left[0] - right[0], left[1] - right[1], left[2] - right[2])


def _add(
    left: tuple[float, float, float], right: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (left[0] + right[0], left[1] + right[1], left[2] + right[2])


def _scale(
    vector: tuple[float, float, float], value: float
) -> tuple[float, float, float]:
    return (vector[0] * value, vector[1] * value, vector[2] * value)


def _cross(
    left: tuple[float, float, float], right: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _norm(vector: tuple[float, float, float]) -> float:
    return math.sqrt(vector[0] ** 2 + vector[1] ** 2 + vector[2] ** 2)


def _normalize(
    vector: tuple[float, float, float]
) -> tuple[float, float, float] | None:
    length = _norm(vector)
    if length <= 1e-12:
        return None
    return _scale(vector, 1.0 / length)


def _tube_vertices(
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    radius: float,
) -> list[tuple[float, float, float]]:
    direction = _normalize(_sub(end, start))
    if direction is None:
        return []

    reference = (0.0, 0.0, 1.0)
    if abs(direction[2]) > 0.9:
        reference = (0.0, 1.0, 0.0)
    u = _normalize(_cross(direction, reference))
    if u is None:
        return []
    v = _normalize(_cross(direction, u))
    if v is None:
        return []

    u = _scale(u, radius)
    v = _scale(v, radius)
    offsets = [
        _add(u, v),
        _sub(u, v),
        _scale(_add(u, v), -1.0),
        _sub(v, u),
    ]
    return [_add(start, offset) for offset in offsets] + [
        _add(end, offset) for offset in offsets
    ]


def write_obj(shapes: list[Shape], obj_path: Path) -> None:
    obj_path.parent.mkdir(parents=True, exist_ok=True)
    mtl_path = obj_path.with_suffix(".mtl")
    vertex_offset = 1

    with obj_path.open("w", encoding="utf-8", newline="\n") as obj:
        obj.write("# Converted from Geant4 VRML2FILE output\n")
        obj.write(f"mtllib {mtl_path.name}\n")
        for shape in shapes:
            material_name = _safe_name(shape.name)
            obj.write(f"\no {shape.name}\n")
            obj.write(f"usemtl {material_name}\n")
            shape_vertex_offset = vertex_offset
            extra_vertex_count = 0
            for x, y, z in shape.points:
                obj.write(f"v {x:g} {y:g} {z:g}\n")
            for face in shape.faces:
                indices = [str(index + shape_vertex_offset) for index in face]
                obj.write("f " + " ".join(indices) + "\n")
            for line in shape.lines:
                indices = [str(index + shape_vertex_offset) for index in line]
                obj.write("l " + " ".join(indices) + "\n")
                if shape.kind == "polyline":
                    for start_index, end_index in zip(line, line[1:]):
                        tube = _tube_vertices(
                            shape.points[start_index],
                            shape.points[end_index],
                            LINE_TUBE_RADIUS,
                        )
                        if not tube:
                            continue
                        tube_offset = (
                            shape_vertex_offset
                            + len(shape.points)
                            + extra_vertex_count
                        )
                        for x, y, z in tube:
                            obj.write(f"v {x:g} {y:g} {z:g}\n")
                        obj.write(
                            f"f {tube_offset} {tube_offset + 1} "
                            f"{tube_offset + 5} {tube_offset + 4}\n"
                        )
                        obj.write(
                            f"f {tube_offset + 1} {tube_offset + 2} "
                            f"{tube_offset + 6} {tube_offset + 5}\n"
                        )
                        obj.write(
                            f"f {tube_offset + 2} {tube_offset + 3} "
                            f"{tube_offset + 7} {tube_offset + 6}\n"
                        )
                        obj.write(
                            f"f {tube_offset + 3} {tube_offset} "
                            f"{tube_offset + 4} {tube_offset + 7}\n"
                        )
                        obj.write(
                            f"f {tube_offset} {tube_offset + 3} "
                            f"{tube_offset + 2} {tube_offset + 1}\n"
                        )
                        obj.write(
                            f"f {tube_offset + 4} {tube_offset + 5} "
                            f"{tube_offset + 6} {tube_offset + 7}\n"
                        )
                        extra_vertex_count += len(tube)
            vertex_offset += len(shape.points) + extra_vertex_count

    with mtl_path.open("w", encoding="utf-8", newline="\n") as mtl:
        mtl.write("# Converted from Geant4 VRML2FILE materials\n")
        written: set[str] = set()
        for shape in shapes:
            material_name = _safe_name(shape.name)
            if material_name in written:
                continue
            written.add(material_name)
            r, g, b = shape.diffuse
            opacity = max(0.0, min(1.0, 1.0 - shape.transparency))
            mtl.write(f"\nnewmtl {material_name}\n")
            mtl.write(f"Kd {r:g} {g:g} {b:g}\n")
            mtl.write(f"d {opacity:g}\n")


def event_collections(shapes: list[Shape]) -> dict[str, list[str]]:
    collections: dict[str, list[str]] = {
        "detector_geometry": [],
        "source_axes": [],
    }
    current_event: str | None = None
    event_count = 0

    for shape in shapes:
        if shape.name.startswith("G4AxesModel"):
            collections["source_axes"].append(shape.name)
        elif shape.name.startswith("gamma_primary_"):
            event_count += 1
            current_event = f"event_{event_count:03d}"
            collections[current_event] = [shape.name]
        elif shape.name.startswith(("electron_", "gamma_secondary_", "positron_")):
            if current_event is None:
                current_event = "event_000"
                collections.setdefault(current_event, [])
            collections[current_event].append(shape.name)
        else:
            collections["detector_geometry"].append(shape.name)

    return {name: objects for name, objects in collections.items() if objects}


def material_opacities(shapes: list[Shape]) -> dict[str, float]:
    opacities: dict[str, float] = {}
    for shape in shapes:
        opacity = max(0.0, min(1.0, 1.0 - shape.transparency))
        if opacity < 0.999:
            opacities[_safe_name(shape.name)] = opacity
    return opacities


def _python_float_dict(values: dict[str, float]) -> str:
    if not values:
        return "{}"
    lines = ["{"]
    for key in sorted(values):
        lines.append(f"  {json.dumps(key)}: {values[key]:.6f},")
    lines.append("}")
    return "\n".join(lines)


def write_blender_import_script(
    obj_path: Path, shapes: list[Shape], script_path: Path | None = None
) -> Path:
    target = script_path or obj_path.with_name("import_tracks_blender.py")
    groups = event_collections(shapes)
    groups_json = json.dumps(groups, indent=2)
    material_opacity_literal = _python_float_dict(material_opacities(shapes))
    absolute_obj_paths = [str(obj_path.resolve())]
    default_local_obj = f"{DEFAULT_LOCAL_EXPORT_DIR}\\{obj_path.name}"
    if default_local_obj not in absolute_obj_paths:
        absolute_obj_paths.append(default_local_obj)
    absolute_obj_paths_literal = "[\n" + ",\n".join(
        f'  r"{path.replace(chr(34), chr(92) + chr(34))}"'
        for path in absolute_obj_paths
    ) + "\n]"
    script = f"""\
import bpy
from pathlib import Path

OBJ_NAME = {obj_path.name!r}
ABSOLUTE_OBJ_PATHS = {absolute_obj_paths_literal}
GROUPS = {groups_json}
MATERIAL_OPACITY = {material_opacity_literal}


def blender_path(path):
    if hasattr(bpy, "path"):
        return Path(bpy.path.abspath(path)).resolve()
    return Path(path).resolve()


def script_directory_candidates():
    directories = []
    text = getattr(getattr(bpy.context, "space_data", None), "text", None)
    filepath = getattr(text, "filepath", "") if text is not None else ""
    if filepath:
        directories.append(blender_path(filepath).parent)
    for text_block in bpy.data.texts:
        filepath = getattr(text_block, "filepath", "")
        if filepath:
            directories.append(blender_path(filepath).parent)
    try:
        directories.append(Path(__file__).resolve().parent)
    except Exception:
        pass
    unique = []
    seen = set()
    for directory in directories:
        key = str(directory)
        if key not in seen:
            seen.add(key)
            unique.append(directory)
    return unique


def resolve_obj_path():
    candidates = [Path(path) for path in ABSOLUTE_OBJ_PATHS]
    candidates.extend(directory / OBJ_NAME for directory in script_directory_candidates())
    for candidate in candidates:
        if candidate.exists():
            return candidate
    checked = "\\n".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(f"Could not find {{OBJ_NAME}}. Checked:\\n{{checked}}")


def ensure_collection(name, parent=None):
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
    parent_collection = parent or bpy.context.scene.collection
    if collection.name not in parent_collection.children.keys():
        parent_collection.children.link(collection)
    return collection


def move_object_to_collection(obj, collection):
    if obj.name not in collection.objects.keys():
        collection.objects.link(obj)
    for old_collection in list(obj.users_collection):
        if old_collection != collection:
            old_collection.objects.unlink(obj)


def import_obj(path):
    before = set(bpy.data.objects)
    if hasattr(bpy.ops.wm, "obj_import"):
        bpy.ops.wm.obj_import(filepath=str(path))
    else:
        bpy.ops.import_scene.obj(filepath=str(path))
    return [obj for obj in bpy.data.objects if obj not in before]


def material_key_candidates(name):
    candidates = [name]
    if "." in name:
        base, suffix = name.rsplit(".", 1)
        if suffix.isdigit():
            candidates.append(base)
    return candidates


def apply_alpha_to_material(material, alpha):
    alpha = max(0.0, min(1.0, alpha))
    color = getattr(material, "diffuse_color", None)
    if color is not None and len(color) >= 3:
        material.diffuse_color = (color[0], color[1], color[2], alpha)

    if hasattr(material, "blend_method"):
        material.blend_method = "BLEND"
    if hasattr(material, "show_transparent_back"):
        material.show_transparent_back = True
    if hasattr(material, "surface_render_method"):
        try:
            material.surface_render_method = "BLENDED"
        except Exception:
            pass

    if getattr(material, "use_nodes", False) and material.node_tree is not None:
        for node in material.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED" and "Alpha" in node.inputs:
                node.inputs["Alpha"].default_value = alpha


def configure_material_transparency():
    for material in bpy.data.materials:
        alpha = None
        for key in material_key_candidates(material.name):
            if key in MATERIAL_OPACITY:
                alpha = MATERIAL_OPACITY[key]
                break
        if alpha is None:
            color = getattr(material, "diffuse_color", None)
            if color is not None and len(color) >= 4 and color[3] < 0.999:
                alpha = color[3]
        if alpha is not None and alpha < 0.999:
            apply_alpha_to_material(material, alpha)


def main():
    obj_path = resolve_obj_path()
    imported = import_obj(obj_path)
    configure_material_transparency()
    root = ensure_collection("spect_geometry_tracks")
    imported_by_key = {{}}
    for obj in imported:
        keys = {{obj.name}}
        if "." in obj.name:
            maybe_suffix = obj.name.rsplit(".", 1)[1]
            if maybe_suffix.isdigit():
                keys.add(obj.name.rsplit(".", 1)[0])
        for key in keys:
            imported_by_key.setdefault(key, []).append(obj)
    for collection_name, object_names in GROUPS.items():
        collection = ensure_collection(collection_name, root)
        for object_name in object_names:
            matches = imported_by_key.get(object_name, [])
            if not matches and "." in object_name:
                matches = imported_by_key.get(object_name.rsplit(".", 1)[0], [])
            if not matches:
                continue
            obj = matches.pop(0)
            for key_matches in imported_by_key.values():
                if key_matches and key_matches[0] == obj:
                    key_matches.pop(0)
            if obj is not None:
                move_object_to_collection(obj, collection)


main()
"""
    target.write_text(dedent(script), encoding="utf-8", newline="\n")
    return target


def find_latest_wrl(build_dir: Path) -> Path | None:
    candidates = list(build_dir.glob("*.wrl"))
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def find_build_wrl(build_dir: Path) -> Path | None:
    stable = build_dir / DEFAULT_BUILD_WRL
    if stable.exists():
        return stable
    return find_latest_wrl(build_dir)


def convert_wrl(
    input_path: Path,
    output_path: Path,
    line_radius: float = LINE_TUBE_RADIUS,
) -> tuple[int, int, int, int]:
    global LINE_TUBE_RADIUS
    previous_radius = LINE_TUBE_RADIUS
    LINE_TUBE_RADIUS = line_radius
    shapes = parse_vrml(input_path)
    shapes = add_dicom_preview_shape(shapes)
    try:
        if not shapes:
            raise ValueError(f"No IndexedFaceSet or IndexedLineSet shapes found in {input_path}")
        write_obj(shapes, output_path)
        write_blender_import_script(output_path, shapes)
    finally:
        LINE_TUBE_RADIUS = previous_radius
    point_count = sum(len(shape.points) for shape in shapes)
    face_count = sum(len(shape.faces) for shape in shapes)
    line_count = sum(len(shape.lines) for shape in shapes)
    return len(shapes), point_count, face_count, line_count


def is_scp_target(target: str) -> bool:
    if re.match(r"^[A-Za-z]:[\\/]", target):
        return False
    return ":" in target


def copy_outputs(files: list[Path], target: str) -> None:
    if is_scp_target(target):
        subprocess.run(
            [
                "scp",
                "-p",
                "-o",
                "ConnectTimeout=10",
                *[str(path) for path in files],
                target,
            ],
            check=True,
        )
        return

    destination = Path(target)
    destination.mkdir(parents=True, exist_ok=True)
    for path in files:
        shutil.copy2(path, destination / path.name)


def main(
    argv: list[str],
    script_path: Path | None = None,
    default_copy_target: str | None = DEFAULT_COPY_TARGET,
) -> int:
    parser = argparse.ArgumentParser(
        description="Convert a Geant4 VRML2FILE .wrl file to OBJ/MTL."
    )
    parser.add_argument(
        "--copy-to",
        help=(
            "Copy the generated .wrl, .obj, and .mtl files to this directory or "
            f"SCP target. Can also be set with {COPY_TARGET_ENV}."
        ),
    )
    parser.add_argument(
        "--line-radius",
        type=float,
        default=LINE_TUBE_RADIUS,
        help=(
            "Radius in Geant4/VRML units for visible mesh tubes generated around "
            f"trajectory polylines. Default: {LINE_TUBE_RADIUS:g}."
        ),
    )
    parser.add_argument(
        "input",
        type=Path,
        nargs="?",
        help="Input Geant4 .wrl file. If omitted, use the latest build/*.wrl.",
    )
    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        help="Output .obj path; defaults to input path with .obj suffix",
    )
    args = parser.parse_args(argv)

    no_argument_mode = args.input is None
    if no_argument_mode:
        script = script_path or Path(__file__).resolve()
        project_dir = script.parent.parent
        source_wrl = find_build_wrl(project_dir / "build")
        if source_wrl is None:
            print(f"No .wrl files found in {project_dir / 'build'}", file=sys.stderr)
            return 1
        export_dir = project_dir / "geometry_exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        input_path = export_dir / "spect_geometry_tracks.wrl"
        output = export_dir / "spect_geometry_tracks.obj"
        shutil.copy2(source_wrl, input_path)
        print(f"Source: {source_wrl}")
        print(f"Wrote: {input_path}")
    else:
        input_path = args.input
        output = args.output or args.input.with_suffix(".obj")

    try:
        shape_count, point_count, face_count, line_count = convert_wrl(
            input_path, output, line_radius=args.line_radius
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Wrote: {output}")
    print(f"Wrote: {output.with_suffix('.mtl')}")
    print(f"Wrote: {output.with_name('import_tracks_blender.py')}")
    print(
        f"Converted {shape_count} shapes, {point_count} vertices, "
        f"{face_count} faces, {line_count} lines."
    )
    copy_target = args.copy_to or os.environ.get(COPY_TARGET_ENV)
    if copy_target is None and no_argument_mode:
        copy_target = default_copy_target
    if copy_target:
        files = [
            input_path,
            output,
            output.with_suffix(".mtl"),
            output.with_name("import_tracks_blender.py"),
        ]
        try:
            copy_outputs(files, copy_target)
        except (OSError, subprocess.CalledProcessError) as exc:
            print(f"Copy failed: {exc}", file=sys.stderr)
            return 1
        print(f"Copied outputs to: {copy_target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
