from abakit.lib.Controllers.SqlController import SqlController
from abakit.lib.Controllers.MarkedCellController import MarkedCellController
from abakit.model.annotation_points import CellSources,MarkedCell
import plotly.graph_objects as go
import numpy as np
animal = 'DK41'
controller = SqlController(animal)
cell_controller = MarkedCellController()
resolution = controller.get_resolution(animal)
cells = cell_controller.get_marked_cells(search_dictionary = dict(id = 3586))
# cells = cells*resolution
bin_voxel = [500,500,500]
bins = []
for i,stepi in enumerate(bin_voxel):
    axis_max = cells.max(axis=0)[i]
    axis_bins = list(range(0,int(axis_max)+1,stepi))
    bins.append(axis_bins)
count,bins =np.histogramdd(cells,bins = bins)


fig = go.Figure(data=[go.Scatter3d(x=cells[:,0], y=cells[:,1], z=cells[:,2],
                                   mode='markers')])
fig['layout']['scene']['aspectmode'] = "data"
fig.show()
X, Y, Z = eval(f'np.mgrid[  0:{count.shape[0]*bin_voxel[0]}:{count.shape[0]}j, \
                            0:{count.shape[1]*bin_voxel[1]}:{count.shape[1]}j, \
                            0:{count.shape[2]*bin_voxel[2]}:{count.shape[2]}j]')
fig = go.Figure(data=go.Volume(
    x=X.flatten(),
    y=Y.flatten(),
    z=Z.flatten(),
    value=count.flatten(),
    isomin=1,
    isomax=100,
    opacity=0.1, # needs to be small to see through all surfaces
    surface_count=80, # needs to be a large number for good volume rendering
    ))
fig['layout']['scene']['aspectmode'] = "data"
fig.show()

data = []
data.append(go.Scatter3d(x=cells[:,0], y=cells[:,1], z=cells[:,2],marker=dict(size=5,opacity=0.8),
                                   mode='markers'))
data.append(go.Volume(
    x=X.flatten(),
    y=Y.flatten(),
    z=Z.flatten(),
    value=count.flatten(),
    isomin=1,
    isomax=100,
    opacity=0.1, # needs to be small to see through all surfaces
    surface_count=80, # needs to be a large number for good volume rendering
    ))
fig = go.Figure(data=data)
fig['layout']['scene']['aspectmode'] = "data"
fig.show()

print()