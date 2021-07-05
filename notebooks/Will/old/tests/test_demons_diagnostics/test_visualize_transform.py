#%%
import sys
import numpy as np
sys.path.append('/home/zhw272/programming/pipeline_utility')
from notebooks.Will.toolbox.IOs.get_calculated_transforms import get_affine_transform,get_demons_transform
from notebooks.Will.toolbox.rough_alignment.apply_affine_transform import transform_point_affine
from notebooks.Will.toolbox.rough_alignment.apply_demons_transform import transform_point_demons
from notebooks.Will.toolbox.IOs.get_stack_image_sitk import load_stack_from_prepi
import SimpleITK as sitk
import neuroglancer
import matplotlib.pyplot as plt

def add_stack(vol,viewer,name):
    volume_layer = neuroglancer.LocalVolume(
            data=vol, 
            dimensions=neuroglancer.CoordinateSpace(names=['x', 'y', 'z'], units='um', scales=[10.4,10.4, 20]), 
            voxel_offset=(0, 0, 0))
    with viewer.txn() as s:
        s.layers.append(name = name, layer = volume_layer)

def get_arrays():
    mov_brain = 'DK52'
    fix_brain = 'DK43'
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
fix_brain = 'DK43'
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
#%%
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
#%%
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
