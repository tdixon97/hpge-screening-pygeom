"""
Basic project to simulate a Germanium detector using pyg4ometry
Author: Toby Dixon (toby.dixon.23@ucl.ac.uk)
"""

import pyg4ometry
from legendhpges import make_hpge
from l200geom import det_utils
from l200geom import vis_utils

import json
from dataclasses import dataclass
from typing import Literal
from pyg4ometry import visualisation
import argparse
import numpy as np
import logging
from pathlib import Path

# LOGGER SETTINGS
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s: %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


    
def visualise(wl:pyg4ometry.geant4.LogicalVolume,logical_detector:pyg4ometry.geant4.LogicalVolume|list):

    v = pyg4ometry.visualisation.VtkViewerColouredNew()
    v.addLogicalVolume(wl)

    if (isinstance(logical_detector,list)):
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




parser = argparse.ArgumentParser(
        prog="hpge-screening-pygeom",
        description="%(prog)s command line interface",
    )

parser.add_argument(
    "--name", "-n", type=str, help="Name of detector", default="ic"
)


parser.add_argument(
    "--vis", "-v", type=int, help="Visualize the detector", default=1
)

parser.add_argument(
    "--out", "-o", type=str, help="Output GDML file name", default=None
)

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
macro =   args.macro
vis_macro=args.vis_macro

if (name not in ["ic","bege"]):
    raise ValueError(f"{name} is not implemented as a detector name")

with open(f"cfg/test_{name}.json", 'r') as file:
    metadata = json.load(file)


# make the world
reg  = pyg4ometry.geant4.Registry()                                                                                                                                       
ws   = pyg4ometry.geant4.solid.Box("ws",400,400,400,reg)
wl   = pyg4ometry.geant4.LogicalVolume(ws,"G4_Galactic","wl",reg)
reg.setWorld(wl)


# use the legendhpge package to make the detector
logical_detector  = make_hpge(metadata,name="det_log",registry=reg)
logical_detector.pygeom_color_rgba = (0, 1, 1, 0.2)
physical_detector = pyg4ometry.geant4.PhysicalVolume([0,0,0],[0,0,0],logical_detector,"det_phy",wl,reg)
physical_detector.pygeom_active_dector = det_utils.RemageDetectorInfo("germanium", "001")

# also add a source
source = pyg4ometry.geant4.solid.Tubs("source",0,2,1,0,2*np.pi,reg,"mm")
logical_source = pyg4ometry.geant4.LogicalVolume(source,"G4_Fe","source_log",reg)
logical_source.pygeom_color_rgba = (1, 0.2, 0, 1)
physical_source = pyg4ometry.geant4.PhysicalVolume([0,0,0],[-100,0,40],logical_source,"source_phy",wl,reg)

# visualise
if (is_vis):
    visualise(wl,[logical_source,logical_detector])

# save gdml
if (out_gdml is not None):
    w = pyg4ometry.gdml.Writer()
    w.addDetector(reg)
    w.write(out_gdml)

if (macro is not None):
    det_utils.generate_detector_macro(reg,Path(macro))


if (vis_macro is not None):
    vis_utils.generate_color_macro(reg,Path(vis_macro))