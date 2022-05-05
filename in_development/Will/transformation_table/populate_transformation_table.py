from abakit.lib.Controllers.SqlController import SqlController
from abakit.lib.Transformation import Transformation
import SimpleITK as sitk
from abakit.registration.algorithm import umeyama
import numpy as np
from abakit.Plotter.Plotter import Plotter
import pickle

controller = SqlController('Atlas')
Jun_brains = ['DK39','DK41','DK43','DK46','DK52','DK54','DK55','DK61',\
            'DK60','DK50','DK40']
plotter = Plotter()
atlas_com = controller.get_atlas_centers()

def itk_to_custom_transform(transform,constructor):
    fixed_and_regular_parameters = (transform.GetFixedParameters(),transform.GetParameters())
    transform = Transformation(fixed_and_regular_parameters,constructor)
    return pickle.dumps(transform)

for braini in Jun_brains:
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
    def initialize_3d_affine():
        return sitk.AffineTransform(3)
    affine_transform = itk_to_custom_transform(affine_transform,initialize_3d_affine)

    rigid_transform = sitk.LandmarkBasedTransformInitializer(sitk.VersorRigid3DTransform(),
            list(dst_point_set.flatten()),list(src_point_set.flatten()))
    rigid_transform = itk_to_custom_transform(rigid_transform,sitk.VersorRigid3DTransform)


    R, t = umeyama(src_point_set, dst_point_set)
    parameters = np.concatenate((R.flatten(),t.flatten()))
    similarity_transform = initialize_3d_affine()
    similarity_transform.SetParameters(parameters)
    similarity_transform = itk_to_custom_transform(similarity_transform,initialize_3d_affine)
    
    controller.add_transformation_row(source = braini,destination = 'Atlas',transformation_type = 1,transformation = rigid_transform)
    controller.add_transformation_row(source = braini,destination = 'Atlas',transformation_type = 2,transformation = affine_transform)
    controller.add_transformation_row(source = braini,destination = 'Atlas',transformation_type = 4,transformation = similarity_transform)

print('done')