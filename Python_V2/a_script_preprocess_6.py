import os
import sys
import argparse

from utilities.a_driver_utilities import call_and_time, create_input_spec_ini_all, make_from_x_to_y_ini, \
    create_prep2_section_limits
from utilities.metadata import REPO_DIR, DATA_ROOTDIR
from utilities.sqlcontroller import SqlController

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='Using the user specified brainstem cropbox, cropped images are generated and saved as raw "prep2" images. Thumbnails are then generated. Raw prep2 images are compressed into jpeg format. Finally the masks are cropped to match the prep2 images. These raw prep2 images are finished being processed, they are the images that will be used throughout the rest of the pipeline.')

parser.add_argument("stack", type=str, help="The name of the stack")
parser.add_argument("stain", type=str, help="Either \'NTB\' or \'Thionin\'.")
parser.add_argument('-l','--list', nargs='+', help='<Required> Set flag', required=True)
args = parser.parse_args()
stack = args.stack
stain = args.stain
rostral_limit, caudal_limit, dorsal_limit, ventral_limit, prep2_section_min, prep2_section_max = args.list

# Create from_padded_to_brainstem.ini
make_from_x_to_y_ini( stack, x='padded', y='brainstem',\
                     rostral_limit=rostral_limit, caudal_limit=caudal_limit,\
                     dorsal_limit=dorsal_limit, ventral_limit=ventral_limit)
# Create prep2-section_limits.ini
create_prep2_section_limits(stack, prep2_section_min, prep2_section_max)

if stain == 'NTB':
    tb_version = 'NtbNormalizedAdaptiveInvertedGamma'
if stain == 'Thionin':
    tb_version = 'gray'

if stain == 'NTB':
    create_input_spec_ini_all( name='input_spec.ini', stack=stack, \
                prep_id='alignedWithMargin', version='NtbNormalizedAdaptiveInvertedGamma', resol='raw')
    # Creates prep2 raw images
    fp =  os.path.join(DATA_ROOTDIR, 'CSHL_data_processed',stack, 'operation_configs', 'from_wholeslice_to_brainstem')
    command = [ 'python', 'warp_crop_v3.py', '--input_spec', 'input_spec.ini', '--op_id', fp]
    completion_message = 'Finished creating brainstem crop of preprocessed image.'
    call_and_time( command, completion_message=completion_message)

    create_input_spec_ini_all( name='input_spec.ini', stack=stack, \
                prep_id='alignedBrainstemCrop', version='NtbNormalizedAdaptiveInvertedGamma', resol='raw')
    # Creates prep2 thumbnail images
    command = [ 'python', 'rescale.py', 'input_spec.ini', 'thumbnail', '-f', '0.03125']
    completion_message = 'Finished generating thumbnails for final preprocessed images.'
    call_and_time( command, completion_message=completion_message)

    create_input_spec_ini_all( name='input_spec.ini', stack=stack, \
                prep_id='alignedBrainstemCrop', version='NtbNormalizedAdaptiveInvertedGamma', resol='raw')
    # Compresses prep2 raw images into jpeg format
    command = [ 'python', 'compress_jpeg.py', 'input_spec.ini']
    completion_message = 'Finished compressing preprocessed images into jpegs.'
    call_and_time( command, completion_message=completion_message)

    create_input_spec_ini_all( name='input_spec.ini', stack=stack, 
                prep_id='alignedPadded', version='mask', resol='thumbnail')
    # Create prep2 thumbnail masks
    fp =  os.path.join(DATA_ROOTDIR, 'CSHL_data_processed', stack, 'operation_configs', 'from_padded_to_brainstem')
    command = [ 'python', 'warp_crop_v3.py', '--input_spec', 'input_spec.ini', '--op_id', fp]
    completion_message = 'Finished creating prep2 thumbnail masks.'
    call_and_time( command, completion_message=completion_message)
    
    create_input_spec_ini_all( name='input_spec.ini', stack=stack, \
                prep_id='alignedPadded', version='mask', resol='thumbnail')
    # Creates prep5 thumbnail masks
    fp =  os.path.join(DATA_ROOTDIR, 'CSHL_data_processed',stack, 'operation_configs', 'from_padded_to_wholeslice')
    command = [ 'python', 'warp_crop_v3.py', '--input_spec', 'input_spec.ini', '--op_id', fp]
    completion_message = 'Finished creating prep5 brainstem thumbnail images.'
    call_and_time( command, completion_message=completion_message)

if stain == 'Thionin':
    create_input_spec_ini_all( name='input_spec.ini', stack=stack, \
                prep_id='alignedWithMargin', version='gray', resol='raw')
    # Creates prep2 raw images
    fp =  os.path.join(DATA_ROOTDIR, 'CSHL_data_processed',stack, 'operation_configs', 'from_wholeslice_to_brainstem')
    command = [ 'python', 'warp_crop_v3.py', '--input_spec', 'input_spec.ini', '--op_id', fp]
    completion_message = 'Finished creating brainstem crop of preprocessed image.'
    call_and_time( command, completion_message=completion_message)

    create_input_spec_ini_all( name='input_spec.ini', stack=stack, \
                prep_id='alignedBrainstemCrop', version='gray', resol='raw')
    # Creates prep2 thumbnail images
    command = [ 'python', 'rescale.py', 'input_spec.ini', 'thumbnail', '-f', '0.03125']
    completion_message = 'Finished generating thumbnails for final preprocessed images.'
    call_and_time( command, completion_message=completion_message)

    create_input_spec_ini_all( name='input_spec.ini', stack=stack, \
                prep_id='alignedBrainstemCrop', version='gray', resol='raw')
    # Compresses prep2 raw images into jpeg format
    command = [ 'python', 'compress_jpeg.py', 'input_spec.ini']
    completion_message = 'Finished compressing preprocessed images into jpegs.'
    call_and_time( command, completion_message=completion_message)

    create_input_spec_ini_all( name='input_spec.ini', stack=stack, 
                prep_id='alignedPadded', version='mask', resol='thumbnail')
    # Create prep2 thumbnail masks
    fp =  os.path.join(DATA_ROOTDIR, 'CSHL_data_processed', stack, 'operation_configs', 'from_padded_to_brainstem')
    command = [ 'python', 'warp_crop_v3.py', '--input_spec', 'input_spec.ini', '--op_id', fp]
    completion_message = 'Finished creating prep2 thumbnail masks.'
    call_and_time( command, completion_message=completion_message)
    
    
# Compute intensity volumes
script_fp =  os.path.join( os.environ['REPO_DIR'], 'reconstruct', 'construct_intensity_volume.py')
command = [ 'python', script_fp, stack, '--tb_version', tb_version, '--tb_resol', 'thumbnail']
completion_message = 'Finished constructing intensity volume.'
call_and_time( command, completion_message=completion_message)