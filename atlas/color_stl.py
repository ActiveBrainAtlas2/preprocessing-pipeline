import vtk, sys

# Read in your STL file
f = vtk.vtkSTLReader()
f.SetFileName(sys.argv[1])
f.Update() # This is necessary to have the data ready to read.

# The vtkSTLReader reads in your file as a vtkPolyData, 'obj' is a reference to
# that output. I'm using the bounds that are automatically calculated during
# the import phase to give a range for the height of the points in the file.
# I believe that the bounds are (xmin, xmax, ymin, ymax, zmin, zmax).
obj = f.GetOutputDataObject(0)
min_z, max_z = obj.GetBounds()[4:]

# I am creating a lookup table to correspond to the height field. I am using
# the default values. Remember that the lookup table is a rather complex and
# handy object, and there are lots of options to set if you need something
# special.
lut = vtk.vtkLookupTable()
lut.SetTableRange(min_z, max_z)
lut.Build()

# This is an array that I am creating to store the heights of the points. I
# will use this as a scalar field on the 'obj' so that the lookup table can be
# used to color it. You could obviously make the array anything you wanted,
# such as ‘x’ or ‘y’ or squared distance from some other point, for instance.
heights = vtk.vtkDoubleArray()
heights.SetName("Z_Value")

# Loop through the points in the vtkPolyData and record the height in the
# 'heights' array.
for i in range(obj.GetNumberOfPoints()):
    z = obj.GetPoint(i)[-1]
    heights.InsertNextValue(z)

# Add this array to the point data as a scalar.
obj.GetPointData().SetScalars(heights)

# Visualization stuff ... you need to tell the mapper about the scalar field
# and the lookup table. The rest of this is pretty standard stuff.
mapper = vtk.vtkPolyDataMapper()
mapper.SetInputDataObject(obj)
mapper.SetScalarRange(min_z, max_z)
mapper.SetLookupTable(lut)

actor = vtk.vtkActor()
actor.SetMapper(mapper)

renderer = vtk.vtkRenderer()
renderer.AddActor(actor)
renderer.SetBackground(.2, .3, .8)

renw = vtk.vtkRenderWindow()
renw.AddRenderer(renderer)

iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renw)

renw.Render()
iren.Start()
f.Update()
# Write the stl file to disk
stlWriter = vtk.vtkSTLWriter()
stlWriter.SetFileName('junk.stl')

stlWriter.SetInputConnection(f.GetOutputPort())
#stlWriter.SetFileName(outfile)
#stlWriter.SetInput(renderer)

stlWriter.Write()
