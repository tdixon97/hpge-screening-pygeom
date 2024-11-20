"""
Basic project to simulate a Germanium detector using pyg4ometry
Author: Toby Dixon (toby.dixon.23@ucl.ac.uk)
"""

import pyg4ometry
from legendhpges import make_hpge

import json
import argparse
import numpy as np
import logging
from pathlib import Path
from utils import visualise
import utils

# LOGGER SETTINGS
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s: %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


parser = argparse.ArgumentParser(
    prog="hpge-screening-pygeom",
    description="%(prog)s command line interface",
)

parser.add_argument("--name", "-n", type=str, help="Name of detector", default="ic")


parser.add_argument("--vis", "-v", type=int, help="Visualize the detector", default=1)


parser.add_argument("--n_det", "-N", type=int, help="Number of detectors", default=1)
parser.add_argument("--out", "-o", type=str, help="Output GDML file name", default=None)

parser.add_argument(
    "--macro", "-m", type=str, help="Output macro file name", default=None
)

parser.add_argument(
    "--vis_macro", "-V", type=str, help="Vis macro file name", default=None
)
args = parser.parse_args()
name = args.name
is_vis = bool(args.vis)
out_gdml = args.out
macro = args.macro
vis_macro = args.vis_macro
n_det = args.n_det

if name not in ["ic", "bege"]:
    from legendmeta import LegendMetadata

    lmeta = LegendMetadata()
    try:
        metadata = lmeta.hardware.detectors.germanium.diodes[name]
    except KeyError:
        msg = f"supplied name {name} is neither one of the test configs or present in the legend metadata"
        raise ValueError(msg)
else:
    with open(f"cfg/test_{name}.json", "r") as file:
        metadata = json.load(file)


# make the world
reg = pyg4ometry.geant4.Registry()
ws = pyg4ometry.geant4.solid.Box("ws", 400, 100 * n_det + 1000, 400, reg)
wl = pyg4ometry.geant4.LogicalVolume(ws, "G4_Galactic", "wl", reg)
reg.setWorld(wl)


# use the legendhpge package to make the detector
logs = []
for n in range(n_det):
    logical_detector = make_hpge(metadata, name=f"det_log_{n}", registry=reg)
    logical_detector.pygeom_color_rgba = (0, 1, 1, 0.2)
    logs.append(logical_detector)
    physical_detector = pyg4ometry.geant4.PhysicalVolume(
        [0, 0, 0], [0, 100 * n, 0], logical_detector, f"det_phy_{n}", wl, reg
    )
    physical_detector.pygeom_active_dector = utils.RemageDetectorInfo(
        "germanium", f"00{n}"
    )

# also add a source
source = pyg4ometry.geant4.solid.Tubs("source", 0, 2, 1, 0, 2 * np.pi, reg, "mm")
logical_source = pyg4ometry.geant4.LogicalVolume(source, "G4_Fe", "source_log", reg)
logical_source.pygeom_color_rgba = (1, 0.2, 0, 1)
physical_source = pyg4ometry.geant4.PhysicalVolume(
    [0, 0, 0], [-100, 0, 40], logical_source, "source_phy", wl, reg
)

# visualise
if is_vis:
    logs.append(logical_source)
    visualise(wl, logs)
# save gdml
if out_gdml is not None:
    w = pyg4ometry.gdml.Writer()
    w.addDetector(reg)
    w.write(out_gdml)

if macro is not None:
    utils.generate_detector_macro(reg, Path(macro))


if vis_macro is not None:
    utils.generate_color_macro(reg, Path(vis_macro))
