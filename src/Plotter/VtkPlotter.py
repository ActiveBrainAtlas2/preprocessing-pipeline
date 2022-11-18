import vtk
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkRenderer
)
from vtkmodules.vtkCommonColor import vtkNamedColors

class VtkPlotter:

    def plot_poly_data(self,polydata):
        colors = vtkNamedColors()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(polydata)
        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetDiffuse(0.8)
        actor.GetProperty().SetDiffuseColor(colors.GetColor3d('LightSteelBlue'))
        actor.GetProperty().SetSpecular(0.3)
        actor.GetProperty().SetSpecularPower(60.0)

        ren = vtkRenderer()
        ren.AddActor(actor)
        ren.SetBackground(colors.GetColor3d('DarkOliveGreen'))

        renWin = vtkRenderWindow()
        renWin.AddRenderer(ren)
        renWin.SetWindowName('ReadSTL')

        iren = vtkRenderWindowInteractor()
        iren.SetRenderWindow(renWin)
        iren.Initialize()
        renWin.Render()
        iren.Start()


