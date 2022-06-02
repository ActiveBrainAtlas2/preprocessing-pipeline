import sys
import numpy as np
sys.path.append('/data/programming/pipeline')
from abakit.lib.utilities_neuroglancer_image import create_neuroglancer_lite
from notebooks.Will.toolbox.IOs.get_calculated_transforms import get_affine_transform
from notebooks.Will.toolbox.IOs.LoadComDatabase import LoadComDatabase
from notebooks.Will.toolbox.IOs.TransformCom import TransformCom
from abakit.lib.Controllers.SqlController import SqlController
from notebooks.Will.toolbox.IOs.get_stack_image_sitk import load_stack_from_prepi
import SimpleITK as sitk
import neuroglancer
print(neuroglancer.PointAnnotation)
def get_annotations(com_dict):
    n_annotations = len(com_dict)
    names = list(com_dict.keys())
    coordinates = list(com_dict.values())
    annotations = []
    for annotationi in range(n_annotations):
        point = np.array(coordinates[annotationi])/np.array([10.4,10.4,20])
        point_annotation = neuroglancer.PointAnnotation(id=names[annotationi],point=point,description=names[annotationi])
        annotations.append(point_annotation)
    return annotations

getcom = LoadComDatabase()
gettc = TransformCom(getcom)
mov_brain = 'DK52'
fix_brain = 'DK41'
controller = SqlController(fix_brain)
moving_image = load_stack_from_prepi(mov_brain)
fixed_image = load_stack_from_prepi(fix_brain)
affine_transform = get_affine_transform(fix_brain)
affine_transformed_image = sitk.Resample(
    moving_image, fixed_image, affine_transform,
    sitk.sitkLinear, 0.0, moving_image.GetPixelID())
fixed_arr = sitk.GetArrayViewFromImage(fixed_image)
moving_arr = sitk.GetArrayViewFromImage(moving_image)
affine_transformed_arr = sitk.GetArrayViewFromImage(affine_transformed_image)
fixed_arr = np.swapaxes(fixed_arr, 0, 2).astype('uint16')
moving_arr = np.swapaxes(moving_arr, 0, 2).astype('uint16')
affine_transformed_arr = np.swapaxes(affine_transformed_arr, 0, 2).astype('uint16')

dimensions=neuroglancer.CoordinateSpace(names=['x', 'y', 'z'], units='um', scales=[10.4,10.4, 20])
fixed_layer = neuroglancer.LocalVolume(volume_type='image',
            data=fixed_arr, 
            dimensions=dimensions, 
            voxel_offset=(0, 0, 0))
moving_layer = neuroglancer.LocalVolume(volume_type='image',
            data=moving_arr, 
            dimensions=dimensions, 
            voxel_offset=(0, 0, 0))
transformed_layer = neuroglancer.LocalVolume(volume_type='image',
            data=affine_transformed_arr, 
            dimensions=dimensions, 
            voxel_offset=(0, 0, 0))

prep_list = getcom.get_prep_list_for_rough_alignment_test()
prepi = 'DK39'
prepi_com = getcom.get_prepi_com(prepi)
DK52_coms = getcom.get_dk52_com()
prepid = prep_list.index(prepi)
itk_transformed_coms = gettc.get_itk_affine_transformed_coms()
prepi_itk_transformed = itk_transformed_coms[prepid]

viewer1=neuroglancer.Viewer()
with viewer1.txn() as s:
    s.layers.clear()
    s.layers.append(name = 'New Brain', layer = fixed_layer)
    s.layers.append(name = 'Reference Brain', layer = moving_layer)
    annotations = get_annotations(DK52_coms)
    s.layers.append(name="Reference COM",
                layer=neuroglancer.LocalAnnotationLayer(dimensions=dimensions,
                annotations=annotations,
                annotationColor = "#FB9F89"))
print(viewer1)

viewer2=neuroglancer.Viewer()
with viewer2.txn() as s:
    s.layers.clear()
    s.layers.append(name = 'New Brain', layer = fixed_layer)
    s.layers.append(name = 'Reference Brain Rough Aligned', layer = transformed_layer)
    annotations = get_annotations(prepi_itk_transformed)
    s.layers.append(name="Reference Brain COM Rough Aligned",
                layer=neuroglancer.LocalAnnotationLayer(dimensions=dimensions,
                annotations=annotations,
                annotationColor = "#FB9F89"))
    annotations = get_annotations(prepi_com)
print(viewer2)

# DK39_detected = controller.get_com_dict('DK39',input_type_id=3,person_id=23,active=True)
# viewer3=neuroglancer.Viewer()
# with viewer3.txn() as s:
#     s.layers.clear()
#     s.layers.append(name = 'New Brain', layer = fixed_layer)
#     s.layers.append(name = 'Reference Brain Rough Aligned', layer = transformed_layer)
#     annotations = get_annotations(prepi_itk_transformed)
#     s.layers.append(name="Reference Brain COM transformed",
#                 layer=neuroglancer.LocalAnnotationLayer(dimensions=dimensions,
#                 annotations=annotations,
#                 annotationColor = "#FB9F89"))
#     annotations = get_annotations(DK39_detected)
#     s.layers.append(name="com_fixed",
#                 layer=neuroglancer.LocalAnnotationLayer(dimensions=dimensions,
#                 annotations=annotations,
#                 annotationColor = "#89EBFB"))
# print(viewer3)

print('print')