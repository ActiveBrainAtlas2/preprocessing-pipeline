"""
This script will take a source brain (where the data comes from) and an image brain 
(the brain whose images you want to display unstriped) and align the data from the point brain
to the image brain. It first aligns the point brain data to the atlas, then that data
to the image brain. It prints out the data by default and also will insert
into the database if given a layer name.
"""

import argparse
from sqlalchemy import func
import numpy as np
import os
import sys
from collections import defaultdict
from pathlib import Path
from tqdm import tqdm
from datetime import datetime
from abakit.registration.algorithm import brain_to_atlas_transform, umeyama
from scipy.ndimage.measurements import center_of_mass
from skimage.filters import gaussian

PIPELINE_ROOT = Path('./src').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())

from model.structure import Structure
from model.layer_data import LayerData
from lib.sql_setup import session
from lib.file_location import DATA_PATH
from lib.utilities_atlas import singular_structures
from lib.sqlcontroller import SqlController
from lib.utilities_atlas import convert_vol_bbox_dict_to_overall_vol, symmetricalize_volume, \
    volume_to_polydata, save_mesh_stl

MANUAL = 1
CORRECTED = 2
DETECTED = 3

"""
    The provided r, t is the affine transformation from brain to atlas such that:
        t_phys = atlas_scale @ t
        atlas_coord_phys = r @ brain_coord_phys + t_phys

    The corresponding reverse transformation is:
        brain_coord_phys = r_inv @ atlas_coord_phys - r_inv @ t_phys
"""

def average_shape(volume_origin_list, force_symmetric=False, sigma=2.0):
    """
    Compute the mean shape based on many co-registered volumes.

    Args:
        force_symmetric (bool): If True, force the resulting volume and mesh to be symmetric wrt z.
        sigma (float): sigma of gaussian kernel used to smooth the probability values.

    Returns:
        average_volume_prob (3D ndarray):
        common_mins ((3,)-ndarray): coordinate of the volume's origin
    """
    volume_list, origin_list = list(map(list, list(zip(*volume_origin_list))))

    bbox_list = [(xm, xm+v.shape[1]-1, ym, ym+v.shape[0]-1, zm, zm+v.shape[2]-1) for v,(xm,ym,zm) in zip(volume_list, origin_list)]
    common_volume_list, common_volume_bbox = convert_vol_bbox_dict_to_overall_vol(
        vol_bbox_tuples=list(zip(volume_list, bbox_list)))
    common_volume_list = list([(v > 0).astype(np.int32) for v in common_volume_list])
    average_volume = np.sum(common_volume_list, axis=0)
    # average_volume_prob = average_volume / float(np.max(average_volume))
    average_volume_prob = average_volume / float(3)

    if force_symmetric:
        average_volume_prob = symmetricalize_volume(average_volume_prob)

    average_volume_prob = gaussian(average_volume_prob, sigma) # Smooth the probability
    # print('1',type(average_volume_prob), average_volume_prob.dtype, average_volume_prob.shape, np.mean(average_volume_prob), np.amax(average_volume_prob))
    common_origin = np.array(common_volume_bbox)[[0,2,4]]

    return average_volume_prob, common_origin



def get_centers(animal):
    rows = session.query(LayerData).filter(
        LayerData.active.is_(True))\
            .filter(LayerData.prep_id == animal)\
            .filter(LayerData.person_id == 1)\
            .filter(LayerData.layer == 'COM')\
            .filter(LayerData.input_type_id == DETECTED)\
            .order_by(LayerData.structure_id)\
            .all()
    data = []
    for row in rows:
        data.append( [row.x, row.y, row.section] )
    return np.array(data)


def add_layer_data_row(abbrev, origin):
    structure = session.query(Structure).filter(Structure.abbreviation == func.binary(abbrev)).one()
    
    to_um = 32 * 0.452
    scales = np.array([to_um, to_um, 20])
    x,y,z = origin * scales


    com = LayerData(
        prep_id='Atlas', structure=structure, x=x, y=y, section=z
        , layer='COM',
        created=datetime.utcnow(), active=True, person_id=1, input_type_id=MANUAL
    )
    try:
        session.add(com)
        session.commit()
    except Exception as e:
        print(f'No merge {e}')
        session.rollback()



def merge_brains():
    ATLAS_PATH = os.path.join(DATA_PATH, 'atlas_data', 'atlasV8')
    fixed_brain = 'MD594'
    sqlController = SqlController(fixed_brain)
    width = sqlController.scan_run.width // 32
    height = sqlController.scan_run.height // 32
    adjustment = np.array([width//2, height//2, 440//2])
    moving_brains = ['MD589', 'MD585']
    fixed_data = get_centers(fixed_brain)
    to_um = 32 * 0.452
    scales = np.array([to_um, to_um, 20])
    volume_origin = defaultdict(list)
    
    # get the data for the fixed brain
    ORIGIN_PATH = os.path.join(ATLAS_PATH, fixed_brain, 'origin')
    origin_files = sorted(os.listdir(ORIGIN_PATH))
    VOLUME_PATH = os.path.join(ATLAS_PATH, fixed_brain, 'structure')
    volume_files = sorted(os.listdir(VOLUME_PATH))
    for volume_filename, origin_filename in zip(volume_files, origin_files):
        structure = os.path.splitext(origin_filename)[0]    
        origin = np.loadtxt(os.path.join(ORIGIN_PATH, origin_filename))
        volume = np.load(os.path.join(VOLUME_PATH, volume_filename))
        volume_origin[structure].append((volume, origin))
    
    for brain in moving_brains:
        moving_data = get_centers(brain)
        r, t = umeyama(moving_data.T, fixed_data.T)
        ORIGIN_PATH = os.path.join(ATLAS_PATH, brain, 'origin')
        origin_files = sorted(os.listdir(ORIGIN_PATH))
        VOLUME_PATH = os.path.join(ATLAS_PATH, brain, 'structure')
        volume_files = sorted(os.listdir(VOLUME_PATH))
        for volume_filename, origin_filename in zip(volume_files, origin_files):
            structure = os.path.splitext(origin_filename)[0]    
            origin = np.loadtxt(os.path.join(ORIGIN_PATH, origin_filename))
            volume = np.load(os.path.join(VOLUME_PATH, volume_filename))
            origin_um = origin * scales
            aligned_origin = brain_to_atlas_transform(origin_um, r, t)                
            volume_origin[structure].append((volume, aligned_origin/scales))

    threshold = 0.05
    for structure, volume_origin_list in volume_origin.items():
        if 'SC' in structure or 'IC' in structure:
            sigma = 5.0
        else:
            sigma = 2.0
        volume, origin = average_shape(volume_origin_list=volume_origin_list, 
                                       force_symmetric=(structure in singular_structures), sigma=sigma)
        try:
            color = sqlController.get_structure_color(structure)
        except:
            color = 100
        
        # mesh
        centered_origin = origin - adjustment
        aligned_volume = (volume >= threshold, centered_origin)
        aligned_structure = volume_to_polydata(volume=aligned_volume,
                               num_simplify_iter=3, smooth=False,
                               return_vertex_face_list=False)
        filepath = os.path.join(ATLAS_PATH, 'mesh', f'{structure}.stl')
        save_mesh_stl(aligned_structure, filepath)
        
        volume[volume >= threshold] = color
        volume[volume < color] = 0
        volume = volume.astype(np.uint8)
        
        #volume = volume >= 0.5
        #volume = volume * color
        #volume = volume.astype(np.uint8)

        
        volume_outpath = os.path.join(ATLAS_PATH, 'structure', f'{structure}.npy')
        origin_outpath = os.path.join(ATLAS_PATH, 'origin', f'{structure}.txt')
        np.save(volume_outpath, volume)
        np.savetxt(origin_outpath, origin)
        
        try:
            ndcom = center_of_mass(volume)
        except:
            print(structure, 'bad ndcome')
            continue
        print(structure, origin, ndcom, volume.shape)   
        add_layer_data_row(structure, origin + ndcom)
        

        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    merge_brains()
