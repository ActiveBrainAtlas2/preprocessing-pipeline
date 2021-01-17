import os, sys
import numpy as np
from tqdm import tqdm

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
atlas_name = 'atlasV9'
surface_level = 0.8
from utilities.file_location import DATA_PATH
ATLAS_PATH = os.path.join(DATA_PATH, 'atlas_data', atlas_name)

OUTPUT = os.path.join(ATLAS_PATH, 'mesh')
os.makedirs(OUTPUT, exist_ok=True)

from utilities.atlas.imported_atlas_utilities import volume_to_polydata, save_mesh_stl
from utilities.sqlcontroller import SqlController
sqlController = SqlController('MD589')
structures = sqlController.get_structures_list()
structures.remove('R')


for structure in tqdm(structures):
    volume_filepath = os.path.join(ATLAS_PATH, 'structure', f'{structure}.npy')
    volume = np.load(volume_filepath)
    origin_filepath = os.path.join(ATLAS_PATH, 'origin', f'{structure}.txt')
    origin = np.loadtxt(origin_filepath)

    volume_origin = (volume >= surface_level, origin)
    #volume_origin = (volume, origin)
    aligned_structure = volume_to_polydata(volume=volume_origin,
                           num_simplify_iter=3, smooth=True,
                           return_vertex_face_list=False)
    mesh_filepath = os.path.join(OUTPUT, '{}.stl'.format(structure))
    save_mesh_stl(aligned_structure, mesh_filepath)
