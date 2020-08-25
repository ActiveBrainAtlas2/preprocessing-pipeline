import os, sys
import numpy as np

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
atlas_name = 'atlasV8'
surface_level = 0.9
ATLAS_PATH = os.path.join('/net/birdstore/Active_Atlas_Data/data_root/atlas_data', atlas_name)
OUTPUT = os.path.join(ATLAS_PATH, 'mesh')

from utilities.imported_atlas_utilities import volume_to_polydata, save_mesh_stl

structures = ['10N_L', '10N_R', '12N', '3N_L', '3N_R', '5N_L', '5N_R', '6N_L', '6N_R', '7N_L', '7N_R', 'Amb_L', 'Amb_R',
              'AP', 'DC_L', 'DC_R', 'IC', 'LC_L', 'LC_R', 'LRt_L', 'LRt_R', 'PBG_L', 'PBG_R', 'Pn_L', 'Pn_R', 'RMC_L',
              'RMC_R', 'RtTg', 'SC', 'SNC_L', 'SNC_R', 'SNR_L', 'SNR_R', 'Sp5C_L', 'Sp5C_R', 'Sp5I_L', 'Sp5I_R',
              'Sp5O_L', 'Sp5O_R', 'Tz_L', 'Tz_R', 'VCA_L', 'VCA_R', 'VCP_L', 'VCP_R', 'VLL_L', 'VLL_R']


for structure in structures:
    structure_filepath = os.path.join(ATLAS_PATH, 'structure', f'{structure}.npy')
    structure_volume = np.load(structure_filepath)
    origin_filepath = os.path.join(ATLAS_PATH, 'origin', f'{structure}.txt')
    structure_origin = np.loadtxt(origin_filepath)

    volume = (structure_volume >= surface_level, structure_origin)
    aligned_structure = volume_to_polydata(volume=volume,
                           num_simplify_iter=3, smooth=True,
                           return_vertex_face_list=False)
    filepath = os.path.join(OUTPUT, '{}.stl'.format(structure))
    save_mesh_stl(aligned_structure, filepath)
