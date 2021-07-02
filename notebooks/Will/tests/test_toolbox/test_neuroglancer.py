#%%
import sys
sys.path.append('/home/zhw272/programming/pipeline_utility')
import neuroglancer
import imageio
from notebooks.Will.toolbox.IOs.get_path import get_subpath_to_tif_files
ip='localhost' # or public IP of the machine for sharable display
port=98092 # change to an unused port number
neuroglancer.set_server_bind_address(bind_address=ip,bind_port=port)
viewer=neuroglancer.Viewer()
import matplotlib.pyplot as plt
# %%
# SNEMI
import numpy as np
from imageio import imread
import glob
import os

def folder2Vol(D0,dt=np.uint16,max_number_of_file_to_read=-1,down_sample_ratio=[1,1,1],file_list=None):
    if file_list is None:
        file_list = sorted(glob.glob(D0+'/*.tif'))
    number_of_files = len(file_list)
    if max_number_of_file_to_read>0:
        number_of_files = min(number_of_files,max_number_of_file_to_read)
    number_of_files = number_of_files//down_sample_ratio[0]
    image_resolution = np.array(imread(file_list[0]).shape)[:2]//down_sample_ratio[1:]

    image_stack = np.zeros((number_of_files,image_resolution[0],image_resolution[1]), dtype=dt)
    section = 0
    for filei in range(number_of_files):
        print(f'loading section {section}')
        if os.path.exists(file_list[filei*down_sample_ratio[0]]):
            sectioni = imread(file_list[filei*down_sample_ratio[0]])
            if sectioni.ndim==3:
                sectioni = sectioni[:,:,0]
            image_stack[filei] = sectioni[::down_sample_ratio[1],::down_sample_ratio[2]]
            section+=1
    return image_stack
#%%
D0=str(get_subpath_to_tif_files("DK39"))
vol = folder2Vol(D0)

# %%
def neuroglancerLayer(data,oo=[0,0,0],tt='image'):
    dimension = neuroglancer.CoordinateSpace(names=['x', 'y', 'z'],units='um',scales=[10.4,10.4, 20])
    return neuroglancer.LocalVolume(data,volume_type=tt,dimensions=dimension,voxel_offset=oo)


#%%
viewer=neuroglancer.Viewer()
all_volume_layer = neuroglancer.LocalVolume(
        data=vol, 
        dimensions=neuroglancer.CoordinateSpace(names=['x', 'y', 'z'], units='um', scales=[10.4,10.4, 20]), 
        voxel_offset=(0, 0, 0))

with viewer.txn() as s:
    s.layers.clear()
    s.layers.append(name = 'text', layer = all_volume_layer)
print(viewer)

# %%
plt.imshow(vol[:,:,200])
# %%
vol = np.swapaxes(vol, 0, 2)

# %%
