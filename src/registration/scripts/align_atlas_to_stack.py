import argparse
import sys
import urllib
from pathlib import Path
PIPELINE_ROOT = Path('./src').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())

from registration.PointSetRegistration.PointSetAlignment import AffinePointSetAlignment,\
    get_shared_key_and_array


from atlas.Plotter import Plotter
from library.controller.structure_com_controller import StructureCOMController
from library.database_model.annotation_points import COMSources

try:
    from settings import host, password, schema, user
except ImportError:
    print('Missing settings using defaults')
    data_path = "/net/birdstore/Active_Atlas_Data/data_root"
    host = "db.dk.ucsd.edu"
    schema = "active_atlas_production"

password = urllib.parse.quote_plus(password) # escape special characters



def get_transformed_atlas_points(animal):
    controller = StructureCOMController(host, password, schema, user)
    com = controller.get_annotation_dict(animal, 2, COMSources.MANUAL)
    atlas = controller.get_annotation_dict('atlas', 16, COMSources.MANUAL)
    print(len(com))
    print(len(atlas))
    
    fixed, moving, shared_keys = get_shared_key_and_array(atlas, com)
    print(shared_keys)
    affine = AffinePointSetAlignment(fixed, moving)
    affine.calculate_transform()
    transformed_atlas_point = affine.inverse_transform_dictionary(atlas)
    return atlas, com, transformed_atlas_point

def create_visual(atlas, com, transformed_atlas_point):
    
    plotter = Plotter()
    plotter.compare_point_dictionaries([atlas, com, transformed_atlas_point], names=['atlas','DK52','transformed_atlas'])



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    
    args = parser.parse_args()
    animal = args.animal
    atlas, com, transformed_atlas_points = get_transformed_atlas_points(animal)
    create_visual(atlas, com, transformed_atlas_points)
