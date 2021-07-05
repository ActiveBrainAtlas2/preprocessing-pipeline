#%%
import sys
sys.path.append('/home/zhw272/programming/pipeline_utility')
from notebooks.Will.toolbox.IOs.get_calculated_transforms import get_demons_transform
import numpy as np
import plotly.graph_objects as go

def get_point_list(grid):
    x,y,z = grid.shape[1:]
    point_list = []
    for xi in range(x):
        for yi in range(y):
            for zi in range(z):
                point_list.append(grid[xi,yi,zi])
    return point_list 

def transform_grid(grid):
    transformed_grid = np.zeros(grid.shape)
    x,y,z = grid.shape[1:]
    for xi in range(x):
        for yi in range(y):
            for zi in range(z):
                pointi = grid[:,xi,yi,zi]
                transformed_pointi = demons_transform.TransformPoint(pointi)
                transformed_grid[:,xi,yi,zi] = transformed_pointi
    return transformed_grid

def get_changed_points(grid,grid_diff):
    # changed_grid = np.zeros(grid_diff.shape)
    changed_points = []
    x,y,z = grid_diff.shape[1:]
    for xi in range(x):
        for yi in range(y):
            for zi in range(z):
                pointi = grid_diff[:,xi,yi,zi]
                if np.any(pointi!=0):
                    changed_points.append(grid[:,xi,yi,zi])
    return np.asarray(changed_points)

def get_mesh_grid():
    xstart = -500
    ystart = -500
    zstart = -500
    xend = 500
    yend = 500
    zend = 500
    ndots = 50
    grid = np.mgrid[xstart:xend:(xend-xstart)/ndots,
                    ystart:yend:(yend-ystart)/ndots,
                    zstart:zend:(zend-zstart)/ndots]
    return grid

def plot_grid(grid):
    fig = go.Figure(data=[go.Scatter3d(x=grid[0].flatten(), y=grid[1].flatten(), z=grid[2].flatten(),mode='markers',marker=dict(
            size=3))])
    fig.show()

def plot_changed_points(changed_points):
    fig = go.Figure(data=[go.Scatter3d(x=changed_points[:,0], y=changed_points[:,1], z=changed_points[:,2],mode='markers',marker=dict(
                size=3))])
    fig.show()

#%%
demons_transform = get_demons_transform('DK39')
Size = np.array([435, 262, 117])
Spacing = np.array([41.6, 41.6, 80])
Origin = np.array([31.2, 26, 40])
#%%
grid = get_mesh_grid()
#%%
transformed_grid = transform_grid(grid)
grid_diff= transformed_grid - grid
changed_points = get_changed_points(grid,grid_diff)
plot_changed_points(changed_points)

# %%
demons_transform.TransformPoint([32.2,27,41])
# %%
