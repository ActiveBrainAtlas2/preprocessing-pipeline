import os
import subprocess
import time
import numpy as np
import cv2
import matplotlib.pyplot as plt

from utilities.data_manager_v2 import DataManager
from utilities.metadata import ordered_pipeline_steps
from utilities.file_location import FileLocationManager


def create_input_spec_ini_all(name, stack, prep_id, version, resol):
    f = open(name, "w")
    f.write('[DEFAULT]\n')
    f.write('image_name_list = all\n')
    f.write('stack = '+stack+'\n')
    f.write('prep_id = '+prep_id+'\n')
    f.write('version = '+version+'\n')
    f.write('resol = '+resol+'\n')

def save_dict_as_ini(input_dict, fp):
    import configparser
    assert 'DEFAULT' in input_dict.keys()

    config = configparser.ConfigParser()

    for key in input_dict.keys():
        config[key] = input_dict[key]

    with open(fp, 'w') as configfile:
        config.write(configfile)


def call_and_time(command_list, completion_message=''):
    start_t = time.time()
    subprocess.call(command_list)
    end_t = time.time()

    if command_list[0] == 'python':
        print('**************************************************************************************************')
        print('\nScript ' + command_list[1] + ' completed. Took ', round(end_t - start_t, 1), ' seconds')
        print(completion_message + '\n')
        print('**************************************************************************************************')

def get_prep5_limits_from_prep1_thumbnail_masks( stack, max_distance_to_scan_from_midpoint=25,
                                                 plot_progression=False):
    prep_id = 1
    version = 'mask'
    resol = 'thumbnail'

    sec_to_fn_dict = DataManager.load_sorted_filenames(stack=stack)[1]

    midpoint = int( np.mean( DataManager.load_sorted_filenames(stack=stack)[1].keys() ) )
    max_distance = max_distance_to_scan_from_midpoint

    # Only keeps sections within a max_distance of the midpoint
    for i in sec_to_fn_dict.keys():
        try:
            if i not in range( midpoint-max_distance, midpoint+max_distance):
                del sec_to_fn_dict[i]
            if sec_to_fn_dict[i] == 'Placeholder':
                del sec_to_fn_dict[i]
        except KeyError:
            pass


    # Get dimensions of the first image in the list (will be the same for all)
    img_fp = DataManager.get_image_filepath(stack=stack, resol=resol, version=version,
                                               fn=sec_to_fn_dict[sec_to_fn_dict.keys()[0]])
    height, width, channels = cv2.imread( img_fp ).shape
    height_d16 = height/16
    width_d16 = width/16

    curr_rostral_lim_d16 = width_d16
    curr_caudal_lim_d16 = 0
    curr_dorsal_lim_d16 = height_d16
    curr_ventral_lim_d16 = 0


    for img_name in sec_to_fn_dict.values():
        # Get the image filepath and then load the image, downsampling
        # an additional 16x for speed
        img_fp = DataManager.get_image_filepath(stack=stack, resol=resol, version=version, fn=img_name)
        img_thumbnail_mask_down16 = cv2.imread( img_fp )[::16,::16]

        # update rostral lim
        for col_i in range( curr_rostral_lim_d16 ):
            col = img_thumbnail_mask_down16[ :, col_i]

            contains_tissue = np.array( col ).any()

            if contains_tissue:
                curr_rostral_lim_d16 = min( curr_rostral_lim_d16, col_i )
                break

        # update caudal lim
        caudal_range = range( curr_caudal_lim_d16, width_d16)
        caudal_range = reversed(caudal_range) # Goes from right of image to left
        for col_i in caudal_range:
            col = img_thumbnail_mask_down16[ :, col_i]

            contains_tissue = np.array( col ).any()

            if contains_tissue:
                curr_caudal_lim_d16 = max( curr_caudal_lim_d16, col_i )
                break

        # update dorsal lim
        for row_i in range( curr_dorsal_lim_d16 ):
            row = img_thumbnail_mask_down16[ row_i, :]

            contains_tissue = np.array( row ).any()

            if contains_tissue:
                curr_dorsal_lim_d16 = min( curr_dorsal_lim_d16, row_i )
                break

        # update ventral lim
        ventral_range = range( curr_ventral_lim_d16, height_d16)
        ventral_range = reversed(ventral_range) # Goes from right of image to left
        for row_i in ventral_range:
            row = img_thumbnail_mask_down16[ row_i, :]

            contains_tissue = np.array( row ).any()

            if contains_tissue:
                curr_ventral_lim_d16 = max( curr_ventral_lim_d16, row_i )
                break

        if plot_progression:
            plt.imshow( img_thumbnail_mask_down16 )
            plt.scatter( [curr_rostral_lim_d16, curr_rostral_lim_d16, curr_caudal_lim_d16, curr_caudal_lim_d16],
                         [curr_dorsal_lim_d16, curr_ventral_lim_d16, curr_dorsal_lim_d16, curr_ventral_lim_d16],
                         c='r')
            plt.show()

    # Make the boundary slightly larger
    final_rostral_lim = (curr_rostral_lim_d16-1.5)*16
    final_caudal_lim = (curr_caudal_lim_d16+1.5)*16
    final_dorsal_lim = (curr_dorsal_lim_d16-1.5)*16
    final_ventral_lim = (curr_ventral_lim_d16+1.5)*16
    # If boundary goes past the image, reset to the min/max value
    final_rostral_lim = max( final_rostral_lim, 0 )
    final_caudal_lim = min( final_caudal_lim, width )
    final_dorsal_lim = max( final_dorsal_lim, 0 )
    final_ventral_lim = min( final_ventral_lim, height )

    print('rostral:',final_rostral_lim)
    print('caudal:',final_caudal_lim)
    print('dorsal:',final_dorsal_lim)
    print('ventral:',final_ventral_lim)

    return final_rostral_lim, final_caudal_lim, final_dorsal_lim, final_ventral_lim

def revert_to_prev_step( stack, target_step ):
    progress_dict = {}

    passed_target_step = False
    for step in ordered_pipeline_steps:
        # Set all steps before "target_step" as completed, all after as incomplete
        if passed_target_step:
            progress_dict[step] = False
        else:
            if step==target_step:
                progress_dict[step] = False
                passed_target_step = True
            else:
                progress_dict[step] = True

    # Save PROGRESS ini
    progress_ini_to_save = {}
    progress_ini_to_save['DEFAULT'] = progress_dict

    # Get filepath and save ini
    fp = DataManager.get_brain_info_progress( stack )
    save_dict_as_ini( progress_ini_to_save, fp )

def make_from_x_to_y_ini(stack,x,y,rostral_limit,caudal_limit,dorsal_limit,ventral_limit):
    '''
    Creates operation configuration files that specify the cropping boxes for either the whole brain, or the brainstem.
    '''
    fileLocationManager = FileLocationManager(stack)
    base_prep_id=''
    dest_prep_id=''
    if x=='aligned':
        base_prep_id = 'aligned'
    elif x=='padded':
        base_prep_id = 'alignedPadded'
    if y=='wholeslice':
        dest_prep_id = 'alignedWithMargin'
    elif y=='brainstem':
        dest_prep_id = 'alignedBrainstemCrop'

    fn = os.path.join(fileLocationManager.operation_configs, 'from_'+x+'_to_'+y+'.ini' )
    f = open(fn, "w")
    f.write('[DEFAULT]\n')
    f.write('type = crop\n\n')
    f.write('base_prep_id = '+base_prep_id+'\n')
    f.write('dest_prep_id = '+dest_prep_id+'\n\n')
    f.write('rostral_limit = '+str(rostral_limit)+'\n')
    f.write('caudal_limit = '+str(caudal_limit)+'\n')
    f.write('dorsal_limit = '+str(dorsal_limit)+'\n')
    f.write('ventral_limit = '+str(ventral_limit)+'\n')
    f.write('resolution = thumbnail')
    f.close()

def create_prep2_section_limits( stack, lower_lim, upper_lim):
    fileLocationManager = FileLocationManager(stack)
    fn = os.path.join(fileLocationManager.brain_info, 'prep2_sectionLimits.ini' )
    f = open(fn, "w")
    f.write('[DEFAULT]\n')
    f.write('left_section_limit = '+str(lower_lim)+'\n')
    f.write('right_section_limit = '+str(upper_lim)+'\n')
    f.close()

def make_manual_anchor_points( stack, x_12N, y_12N, x_3N, y_3N, z_midline):
    fileLocationManager = FileLocationManager(stack)

    fn = os.path.join(fileLocationManager.brain_info, 'manual_anchor_points.ini' )
    f = open(fn, "w")
    f.write('[DEFAULT]\n')
    f.write('x_12N = '+str(x_12N)+'\n')
    f.write('y_12N = '+str(y_12N)+'\n')
    f.write('x_3N = '+str(x_3N)+'\n')
    f.write('y_3N = '+str(y_3N)+'\n')
    f.write('z_midline = '+str(z_midline))
    f.close()

