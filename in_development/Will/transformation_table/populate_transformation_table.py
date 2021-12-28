from lib.Controllers.SqlController import SqlController
from DKLabInformation import DKLabInformation
from lib.Transformation import Transformation
import SimpleITK as sitk
from abakit.registration.algorithm import umeyama
import numpy as np
from Plotter.Plotter import Plotter
import pickle

controller = SqlController('Atlas')
info = DKLabInformation()
plotter = Plotter()

atlas_com = controller.get_atlas_centers()
for braini in info.Jun_brains:
    source = braini
    destination = 'Atlas'
    brain_com = controller.get_layer_data_entry(braini)

    common_keys = atlas_com.keys() & brain_com.keys()
    if len(common_keys) ==0 :
        continue
    if controller.has_transformation(source = braini, destination = 'Atlas'):
        continue
    dst_point_set = np.array([atlas_com[s] for s in common_keys]).T
    src_point_set = np.array([brain_com[s] for s in common_keys]).T

    affine_transform = sitk.LandmarkBasedTransformInitializer(sitk.AffineTransform(3),
            list(dst_point_set.flatten()),list(src_point_set.flatten()))
    affine_transform = pickle.dumps(Transformation(affine_transform))

    rigid_transform = sitk.LandmarkBasedTransformInitializer(sitk.VersorRigid3DTransform(),
            list(dst_point_set.flatten()),list(src_point_set.flatten()))
    rigid_transform = pickle.dumps(Transformation(rigid_transform))

    R, t = umeyama(src_point_set, dst_point_set)
    parameters = np.concatenate((R.flatten(),t.flatten()))
    similarity_transform = sitk.AffineTransform(3)
    similarity_transform.SetParameters(parameters)
    similarity_transform = pickle.dumps(Transformation(similarity_transform))
    
    controller.add_transformation_row(source = braini,destination = 'Atlas',transformation_type = 1,transformation = rigid_transform)
    controller.add_transformation_row(source = braini,destination = 'Atlas',transformation_type = 2,transformation = affine_transform)
    controller.add_transformation_row(source = braini,destination = 'Atlas',transformation_type = 4,transformation = similarity_transform)

breakpoint()