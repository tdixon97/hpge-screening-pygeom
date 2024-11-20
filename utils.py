import pyg4ometry
from collections.abc import Generator
from dataclasses import dataclass
from itertools import groupby
from pathlib import Path
from typing import Literal
from pyg4ometry.gdml.Defines import Auxiliary
import pyg4ometry.geant4 as g4


def visualise(
    wl: pyg4ometry.geant4.LogicalVolume,
    logical_detector: pyg4ometry.geant4.LogicalVolume | list,
):
    v = pyg4ometry.visualisation.VtkViewerColouredNew()
    v.addLogicalVolume(wl)

    if isinstance(logical_detector, list):
        for ld in logical_detector:
            vtmp = v.instanceVisOptions[ld.name][0]
            vtmp.colour = ld.pygeom_color_rgba[0:3]
            vtmp.alpha = ld.pygeom_color_rgba[3]
    else:
        vtmp = v.instanceVisOptions[logical_detector.name][0]
        vtmp.colour = logical_detector.pygeom_color_rgba[0:3]
        vtmp.alpha = logical_detector.pygeom_color_rgba[3]

    # set the colors

    v.buildPipelinesAppend()
    v.view()


def _color_macro_recursive(lv: g4.LogicalVolume, macro_lines: dict) -> None:
    if hasattr(lv, "pygeom_color_rgba") and lv.name not in macro_lines:
        mac = f"/vis/geometry/set/forceSolid {lv.name}\n"
        if lv.pygeom_color_rgba is False or lv.pygeom_color_rgba[3] == 0:
            mac += f"/vis/geometry/set/visibility {lv.name} -1 false\n"
        else:
            rgba = " ".join([str(c) for c in lv.pygeom_color_rgba])
            mac += f"/vis/geometry/set/colour {lv.name} 0 {rgba}\n"
        macro_lines[lv.name] = mac

    for pv in lv.daughterVolumes:
        if pv.type == "placement":
            _color_macro_recursive(pv.logicalVolume, macro_lines)


def generate_color_macro(registry: g4.Registry, filename: str) -> None:
    """Create a Geant4 macro file containing the defined visualization attributes."""
    macro_lines = {}
    _color_macro_recursive(registry.worldVolume, macro_lines)
    macro_contents = "".join(macro_lines.values())

    with Path.open(filename, "w", encoding="utf-8") as f:
        f.write(macro_contents)


@dataclass
class RemageDetectorInfo:
    detector_type: Literal["optical", "germanium", "scintillator"]
    uid: int


def walk_detectors(
    pv: g4.PhysicalVolume | g4.LogicalVolume | g4.Registry,
) -> Generator[tuple[g4.PhysicalVolume, RemageDetectorInfo], None, None]:
    if isinstance(pv, g4.PhysicalVolume) and hasattr(pv, "pygeom_active_dector"):
        det = pv.pygeom_active_dector
        assert isinstance(det, RemageDetectorInfo)
        yield pv, det

    if isinstance(pv, g4.LogicalVolume):
        next_v = pv
    if isinstance(pv, g4.PhysicalVolume):
        next_v = pv.logicalVolume
    elif isinstance(pv, g4.Registry):
        next_v = pv.worldVolume
    else:
        msg = "invalid type encountered in walk_detectors volume tree"
        raise TypeError(msg)

    for dv in next_v.daughterVolumes:
        if dv.type == "placement":
            yield from walk_detectors(dv)


def generate_detector_macro(registry: g4.Registry, filename: str) -> None:
    """Create a Geant4 macro file containing the defined active detector volumes for use in remage."""

    macro_lines = {}

    for pv, det in walk_detectors(registry):
        if pv.name in macro_lines:
            return
        mac = f"/RMG/Geometry/RegisterDetector {det.detector_type.title()} {pv.name} {det.uid}\n"
        macro_lines[pv.name] = mac

    macro_contents = "".join(macro_lines.values())

    with Path.open(filename, "w", encoding="utf-8") as f:
        f.write(macro_contents)


def append_detector_auxvals(registry: g4.Registry) -> None:
    """Append an auxiliary structure, storing the sensitive detector volume information.

    The structure is a nested dict, stored as follows (read ``auxtype`: ``auxvalue``):

    * "RMG_detector": ``det_type`` (see :class:`RemageDetectorInfo`)
        * ``physvol->name``: ``det_uid``
        * [...repeat...]
    * [...repeat...]
    """

    written_pvs = set()
    group_it = groupby(walk_detectors(registry), lambda d: d[1].detector_type)

    for key, group in group_it:
        group_aux = Auxiliary("RMG_detector", key, registry)

        for pv, det in group:
            if pv.name in written_pvs:
                return
            written_pvs.add(pv.name)

            group_aux.addSubAuxiliary(
                Auxiliary(pv.name, det.uid, registry, addRegistry=False)
            )
