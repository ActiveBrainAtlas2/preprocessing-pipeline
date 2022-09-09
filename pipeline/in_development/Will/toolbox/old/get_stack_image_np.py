import matplotlib.pyplot as plt
from toolbox.IOs.get_path import get_subpath_to_tif_files,get_subpath_to_affine_transformed_thumbnails
import os
import numpy as np
import glob
from imageio import imread

def get_list_of_tiff(prepi):
    tiff_path = get_subpath_to_tif_files(prepi)
    list_of_tiffs = os.listdir(tiff_path)
    list_of_tiffs = sorted(list_of_tiffs)
    return list_of_tiffs

def get_nsections(prepi):
    list_of_tiffs = get_list_of_tiff(prepi)
    return len(list_of_tiffs)

def load_image(prepi,z=0):
    tiff_path = get_subpath_to_tif_files(prepi)
    list_of_tiffs = get_list_of_tiff(prepi)
    return plt.imread(tiff_path/list_of_tiffs[z])

def get_ndarray_from_tiff_path(tiff_path,dt=np.uint16,max_number_of_file_to_read=-1,down_sample_ratio=[1,1,1],file_list=None):
    if file_list is None:
        file_list = sorted(glob.glob(tiff_path+'/*.tif'))
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

def get_prepi_thumbnail_ndarray(prepi):
    tiff_path = str(get_subpath_to_tif_files(prepi))
    ndarray = get_ndarray_from_tiff_path(tiff_path)
    ndarray = np.swapaxes(ndarray, 0, 2)
    return ndarray

def get_prepi_transformed_thumbnail_ndarray(prepi):
    tiff_path = str(get_subpath_to_affine_transformed_thumbnails(prepi))
    ndarray = get_ndarray_from_tiff_path(tiff_path)
    ndarray = np.swapaxes(ndarray, 0, 2)
    return ndarray

