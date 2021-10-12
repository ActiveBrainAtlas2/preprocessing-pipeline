import os
import json
from lib.file_location import DATA_PATH
from lib.utilities_atlas import ATLAS
from lib.sqlcontroller import SqlController
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
from lib.utilities_atlas_lite import volume_to_polygon, save_mesh
from lib.file_location import FileLocationManager
class Brain:
    def __init__(self,animal):
        self.animal = animal
        self.sqlController = SqlController(self.animal)
        self.origins = {}
        self.COM = {}
        self.volumes = {}
        self.aligned_contours = {}
        self.set_path_and_create_folders()
    
    def set_path_and_create_folders(self):
        self.animal_directory = os.path.join(DATA_PATH, 'atlas_data', ATLAS, self.animal)
        self.original_contour_path = os.path.join(self.animal_directory,  'original_structures.json')
        self.padded_contour_path = os.path.join(self.animal_directory,  'unaligned_padded_structures.json')
        self.align_and_padded_contour_path = os.path.join(self.animal_directory,  'aligned_padded_structures.json')
        self.volume_path = os.path.join(self.animal_directory, 'structure')
        self.origin_path = os.path.join(self.animal_directory, 'origin')
        os.makedirs(self.animal_directory, exist_ok=True)
        os.makedirs(self.volume_path, exist_ok=True)
        os.makedirs(self.origin_path, exist_ok=True)

    def load_com(self):
        self.COM = self.sqlController.get_centers_dict(self.animal)

    def load_origins(self):
        assert(os.path.exists(self.origin_path))
        origin_files = sorted(os.listdir(self.origin_path))
        for filei in origin_files:
            structure = os.path.splitext(filei)[0]    
            self.origins[structure] = np.loadtxt(os.path.join(self.origin_path, filei))
    
    def load_volumes(self):
        assert(os.path.exists(self.volume_path))
        volume_files = sorted(os.listdir(self.volume_path))
        for filei in volume_files:
            structure = os.path.splitext(filei)[0]    
            self.volumes[structure] = np.load(os.path.join(self.volume_path, filei))
    
    def load_aligned_contours(self):
        with open(self.align_and_padded_contour_path) as f:
            self.aligned_contours = json.load(f)
        self.structures = list(self.aligned_contours.keys())        
    
    def save_contours(self):
        assert(hasattr(self,'original_structures'))
        assert(hasattr(self,'centered_structures'))
        assert(hasattr(self,'aligned_structures'))
        with open(self.original_contour_path, 'w') as f:
            json.dump(self.original_structures, f, sort_keys=True)
        with open(self.padded_contour_path, 'w') as f:
            json.dump(self.centered_structures, f, sort_keys=True)
        with open(self.align_and_padded_contour_path, 'w') as f:
            json.dump(self.aligned_structures, f, sort_keys=True)

    def save_volumes(self):
        assert(hasattr(self,'volumes'))
        if not hasattr(self,'structures'):
            self.structures = list(self.volumes.keys())
        for structurei in self.structures:
            volume = self.volumes[structurei]
            volume = np.swapaxes(volume, 0, 2)
            volume = np.rot90(volume, axes=(0,1))
            volume = np.flip(volume, axis=0)
            volume_filepath = os.path.join(self.volume_path, f'{structurei}.npy')
            np.save(volume_filepath, volume)
    
    def save_mesh_files(self):
        assert(hasattr(self,'volumes'))
        assert(hasattr(self,'origins'))
        if not hasattr(self,'structures'):
            self.structures = list(self.volumes.keys())
        for structurei in self.structures:
            origin,volume = self.origins[structurei],self.volumes[structurei]
            centered_origin = origin - self.fixed_brain_center
            threshold_volume = volume >= self.threshold
            aligned_volume = (threshold_volume, centered_origin)
            aligned_structure = volume_to_polygon(volume=aligned_volume,num_simplify_iter=3, smooth=False,return_vertex_face_list=False)
            filepath = os.path.join(self.ATLAS_PATH, 'mesh', f'{structurei}.stl')
            save_mesh(aligned_structure, filepath)

    def save_origins(self):
        assert(hasattr(self,'origins'))
        if not hasattr(self,'structures'):
            self.structures = list(self.origins.keys())
        for structurei in self.structures:
            x, y, z = self.origins[structurei]
            origin_filepath = os.path.join(self.origin_path, f'{structurei}.txt')
            np.savetxt(origin_filepath, (x,y,z))
    
    def save_coms(self):
        assert(hasattr(self,'COM'))
        if not hasattr(self,'structures'):
            self.structures = self.COM.keys()
        for structurei in self.structures:
            comx, comy, comz = self.COM[structurei]
            self.sqlController.add_layer_data(abbreviation=structurei, animal=self.animal, 
                layer='COM', x=comx, y=comy, section=comz, person_id=2, input_type_id=1)

    def plot_contours(self,contours):
        data = []
        for sectioni in contours:
            datai = np.array(contours[sectioni])
            npoints = datai.shape[0]
            datai = np.hstack((datai,np.ones(npoints).reshape(npoints,1)*sectioni))
            data.append(datai)
        data = np.vstack(data)
        fig = go.Figure(data=[go.Scatter3d(x=data[:,0], y=data[:,1], z=data[:,2],mode='markers')])
        fig.show()

    def plot_volume(self,structure='10N_L'):
        volume = self.volumes[structure]
        ax = plt.figure().add_subplot(projection='3d')
        ax.voxels(volume,edgecolor='k')
        plt.show()
    
    def compare_point_dictionaries(self,point_dicts):
        fig = make_subplots(rows = 1, cols = 1,specs=[[{'type':'scatter3d'}]])
        for point_dict in point_dicts:
            values = np.array(list(point_dict.values()))
            fig.add_trace(go.Scatter3d(x=values[:,0], y=values[:,1], z=values[:,2],
                                    mode='markers'),row = 1,col = 1)
        fig.show()

    def get_com_array(self):
        assert(hasattr(self,'COM'))
        return np.array(list(self.COM.values()))

class Atlas(Brain):
    def __init__(self,atlas = ATLAS):
        self.atlas = atlas
        self.fixed_brain = FileLocationManager('MD589')
        super().__init__('Atlas')
    
    def set_path_and_create_folders(self):
        self.animal_directory = os.path.join(DATA_PATH, 'atlas_data', self.atlas)
        self.volume_path = os.path.join(self.animal_directory, 'structure')
        self.origin_path = os.path.join(self.animal_directory, 'origin')
        os.makedirs(self.animal_directory, exist_ok=True)
        os.makedirs(self.volume_path, exist_ok=True)
        os.makedirs(self.origin_path, exist_ok=True)
    
    def create_atlas_contours(self):
        ...
    
    def display_atlas_contours(self):
        ...

    def load_atlas(self):
        self.load_origins()
        self.load_volumes()
