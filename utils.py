import pyg4ometry

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
