import os 
import sys
import numpy as np
import pandas as pd
from skimage import io
from collections import OrderedDict
from concurrent.futures.process import ProcessPoolExecutor
from sqlalchemy import false
from sqlalchemy.orm.exc import NoResultFound
import tifffile as tiff

from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from lib.file_location import FileLocationManager
from lib.sqlcontroller import SqlController
from lib.utilities_alignment import (create_downsampled_transforms, process_image)
from lib.utilities_process import test_dir, get_cpus
from model.elastix_transformation import ElastixTransformation
from lib.sql_setup import session


def create_elastix_transformation(rotation, xshift, yshift, center):
    R = np.array([[np.cos(rotation), -np.sin(rotation)],
                    [np.sin(rotation), np.cos(rotation)]])
    shift = center + (xshift, yshift) - np.dot(R, center)
    T = np.vstack([np.column_stack([R, shift]), [0, 0, 1]])
    return T


def load_elastix_transformation(animal, moving_index):
    try:
        elastixTransformation = session.query(ElastixTransformation).filter(ElastixTransformation.prep_id == animal)\
            .filter(ElastixTransformation.section == moving_index).one()
    except NoResultFound as nrf:
        print('No value for {} {} error: {}'.format(animal, moving_index, nrf))
        return 0,0,0

    R = elastixTransformation.rotation
    xshift = elastixTransformation.xshift
    yshift = elastixTransformation.yshift
    return R, xshift, yshift

def parse_elastix(animal):
    """
    After the elastix job is done, this goes into each subdirectory and parses the Transformation.0.txt file
    Args:
        animal: the animal
    Returns: a dictionary of key=filename, value = coordinates
    """
    fileLocationManager = FileLocationManager(animal)
    DIR = fileLocationManager.prep
    INPUT = os.path.join(DIR, 'CH1', 'thumbnail_cleaned')

    files = sorted(os.listdir(INPUT))
    midpoint = len(files) // 2
    transformation_to_previous_sec = {}
    midfilepath = os.path.join(INPUT, files[midpoint])
    midfile = io.imread(midfilepath, img_num=0)
    height = midfile.shape[0]
    width = midfile.shape[1]
    center = np.array([width, height]) / 2
    
    for i in range(1, len(files)):
        moving_index = os.path.splitext(files[i])[0]
        rotation, xshift, yshift = load_elastix_transformation(animal, moving_index)
        T = create_elastix_transformation(rotation, xshift, yshift, center)
        transformation_to_previous_sec[i] = T
    
    
    transformations = {}
    # Converts every transformation
    for moving_index in range(len(files)):
        if moving_index == midpoint:
            transformations[files[moving_index]] = np.eye(3)
        elif moving_index < midpoint:
            T_composed = np.eye(3)
            for i in range(midpoint, moving_index, -1):
                T_composed = np.dot(np.linalg.inv(transformation_to_previous_sec[i]), T_composed)
            transformations[files[moving_index]] = T_composed
        else:
            T_composed = np.eye(3)
            for i in range(midpoint + 1, moving_index + 1):
                T_composed = np.dot(transformation_to_previous_sec[i], T_composed)
            transformations[files[moving_index]] = T_composed

    return transformations




def run_offsets(animal, transforms, channel, downsample, masks, create_csv, allen):
    """
    This gets the dictionary from the above method, and uses the coordinates
    to feed into the Imagemagick convert program. This method also uses a Pool to spawn multiple processes.
    Args:
        animal: the animal
        transforms: the dictionary of file, coordinates
        limit: number of jobs
    Returns: nothing
    """
    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    channel_dir = 'CH{}'.format(channel)
    INPUT = os.path.join(fileLocationManager.prep,  channel_dir, 'thumbnail_cleaned')
    OUTPUT = os.path.join(fileLocationManager.prep, channel_dir, 'thumbnail_aligned')

    if not downsample:
        INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'full_cleaned')
        OUTPUT = os.path.join(fileLocationManager.prep, channel_dir, 'full_aligned')

    error = test_dir(animal, INPUT, downsample=downsample, same_size=True)
    if len(error) > 0 and not create_csv:
        print(error)
        sys.exit()

    if masks:
        INPUT = os.path.join(fileLocationManager.prep, 'rotated_masked')
        error = test_dir(animal, INPUT, downsample=False, same_size=True)
        if len(error) > 0:
            print(error)
            sys.exit()
        OUTPUT = os.path.join(fileLocationManager.prep, 'rotated_aligned_masked')

    progress_id = sqlController.get_progress_id(downsample, channel, 'ALIGN')
    sqlController.set_task(animal, progress_id)

    os.makedirs(OUTPUT, exist_ok=True)
    downsampled_transforms = create_downsampled_transforms(animal, transforms, downsample)
    downsampled_transforms = OrderedDict(sorted(downsampled_transforms.items()))
    file_keys = []
    for i, (file, T) in enumerate(downsampled_transforms.items()):
        if allen:
            r90 = np.array([[0,-1,0],[1,0,0],[0,0,1]])
            ROT_DIR = os.path.join(fileLocationManager.root, animal, 'rotations')
            rotfile = file.replace('tif', 'txt')
            rotfile = os.path.join(ROT_DIR, rotfile)
            R_cshl = np.loadtxt(rotfile)
            R_cshl[0,2] = R_cshl[0,2] / 32
            R_cshl[1,2] = R_cshl[1,2] / 32
            R_cshl = R_cshl @ r90
            R_cshl = np.linalg.inv(R_cshl)
            R = T @ R_cshl
        infile = os.path.join(INPUT, file)
        outfile = os.path.join(OUTPUT, file)
        if os.path.exists(outfile) and not create_csv:
            continue

        file_keys.append([i,infile, outfile, T])
    
    if create_csv:
        create_csv_data(animal, file_keys)
    else:
        workers, _ = get_cpus()
        with ProcessPoolExecutor(max_workers=workers) as executor:
            executor.map(process_image, sorted(file_keys))

def align_full_size_image(animal, transforms, channel):
    transforms = create_downsampled_transforms(animal, transforms, downsample = False)
    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    channel_dir = 'CH{}'.format(channel)
    INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'full_cleaned')
    OUTPUT = os.path.join(fileLocationManager.prep, channel_dir, 'full_aligned')
    align_images(INPUT,OUTPUT,transforms)
    progress_id = sqlController.get_progress_id(downsample = False, channel = channel, action = 'ALIGN')
    sqlController.set_task(animal, progress_id)

def align_downsampled_images(animal, transforms, channel):
    transforms = create_downsampled_transforms(animal, transforms, downsample = True)
    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    channel_dir = 'CH{}'.format(channel)
    INPUT = os.path.join(fileLocationManager.prep,  channel_dir, 'thumbnail_cleaned')
    OUTPUT = os.path.join(fileLocationManager.prep, channel_dir, 'thumbnail_aligned')
    align_images(INPUT,OUTPUT,transforms)
    progress_id = sqlController.get_progress_id(downsample = True, channel = channel, action = 'ALIGN')
    sqlController.set_task(animal, progress_id)

def align_allen_image():
    ...

def align_section_masks(animal, transforms):
    fileLocationManager = FileLocationManager(animal)
    INPUT = fileLocationManager.rotated_and_padded_thumbnail_mask
    OUTPUT = fileLocationManager.aligned_rotated_and_padded_thumbnail_mask
    align_images(INPUT,OUTPUT,transforms)

def align_images(INPUT,OUTPUT,transforms):
    os.makedirs(OUTPUT, exist_ok=True)
    transforms = OrderedDict(sorted(transforms.items()))
    file_keys = []
    for i, (file, T) in enumerate(transforms.items()):
        infile = os.path.join(INPUT, file)
        outfile = os.path.join(OUTPUT, file)
        if os.path.exists(outfile):
            continue
        file_keys.append([i,infile, outfile, T])
    workers, _ = get_cpus()
    with ProcessPoolExecutor(max_workers=workers) as executor:
        executor.map(process_image, sorted(file_keys))

def create_csv_data(animal, file_keys):
    data = []
    for index, infile, outfile, T in file_keys:
        T = np.linalg.inv(T)
        file = os.path.basename(infile)

        data.append({
            'i': index,
            'infile': file,
            'sx': T[0, 0],
            'sy': T[1, 1],
            'rx': T[1, 0],
            'ry': T[0, 1],
            'tx': T[0, 2],
            'ty': T[1, 2],
        })
    df = pd.DataFrame(data)
    df.to_csv(f'/tmp/{animal}.section2sectionalignments.csv', index=False)