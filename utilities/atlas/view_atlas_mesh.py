import argparse
import os, sys
from vedo import load, show
from tqdm import tqdm

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
atlas_name = 'atlasV8'
from utilities.file_location import DATA_PATH
from utilities.sqlcontroller import SqlController

def create_atlas(level):

    if level == 'high':
        MESH_PATH = os.path.join(DATA_PATH, 'atlas_data', atlas_name, 'mesh', '0.9')
    else:
        MESH_PATH = os.path.join(DATA_PATH, 'atlas_data', atlas_name, 'mesh', '0.1')

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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--level', help='surface threshold', required=False, default='high')

    args = parser.parse_args()
    level = str(args.level).lower().strip()
    create_atlas(level)
