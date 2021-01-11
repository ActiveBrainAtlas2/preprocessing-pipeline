import os, sys
from vedo import load, show
from tqdm import tqdm

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
atlas_name = 'atlasV8'
from utilities.file_location import DATA_PATH
MESH_PATH = os.path.join(DATA_PATH, 'atlas_data', atlas_name, 'mesh', '0.9')
from utilities.sqlcontroller import SqlController
sqlController = SqlController('MD589')
structures = sqlController.get_structures_list()

acts = []
for structure in tqdm(structures):
    filepath = os.path.join(MESH_PATH, f'{structure}.stl')
    if os.path.exists(filepath):
        act = load(filepath)
        color = sqlController.get_structure_color_rgb(structure)
        act.color(color)
        acts.append(act)

show(acts)

