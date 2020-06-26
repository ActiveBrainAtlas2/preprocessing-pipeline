import sys
import os

#import json
#import numpy as np


# <VERSION> = 'gray' or 'ntbNormalizedAdaptiveInvertedGamma'
# <STACK> = name of the stack
# <RES> = xy5um z20um is the most common
# <COLOR_I>/<THICKNESS_I> = index of the color scheme and thickness scheme used
#       - example, color_i=1 links to a specific json color mapping file.
#       - example, thickness_i=1 links to a json file encoding contour point density / thickness
# <OFFSET_I> = boolean. True if volume(s) has offset. False if begins at image origin (origin=[0,0,0]).

## Volume filepaths
def get_volume_root_fp( stack, precomputed=True, human_annotated=True ):
    # Volumes are either in 3D matrix form, or precomputed form
    if precomputed:
        volume_fp_root = os.path.join( os.environ['NG_ROOT_DIR'], 'Neuroglancer_Volumes', \
                                      'Precomputed', stack )
    else:
        volume_fp_root = os.path.join( os.environ['NG_ROOT_DIR'], 'Neuroglancer_Volumes', \
                                      'Matrix', stack )
    # Volumes are either reconstructed from human annotation, for are a result of the registration script
    if human_annotated:
        volume_fp_root = os.path.join( volume_fp_root, 'human_annotation' )
    else:
        volume_fp_root = os.path.join( volume_fp_root, 'registration' )
        
    return volume_fp_root

def get_volume_fp( stack, precomputed=True, human_annotated=True, volume_type='combined', brain_crop='brainstem', \
                  xy_res=5, z_res=20, offset=False, color_scheme=1, thickness_scheme=1, structure=None ):
    '''
    Returns the full path of the neuroglancer volume files you are working with.
    '''
    assert volume_type=='structure' or volume_type=='combined'
    assert brain_crop=='brainstem' or brain_crop=='wholebrain' or brain_crop==2 or brain_crop==5
    assert offset==True or offset==False
    
    
    volume_fp_root = get_volume_root_fp( stack, precomputed=precomputed, human_annotated=human_annotated )
    
    if brain_crop==2:
        brain_crop=='brainstem'
    elif brain_crop==5:
        brain_crop=='wholebrain'
    
    # volume_type dictates whether we use folder 'combined_volume' (all structures combined) \
    # or 'structure_volumes'
    if volume_type=='combined':
        folder_name_1 = 'combined_volume'
    elif volume_type=='structure':
        folder_name_1 = 'structure_volumes'
    volume_fp = os.path.join( volume_fp_root, folder_name_1 )
    
    # The next folder's name is dictated by resolution in xy plane and z plane
    folder_name_2 = brain_crop+'_xy'+str(xy_res)+'um_z'+str(z_res)+'um'
    volume_fp = os.path.join( volume_fp, folder_name_2 )
    
    # The folder at the lowest level encodes the color_scheme, thickness_sceme, and whether 
    # the volumes have an offset (True) or if the volumes start at the origin (False)
    folder_name_3 = 'color_'+str(color_scheme)+'_thickness_'+str(thickness_scheme)+\
                    '_offset_'+str(int(offset))
    volume_fp = os.path.join( volume_fp, folder_name_3 )+'/'
    
    # If the volume is for a single structure, then there is one last folder level that \
    # designates the contained structure volume
    if volume_type=='structure':
        assert structure!=None
        folder_name_4 = structure
        volume_fp = os.path.join( volume_fp, folder_name_4)+'/'
    
    return volume_fp

## Image filepaths
def get_image_root_fp( stack, precomputed=True ):
    # Volumes are either in jpeg form (raw), or precomputed form
    if precomputed:
        image_fp_root = os.path.join( os.environ['NG_ROOT_DIR'], 'Neuroglancer_Images', \
                                      'Precomputed', stack )
    else:
        image_fp_root = os.path.join( os.environ['NG_ROOT_DIR'], 'Neuroglancer_Images', \
                                      'Raw', stack )
    return image_fp_root

def get_image_fp( stack, precomputed=True, brain_crop='brainstem', \
                 image_version='grayJpeg', resolution='raw' ):
    '''
    Returns the full path of the neuroglancer image files you are working with.
    '''
    assert brain_crop=='brainstem' or brain_crop=='wholebrain' or brain_crop==2 or brain_crop==5
    assert image_version=='grayJpeg' or image_version=='ntbNormalizedAdaptiveInvertedGammaJpeg'
    assert resolution=='raw' or resolution=='lossless'
    
    image_root_fp = get_image_root_fp( stack, precomputed=precomputed )
    
    if brain_crop=='brainstem':
        brain_crop=2
    elif brain_crop=='wholebrain':
        brain_crop=5
    
    folder_name_1 = stack+'_prep'+str(brain_crop)+'_'+resolution+'_'+image_version
    if precomputed:
        folder_name_1 = folder_name_1+'_precomputed'
        
    image_fp = os.path.join( image_root_fp, folder_name_1)+'/'
    
    return image_fp


def get_json_cache_fp():
    return os.path.join( os.environ['NG_REPO_DIR'], 'json_cache')+'/'

def get_src_fp():
    return os.path.join( os.environ['NG_REPO_DIR'], 'src')+'/'

def get_utilities_fp():
    return os.path.join( os.environ['NG_REPO_DIR'], 'src', 'utilities')+'/'

def test():
    return os.environ['NG_REPO_DIR']