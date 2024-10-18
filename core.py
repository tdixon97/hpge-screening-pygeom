"""
Basic project to simulate a Germanium detector using pyg4ometry
Author: Toby Dixon (toby.dixon.23@ucl.ac.uk)
"""

import pyg4ometry
from legendhpges import make_hpge
import json
from dataclasses import dataclass
from typing import Literal
from pyg4ometry import visualisation
import argparse
@dataclass
class RemageDetectorInfo:
    detector_type: Literal["optical", "germanium"]
    uid: int
    
def visualise(wl:pyg4ometry.geant4.LogicalVolume,logical_detector:pyg4ometry.geant4.LogicalVolume):

    v = pyg4ometry.visualisation.VtkViewerColouredNew()
    v.addLogicalVolume(wl)
    vtmp = v.instanceVisOptions[logical_detector.name][0]
    vtmp.colour = logical_detector.pygeom_color_rgba[0:3]
    vtmp.alpha = logical_detector.pygeom_color_rgba[3]


    # set the colors
   
    v.buildPipelinesAppend()
    v.view()


# make the world
reg  = pyg4ometry.geant4.Registry()

# world solid and logical                                                                                                                                         
ws   = pyg4ometry.geant4.solid.Box("ws",400,400,400,reg)
wl   = pyg4ometry.geant4.LogicalVolume(ws,"G4_Galactic","wl",reg)
reg.setWorld(wl.name)

# define a block of metadata

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
args = parser.parse_args()
name = args.name
is_vis = bool(args.vis)
out_gdml = args.out

if (name not in ["ic","bege"]):
    raise ValueError(f"{name} is not implemented as a detector name")

with open(f"cfg/test_{name}.json", 'r') as file:
    metadata = json.load(file)

# use the legendhpge package to make the detector
logical_detector  = make_hpge(metadata,name="det_log")
logical_detector.pygeom_color_rgba = (0, 1, 1, 1)

# get volume and mass 
print("Volume = ",logical_detector.volume)
print("Mass = ",logical_detector.mass)

# make physical detector
physical_detector = pyg4ometry.geant4.PhysicalVolume([0,0,0],[0,0,0],logical_detector,"det_phy",wl,reg)

# set it as being a sensitivie 
physical_detector.pygeom_active_dector = RemageDetectorInfo("germanium", "001")

# visualise
if (is_vis):
    visualise(wl,logical_detector)

# save gdml
if (out_gdml is not None):
    w = pyg4ometry.gdml.Writer()
    w.addDetector(reg)
    w.write(out_gdml)

