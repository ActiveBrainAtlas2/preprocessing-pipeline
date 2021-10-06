"""
William this is the 3rd script.

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
from datetime import datetime
from abakit.registration.algorithm import brain_to_atlas_transform, umeyama
from scipy.ndimage.measurements import center_of_mass
from skimage.filters import gaussian
from math import isnan

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

def average_shape(volume_xyz_offset_list, force_symmetric=False, sigma=2.0):
    """
    Compute the mean shape based on many co-registered volumes.

    Args:
        force_symmetric (bool): If True, force the resulting volume and mesh to be symmetric wrt z.
        sigma (float): sigma of gaussian kernel used to smooth the probability values.

    Returns:
        average_volume_prob (3D ndarray):
        common_mins ((3,)-ndarray): coordinate of the volume's xyz_offset
    """
    volume_list, xyz_offset_list = list(map(list, list(zip(*volume_xyz_offset_list))))
    bbox_list = [(xm, xm+v.shape[1]-1, ym, ym+v.shape[0]-1, zm, zm+v.shape[2]-1) for v,(xm,ym,zm) in zip(volume_list, xyz_offset_list)]
    common_volume_list, common_volume_bbox = convert_vol_bbox_dict_to_overall_vol(
        vol_bbox_tuples=list(zip(volume_list, bbox_list)))
    common_volume_list = list([(v > 0).astype(np.int32) for v in common_volume_list])
    average_volume = np.sum(common_volume_list, axis=0)
    average_volume_prob = average_volume / float(np.max(average_volume))
    if force_symmetric:
        average_volume_prob = symmetricalize_volume(average_volume_prob)

    average_volume_prob = gaussian(average_volume_prob, sigma) # Smooth the probability
    # print('1',type(average_volume_prob), average_volume_prob.dtype, average_volume_prob.shape, np.mean(average_volume_prob), np.amax(average_volume_prob))
    # common_xyz_offset = np.array(common_volume_bbox)[[0,2,4]]
    # print(common_xyz_offset, np.mean(xyz_offset_list, axis=0))
    # return average_volume_prob, common_xyz_offset
    return average_volume_prob, np.mean(xyz_offset_list, axis=0)



def get_centers(animal):
    rows = session.query(LayerData).filter(
        LayerData.active.is_(True))\
            .filter(LayerData.prep_id == animal)\
            .filter(LayerData.person_id == 2)\
            .filter(LayerData.layer == 'COM')\
            .filter(LayerData.input_type_id == MANUAL)\
            .order_by(LayerData.structure_id)\
            .all()
    data = []
    for row in rows:
        data.append( [row.x, row.y, row.section] )
    return np.array(data)


def add_layer_data_row(abbrev, com):
    structure = session.query(Structure).filter(Structure.abbreviation == func.binary(abbrev)).one()
    
    x,y,z = com
    
    if isnan(x) or isnan(y) or isnan(z):
        print(structure.abbreviation, 'has nan values')
        return

    com_object = LayerData(
        prep_id='Atlas', structure=structure, x=x, y=y, section=z
        , layer='COM',
        created=datetime.utcnow(), active=True, person_id=16, input_type_id=MANUAL
    )
    try:
        session.add(com_object)
        session.commit()
    except Exception as e:
        print(f'No merge {e}')
        session.rollback()



def merge_brains():
    """
    Note! the origin is the x,y,z offset from the top left corner, 1st section
    of the image stack.
    """
    ATLAS_PATH = os.path.join(DATA_PATH, 'atlas_data', 'atlasV8')
    fixed_brain = 'MD589'
    sqlController = SqlController(fixed_brain)
    width = sqlController.scan_run.width // 32
    height = sqlController.scan_run.height // 32
    adjustment = np.array([width//2, height//2, 440//2])
    moving_brains = ['MD585', 'MD594']
    brains = moving_brains + [fixed_brain]
    to_um = 32 * 0.452
    scales = np.array([to_um, to_um, 20])
    volume_com = defaultdict(list)
    fixed_data = get_centers(fixed_brain)        
    # these brains need to be aligned to the fixed brain, hence the 2nd loop
    for brain in brains:
        moving_data = get_centers(brain)
        if brain in moving_brains:
            r, t = umeyama(moving_data.T, fixed_data.T)
        XYZ_OFFSET_PATH = os.path.join(ATLAS_PATH, brain, 'origin')
        xyz_offset_files = sorted(os.listdir(XYZ_OFFSET_PATH))
        VOLUME_PATH = os.path.join(ATLAS_PATH, brain, 'structure')
        volume_files = sorted(os.listdir(VOLUME_PATH))
        for volume_filename, xyz_offset_filename in zip(volume_files, xyz_offset_files):
            structure = os.path.splitext(xyz_offset_filename)[0]    
            xyz_offset = np.loadtxt(os.path.join(XYZ_OFFSET_PATH, xyz_offset_filename))
            volume = np.load(os.path.join(VOLUME_PATH, volume_filename))
            ndcom = center_of_mass(volume)
            ndcom = np.array([ndcom[1], ndcom[0], ndcom[2]])
            xyz_offset_um_with_ndcom = (xyz_offset + ndcom) * scales
            # brain_to_atlas _transform should be called brain_to_brain_transform
            # the units need to be in um with the center of mass
            if brain in moving_brains:
                aligned_com = brain_to_atlas_transform(xyz_offset_um_with_ndcom, r, t)
            else:
                aligned_com = xyz_offset_um_with_ndcom 
            volume_com[structure].append((volume, aligned_com/scales))
            
    # the xyz_offsets are now in neuroglancer coordinates
    for structure, volume_xyz_offset_list in volume_com.items():
        if 'SC' in structure or 'IC' in structure:
            sigma = 5.0
        else:
            sigma = 2.0
        ## look at the average_shape method
        volume, com = average_shape(volume_xyz_offset_list=volume_xyz_offset_list, 
                                       force_symmetric=(structure in singular_structures), sigma=sigma)
        try:
            color = sqlController.get_structure_color(structure)
        except:
            color = 100
        # the max quantile tells you how much of the values to use
        # the smaller the value, the more values and the bigger the shapes
        max_quantile = 0.8 
        threshold = np.quantile(volume[volume > 0], max_quantile)
        volume[volume >= threshold] = color
        volume[volume < color] = 0
        volume = volume.astype(np.uint8)        
        # we need the com again to subtract it from the xyz_offset
        # the script that builds the neuroglancer mesh needs the xyz
        # offsets, not the com
        ndcom = center_of_mass(volume)
        # its important to get the order of the array correct the 
        # the 0=rows=height and 1=columns=width
        ndcom = np.array([ndcom[1], ndcom[0], ndcom[2]])
        xyz_offset = com - ndcom
        
        # mesh for 3D Slicer
        aligned_volume = (volume, xyz_offset - adjustment)
        aligned_structure = volume_to_polydata(volume=aligned_volume,
                               num_simplify_iter=3, smooth=False,
                               return_vertex_face_list=False)
        filepath = os.path.join(ATLAS_PATH, 'mesh', f'{structure}.stl')
        save_mesh_stl(aligned_structure, filepath)
        # finished mesh
        scaled_coms = com*scales
        print(structure, volume.shape, ndcom, threshold, xyz_offset, scaled_coms)
        

        volume_outpath = os.path.join(ATLAS_PATH, 'structure', f'{structure}.npy')
        xyz_offset_outpath = os.path.join(ATLAS_PATH, 'origin', f'{structure}.txt')
        # we want to save the xyz offsets to the origin files as that is what
        # the create_atlas needs
        # we take the real COMs, multiple it by the scales to um and insert
        # into the DB
        if not isnan(xyz_offset[0]):
            np.save(volume_outpath, volume)
            np.savetxt(xyz_offset_outpath, xyz_offset)
            add_layer_data_row(structure, scaled_coms)
        else:
            print(structure, 'has no xyz_offset')
        
        

        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    merge_brains()
