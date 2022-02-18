import vtk
import os
import sys
from pathlib import Path

PIPELINE_ROOT = Path('./src').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())

from lib.FileLocationManager import DATA_PATH
from lib.utilities_atlas import save_mesh_stl

ATLAS_PATH = os.path.join(DATA_PATH, 'atlas_data', 'atlasV8')

INPUT = os.path.join(ATLAS_PATH, 'mesh')
files = sorted(os.listdir(INPUT))

def transformPolyData(actor):
    polyData = vtk.vtkPolyData()
    polyData.DeepCopy(actor.GetMapper().GetInput())
    transform = vtk.vtkTransform()
    transform.SetMatrix(actor.GetMatrix())
    fil = vtk.vtkTransformPolyDataFilter()
    fil.SetTransform(transform)
    fil.SetInputDataObject(polyData)
    fil.Update()
    polyData.DeepCopy(fil.GetOutput())
    return polyData;

reader = vtk.vtkSTLReader()
filename = os.path.join(INPUT, 'SC.stl')
reader.SetFileName(filename)

mapper = vtk.vtkPolyDataMapper()
if vtk.VTK_MAJOR_VERSION <= 5:
    mapper.SetInput(reader.GetOutput())
else:
    mapper.SetInputConnection(reader.GetOutputPort())


actor = vtk.vtkActor()
actor.SetMapper(mapper)
actor.SetPosition([0.0, 0.0, 0.0])
actor.SetScale([1.0, 1.0, 1.0])

actor.GetProperty().SetColor(1.0,0,1.0)

polyData = transformPolyData(actor)

stlWriter = vtk.vtkSTLWriter()
stlWriter.SetFileName('/home/eddyod/SC.stl')
stlWriter.SetInputData(polyData)
stlWriter.Write()
