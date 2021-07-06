#%%
# from notebooks.Will.toolbox.brain_lists import get_prep_list_for_rough_alignment_test
# from notebooks.Will.toolbox import com_dict_tools
import sys
import numpy as np
sys.path.append('/home/zhw272/programming/pipeline_utility')
from notebooks.Will.toolbox.IOs.get_calculated_transforms import get_affine_transform,get_demons_transform
from notebooks.Will.toolbox.rough_alignment.apply_affine_transform import transform_point_affine
from notebooks.Will.toolbox.rough_alignment.apply_demons_transform import transform_point_demons
from notebooks.Will.experimental.get_coms_from_pickle import *
from notebooks.Will.toolbox.IOs.get_stack_image_sitk import load_stack_from_prepi
import SimpleITK as sitk
import neuroglancer
import matplotlib.pyplot as plt
# from utilities.utilities_cvat_neuroglancer import NumpyToNeuroglancer
# from notebooks.Will.IO.old
def add_stack(vol,viewer,name):
    volume_layer = neuroglancer.LocalVolume(
            data=vol, 
            dimensions=neuroglancer.CoordinateSpace(names=['x', 'y', 'z'], units='um', scales=[10.4,10.4, 20]), 
            voxel_offset=(0, 0, 0))
    with viewer.txn() as s:
        s.layers.append(name = name, layer = volume_layer)

def get_arrays():
    mov_brain = 'DK52'
    fix_brain = 'DK39'
    moving_image = load_stack_from_prepi(mov_brain)
    fixed_image = load_stack_from_prepi(fix_brain)
    affine_transform = get_affine_transform(fix_brain)
    affine_transformed_image = sitk.Resample(
        moving_image, fixed_image, affine_transform,
        sitk.sitkLinear, 0.0, moving_image.GetPixelID())
    fixed_arr = sitk.GetArrayViewFromImage(fixed_image)
    moving_arr = sitk.GetArrayViewFromImage(moving_image)
    affine_transformed_arr = sitk.GetArrayViewFromImage(affine_transformed_image)
    # fixed_arr = np.swapaxes(fixed_arr, 0, 2)
    # moving_arr = np.swapaxes(moving_arr, 0, 2)
    # affine_transformed_arr = np.swapaxes(affine_transformed_arr, 0, 2)
    return fixed_arr,moving_arr,affine_transformed_arr

#%%
mov_brain = 'DK52'
fix_brain = 'DK39'
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
# #%%
#%%
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
#%% compare untransformed moving to fixed
viewer=neuroglancer.Viewer()
with viewer.txn() as s:
    s.layers.clear()
    s.layers.append(name = 'fixed', layer = fixed_layer)
    s.layers.append(name = 'moving', layer = moving_layer)
    print(s.dimensions)
    s.layers.append(name="com",
                layer=neuroglancer.LocalAnnotationLayer(dimensions=dimensions,
                annotations=[
                    neuroglancer.PointAnnotation(
                        id='d6704f30d2f08f1795d73bf387da7d5eec9d813f',
                        point=[100, 100, 200]),
                    neuroglancer.PointAnnotation(
                        id='234',
                        point=[100, 100, 300])
                ]))

print(viewer)
#%% compare transformed moving to fixed
viewer=neuroglancer.Viewer()
with viewer.txn() as s:
    s.layers.clear()
    s.layers.append(name = 'fixed', layer = fixed_layer)
    s.layers.append(name = 'transformed', layer = transformed_layer)
    print(s.dimensions)
    s.layers.append(name="com",
                layer=neuroglancer.LocalAnnotationLayer(dimensions=dimensions,
                annotations=[
                    neuroglancer.PointAnnotation(
                        id='d6704f30d2f08f1795d73bf387da7d5eec9d813f',
                        point=[100, 100, 200]),
                    neuroglancer.PointAnnotation(
                        id='234',
                        point=[100, 100, 300])
                ]))

print(viewer)

#%%
add_stack(fixed_arr,viewer,'prepi')
#%%
print(viewer)

# %%
plt.imshow(fixed_arr[:,:,200])

# %%
# neuroglancer = NumpyToNeuroglancer(animal='DK52',volume = moving_arr,scales=[325,325,20000],layer_type='image',data_type=moving_arr.dtype)
# %%
prepid = 'DK39'
prep_list = get_prep_list_for_rough_alignment_test()
prepi = prep_list.index(prepid)
#['DK39', 'DK41', 'DK43', 'DK54', 'DK55']

def physical_to_thumbnail(com):
    return np.array(com)/np.array([10.4,10.4,20])
atlas_com_dict = get_atlas_com()
dk52_com = get_dk52_com()
dk52_com_thumbnail = convert_com_dict_units(dk52_com,physical_to_thumbnail)
prep_coms = get_prep_coms()
prepi_com = convert_com_dict_units(prep_coms[prepi],physical_to_thumbnail)
affine_transformed_coms_itk,affine_aligned_coms_itk = get_itk_affine_transformed_coms()
affine_transformed_com_itk_prepi = convert_com_dict_units(
    affine_transformed_coms_itk[prepi],physical_to_thumbnail)
transformed_coms_airlab,aligned_coms_airlab = get_airlab_transformed_coms()
#%% compare transformed moving to fixed
def get_annotations(com_dict):
    n_annotations = len(com_dict)
    names = list(com_dict.keys())
    coordinates = list(com_dict.values())
    annotations = []
    for annotationi in range(n_annotations):
        point_annotation = neuroglancer.PointAnnotation(id=names[annotationi],point=coordinates[annotationi])
        annotations.append(point_annotation)
    return annotations

def get_annotation_properties(com_dict,color='yellow'):
    n_annotations = len(com_dict)
    annotation_properties = []
    for annotationi in range(n_annotations):
        annotation_propperty = neuroglancer.AnnotationPropertySpec(id='color',type='rgb')
        annotation_properties.append(annotation_propperty)
    return annotation_properties
#%%
viewer1=neuroglancer.Viewer()
#%%
with viewer1.txn() as s:
    s.layers.clear()
    s.layers.append(name = 'fixed', layer = fixed_layer)
    s.layers.append(name = 'transformed', layer = transformed_layer)
    annotations = get_annotations(affine_transformed_com_itk_prepi)
    s.layers.append(name="com_transformed",
                layer=neuroglancer.LocalAnnotationLayer(dimensions=dimensions,
                annotations=annotations,
                annotationColor = "#FB9F89"))
    annotations = get_annotations(prepi_com)
    s.layers.append(name="com_fixed",
                layer=neuroglancer.LocalAnnotationLayer(dimensions=dimensions,
                annotations=annotations,
                annotationColor = "#89EBFB"))

print(viewer1)
#%%
viewer2=neuroglancer.Viewer()
#%%
with viewer2.txn() as s:
    s.layers.clear()
    s.layers.append(name = 'fixed', layer = fixed_layer)
    s.layers.append(name = 'moving', layer = moving_layer)
    annotations = get_annotations(dk52_com_thumbnail)
    s.layers.append(name="com_moving",
                layer=neuroglancer.LocalAnnotationLayer(dimensions=dimensions,
                annotations=annotations,
                annotationColor = "#FB9F89"))
    annotations = get_annotations(prepi_com)
    s.layers.append(name="com_fixed",
                layer=neuroglancer.LocalAnnotationLayer(dimensions=dimensions,
                annotations=annotations,
                annotationColor = "#89EBFB"))

print(viewer2)
#%%
viewer3=neuroglancer.Viewer()
#%%
with viewer3.txn() as s:
    s.layers.clear()
    s.layers.append(name = 'transformed', layer = transformed_layer)
    s.layers.append(name = 'moving', layer = moving_layer)
    annotations = get_annotations(prepi_com)
    s.layers.append(name="com_moving",
                layer=neuroglancer.LocalAnnotationLayer(dimensions=dimensions,
                annotations=annotations,
                annotationColor = "#FB9F89"))
    annotations = get_annotations(affine_transformed_com_itk_prepi)
    s.layers.append(name="com_transformed",
                layer=neuroglancer.LocalAnnotationLayer(dimensions=dimensions,
                annotations=annotations,
                annotationColor = "#89EBFB"))
    
print(viewer3)

# %%
