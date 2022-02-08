"""
Creates a shell from  aligned masks
"""
import argparse
import os
import sys
import numpy as np
import shutil
from skimage import io
from tqdm import tqdm
from atlas.NgSegmentMaker import NgConverter
from lib.utilities_cvat_neuroglancer import mask_to_shell
from lib.sqlcontroller import SqlController
from lib.file_location import FileLocationManager
from lib.utilities_process import test_dir, SCALING_FACTOR,get_max_imagze_size
from lib.utilities_create_alignment import parse_elastix, align_section_masks
from lib.utilities_mask import place_image,rotate_image
import tifffile as tiff
import cv2
from skimage import measure
import pickle as pk
from scipy.signal import savgol_filter
from lib.utilities_process import get_image_size

def align_masks(animal):
    rotate_and_pad_masks(animal)
    transforms = parse_elastix(animal)
    align_section_masks(animal,transforms)

def rotate_and_pad_masks(animal):
    sqlController = SqlController(animal)
    fileLocationManager = FileLocationManager(animal)
    INPUT = fileLocationManager.thumbnail_mask
    rotation = sqlController.scan_run.rotation
    flip = sqlController.scan_run.flip
    OUTPUT = fileLocationManager.rotated_and_padded_thumbnail_mask
    os.makedirs(OUTPUT,exist_ok=True)
    max_width, max_height = get_max_imagze_size(fileLocationManager.get_thumbnail_aligned())
    for file in os.listdir(INPUT):
        if file == '045.tif':
            breakpoint()
        infile = os.path.join(INPUT, file)
        outfile = os.path.join(OUTPUT, file)
        if os.path.exists(outfile):
            continue
        try:
            mask = io.imread(infile)
        except IOError as e:
            errno, strerror = e.args
            print(f'Could not open {infile} {errno} {strerror}')

        if rotation > 0:
            mask = rotate_image(mask, infile, rotation)
        if flip == 'flip':
            mask = np.flip(mask)
        if flip == 'flop':
            mask = np.flip(mask, axis=1)
        mask = place_image(mask, infile, max_width, max_height, 0)
        tiff.imsave(outfile, mask)

def create_shell(animal, DEBUG=False):
    '''
    Gets some info from the database used to create the numpy volume from
    the masks. It then turns that numpy volume into a neuroglancer precomputed
    mesh
    :param animal:
    :param DEBUG:
    '''
    sqlController = SqlController(animal)
    fileLocationManager = FileLocationManager(animal)
    INPUT = fileLocationManager.aligned_rotated_and_padded_thumbnail_mask
    error = test_dir(animal, INPUT, downsample=True, same_size=True)
    if len(error) > 0:
        print(error)
        sys.exit()

    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'shell')
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = sorted(os.listdir(INPUT))
    len_files = len(files)
    midpoint = len_files // 2
    if DEBUG:
        limit = 50
        start = midpoint - limit
        end = midpoint + limit
        files = files[start:end]
    volume = []
    for file in tqdm(files):
        tif = io.imread(os.path.join(INPUT, file))
        tif = (tif>125)*255
        tif = mask_to_shell(tif)
        if tif.shape!=(1854, 1045):
            breakpoint()
        volume.append(tif)
    volume = np.array(volume).astype('uint8')
    volume = np.swapaxes(volume, 0, 2)
    ids = np.unique(volume)
    ids = [(i,i) for i in ids]
    resolution = sqlController.scan_run.resolution
    resolution = int(resolution * 1000 / SCALING_FACTOR)
    ng = NgConverter(volume, [resolution, resolution, 20000], offset=[0,0,0])
    ng.create_neuroglancer_files(OUTPUT_DIR,ids)

def create_shell_threshold(animal):
    sqlController = SqlController(animal)
    fileLocationManager = FileLocationManager(animal)
    input = fileLocationManager.get_thumbnail_aligned()
    files = os.listdir(input)
    files = sorted(files)
    rotation = sqlController.scan_run.rotation
    flip = sqlController.scan_run.flip
    volume = []
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'shell_threshold')
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for filei in tqdm(files):
        img = io.imread(os.path.join(input,filei))
        img =  rotate_image(img, filei, 0)
        img = np.flip(img)
        # img = np.flip(img, axis=1)
        mask = img>np.average(img)*0.5
        _,masks,stats,_=cv2.connectedComponentsWithStats(np.int8(mask))
        seg_sizes = stats[:,-1]
        second_largest = np.argsort(seg_sizes)[-2]
        mask = masks==second_largest
        sub_contours = measure.find_contours(mask, 0)
        sub_contour = sub_contours[0]
        sub_contour.T[[0, 1]] = sub_contour.T[[1, 0]]
        pts = sub_contour.astype(np.int32).reshape((-1, 2))
        if len(pts)>99:
            pts = savgol_filter((pts[:,0],pts[:,1]), 99, 1).T.astype(np.int32)
        sub_shell = np.zeros(mask.shape, dtype='uint8')
        sub_shell = cv2.polylines(sub_shell, [pts], True, 1, 5, lineType=cv2.LINE_AA)
        volume.append(sub_shell)
    volume = np.array(volume).astype('uint8')
    volume = np.swapaxes(volume, 0, 2)
    ids = np.unique(volume)
    ids = [(i,i) for i in ids]
    resolution = sqlController.scan_run.resolution
    resolution = int(resolution * 1000 / SCALING_FACTOR)
    ng = NgConverter(volume, [resolution, resolution, 20000], offset=[0,0,0])
    ng.create_neuroglancer_files(OUTPUT_DIR,ids)

if __name__ == '__main__':
    animal = 'DK55'
    align_masks(animal)
    
    # create_shell_threshold(animal)
    create_shell(animal)
