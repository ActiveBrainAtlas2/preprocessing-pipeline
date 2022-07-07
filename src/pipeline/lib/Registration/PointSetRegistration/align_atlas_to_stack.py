from Registration.PointSetRegistration.PointSetAlignment import AffinePointSetAlignment,\
    get_shared_key_and_array
from abakit.atlas.Plotter import Plotter
from abakit.lib.Controllers.SqlController import SqlController
import pickle
from abakit.registration.utilities import get_similarity_transformation_from_dicts,apply_similarity_transformation_to_com_dict,umeyama
import numpy as np

def get_transformed_atlas_points(prepi):
    controller = SqlController(prepi)
    com = controller.get_com_dict(prepi)
    atlas = controller.get_atlas_centers()
    fixed,moving,shared_keys = get_shared_key_and_array(atlas,com)
    affine = AffinePointSetAlignment(fixed, moving)
    affine.calculate_transform()
    transformed_atlas_point = affine.inverse_transform_dictionary(atlas)
    return transformed_atlas_point

def create_visual():
    plotter = Plotter()
    plotter.compare_point_dictionaries([atlas,com,transformed_atlas_point],names=['atlas','DK52','transformed_atlas'])