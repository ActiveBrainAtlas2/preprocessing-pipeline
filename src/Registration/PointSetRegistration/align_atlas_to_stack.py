from Registration.PointSetRegistration.PointSetAlignment import AffinePointSetAlignment,\
    get_shared_key_and_array
from atlas.Plotter import Plotter
from lib.sqlcontroller import SqlController

controller = SqlController('DK52')
com52 = controller.get_com_dict('DK52')
atlas = controller.get_atlas_centers()
plotter = Plotter()

fixed,moving,shared_keys = get_shared_key_and_array(atlas,com52)
affine = AffinePointSetAlignment(fixed, moving)
affine.calculate_transform()
transformed_atlas_point = affine.inverse_transform_dictionary(atlas)

plotter.compare_point_dictionaries([atlas,com52,transformed_atlas_point],names=['atlas','DK52','transformed_atlas'])