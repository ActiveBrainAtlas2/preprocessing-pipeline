from Registration.PointSetRegistration.PointSetAlignment import AffinePointSetAlignment,\
    get_shared_key_and_array
from atlas.Plotter import Plotter
from lib.sqlcontroller import SqlController
import pickle
plotter = Plotter()

controller = SqlController('DK52')
com52 = controller.get_com_dict('DK52')
atlas = controller.get_atlas_centers()
fixed,moving,shared_keys = get_shared_key_and_array(atlas,com52)
affine = AffinePointSetAlignment(fixed, moving)
affine.calculate_transform()
transformed_atlas_point = affine.inverse_transform_dictionary(atlas)

plotter.compare_point_dictionaries([atlas,com52,transformed_atlas_point],names=['atlas','DK52','transformed_atlas'])

def get_transformed_atlas_points(prepi):
    controller = SqlController('DK52')
    com52 = controller.get_com_dict(prepi)
    atlas = controller.get_atlas_centers()
    fixed,moving,shared_keys = get_shared_key_and_array(atlas,com52)
    affine = AffinePointSetAlignment(fixed, moving)
    affine.calculate_transform()
    transformed_atlas_point = affine.inverse_transform_dictionary(atlas)
    return transformed_atlas_point

transformed = {}
for prepi in ['DK39', 'DK41', 'DK43', 'DK55', 'DK52', 'DK63', 'DK46', 'DK54', 'DK61', 'DK62']:
    transformed_atlas_point = get_transformed_atlas_points(prepi)
    transformed[prepi] = transformed_atlas_point

path = 'change_to_your_save_folder'
pickle.dump(transformed,open(path,'wb'))
