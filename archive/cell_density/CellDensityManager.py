import sys
sys.path.append('/scratch/programming/pipeline/pipeline')
from Controllers.SqlController import SqlController
import plotly.graph_objects as go
import numpy as np
import os
from atlas.atlas_manager import Atlas
from atlas.Assembler import Assembler,get_v7_volume_and_origin,get_assembled_atlas_v7
from scipy.ndimage import zoom
import matplotlib.pyplot as plt

class CellDensityManager(SqlController):
    def __init__(self,animal):
        super().__init__(animal)
        self.assembler = get_assembled_atlas_v7()
        self.downsampled_atlas = zoom(self.assembler.combined_volume, (0.1, 0.1, 0.1))
        self.resolution = self.get_resolution(self.animal.prep_id).reshape(-1,1)
        self.transformation = self.get_transformation(source = self.animal.prep_id,destination = 'Atlas', transformation_type = 'Similarity')

    def get_atlas_volume(self):
        controller = SqlController(self.animal.prep_id)
        atlas = Atlas(atlas = 'atlasV7')
        atlas.get_com_array()
        assembler = Assembler(check=False,side = '_R')
        assembler.volumes,assembler.origins = get_v7_volume_and_origin()
        assembler.sqlController = atlas.sqlController
        assembler.structures = list(assembler.volumes.keys())
        segment_to_id = controller.get_segment_to_id_where_segment_are_brain_regions()
        for i in segment_to_id:
            segment_to_id[i]=1
        assembler.assemble_all_structure_volume(segment_to_id)
        return assembler.combined_volume
    
    def plot_3d_volume(self,volume,X,Y,Z,*args,**kwargs):
        return go.Volume(
            x=X.flatten(),
            y=Y.flatten(),
            z=Z.flatten(),
            value=volume.flatten(),
            *args,**kwargs,
            )
    
    def hist3d(self,data):
        origin = np.min(data,axis = 1).astype(int)
        end = np.max(data,axis = 1).astype(int)+1
        data = data - np.min(data,axis = 1).reshape(-1,1)
        shape = np.max(data,axis = 1).astype(int)
        density = np.zeros(shape)
        npoints = data.shape[1]
        for i in range(npoints):
            point = data[:,i].astype(int)-1
            density[point[0],point[1],point[2]] += 1
        return density,origin,end     
    
    def transform_data_to_atlas_space(self,data):
        data = data*self.resolution
        tfdata = self.transformation.forward_transform_points(data.T).T/np.array([10,10,20]).reshape(-1,1)
        tfdata = tfdata*0.1*np.array([1,1,2]).reshape(-1,1)
        return tfdata

    def get_atlas_plot(self,):
        shape = self.downsampled_atlas.shape
        X, Y, Z = eval(f'np.mgrid[  0:{shape[0]}:{shape[0]}j, \
                                        0:{shape[1]}:{shape[1]}j, \
                                        0:{shape[2]*2}:{shape[2]}j]')
        atlas = go.Volume(
                x=X.flatten(),
                y=Y.flatten(),
                z=Z.flatten(),
                value=self.downsampled_atlas.flatten(),
                isomin=1,
                isomax=40,
                opacity=0.5, 
                surface_count=2, )
        return atlas

    def get_density_plot(self,tfdata):
        density,origin,end = self.hist3d(tfdata)
        shape = density.shape
        X, Y, Z = eval(f'np.mgrid[  {origin[0]}:{end[0]}:{shape[0]}j, \
                                        {origin[1]}:{end[1]}:{shape[1]}j, \
                                        {origin[2]}:{end[2]}:{shape[2]}j]')
        cell_density = go.Volume(
                x=X.flatten(),
                y=Y.flatten(),
                z=Z.flatten(),
                value=density.flatten(),
                isomin=1,
                isomax=20,
                opacity=0.5, 
                surface_count=20, )
        return cell_density
    
    def plot_atlas_and_cell(self,data):
        tfdata = self.transform_data_to_atlas_space(data)
        atlas = self.get_atlas_plot()
        cells = go.Scatter3d(x=tfdata[0], y=tfdata[1], z=tfdata[2],marker=dict(size=5,opacity=0.2),
                                           mode='markers')
        fig = go.Figure(data=[atlas,cells])
        fig['layout']['scene']['aspectmode'] = "data"
        fig.update_layout(scene_aspectmode="data", scene_camera_eye=dict (x=1, y=1, z=1))
        fig.show()
        
    def plot_atlas_and_cell_density(self,data):
        tfdata = self.transform_data_to_atlas_space(data)
        atlas = self.get_atlas_plot()
        cell_density = self.get_density_plot(tfdata)
        fig = go.Figure(data=[atlas,cell_density])
        fig['layout']['scene']['aspectmode'] = "data"
        fig.update_layout(scene_aspectmode="data", scene_camera_eye=dict (x=1, y=1, z=1))
        fig.show()
    
    def get_id_to_structure(self,segment_to_id):
        id_to_structure = {}
        ids = list(segment_to_id.values())
        structures = list(segment_to_id.keys())
        for i,id in enumerate(np.unique(ids)):
            index = np.where(ids==id)[0][0]
            structure = structures[index]
            if '_' in structure:
                structure = structure.split('_')[0]
            id_to_structure[id] = structure
        return id_to_structure
    
    def get_cell_count_per_structure(self,data):
        tfdata = self.transform_data_to_atlas_space(data)
        npoints = tfdata.shape[1]
        category = np.ones(npoints)*-1
        for i in range(npoints):
            pointi = tfdata[:,i].astype(int)-1
            if np.all(pointi>0) and np.all(pointi<self.downsampled_atlas.shape):
                category[i] = self.downsampled_atlas[pointi[0],pointi[1],pointi[2]]
        segment_to_id = self.get_segment_to_id_where_segment_are_brain_regions()
        id_to_structure = self.get_id_to_structure(segment_to_id)
        ids,structures = list(id_to_structure.keys()),list(id_to_structure.values())
        cell_count_per_structure={}
        for i,id in enumerate(ids):
            cell_count_per_structure[structures[i]] =  sum(category==id)
        return ids, cell_count_per_structure
        
    def plot_cell_distribution(self,data):
        ids, cell_count_per_structure = self.get_cell_count_per_structure(data)
        structures,counts = list(cell_count_per_structure.keys()),list(cell_count_per_structure.values())
        plt.figure(figsize = [15,8])
        plt.title('Sure Detection Distribution for DK41')
        plt.bar(ids,counts, width = 0.4);
        plt.xticks(ids, structures, rotation=45);
