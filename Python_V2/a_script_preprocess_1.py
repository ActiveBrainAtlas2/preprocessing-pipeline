import os
import sys
import argparse

from utilities.data_manager_v2 import DataManager
from utilities.a_driver_utilities import call_and_time, create_input_spec_ini_all
from utilities.sqlcontroller import SqlController

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='Converts image format to tiff, extracts different channels')

parser.add_argument("stack", type=str, help="The name of the stack")
parser.add_argument("stain", type=str, help="Either \'NTB\' or \'Thionin\'.")
args = parser.parse_args()
stack = args.stack
stain = args.stain


# Do quality check on sorted_filenames.txt

# Make sure ROOT_DIR/CSHL_data_processed/STACK/STACK_raw/SLICE_raw.tif files all exist, otherwise can't continue
sorted_fns = DataManager.get_fn_list_from_sorted_filenames(stack)
for fn in sorted_fns:
    fp_tif = os.path.join(DataManager.get_images_root_folder(stack), stack + '_raw', fn + '_raw.tif')
    fp_tif_generic = os.path.join(DataManager.get_images_root_folder(stack), stack + '_raw', '<FILENAME>_raw.tif')
    # fp_tif = ROOT_DIR+'CSHL_data_processed/'+stack+'/'+stack+'_raw/'+fn+'_raw.tif'
    if not os.path.isfile(fp_tif):
        print('')
        print('_________________________________________________________________________________')
        print('_________________________________________________________________________________')
        print('Raw files either not located at proper location or not named properly.')
        print('Files must be located at this filepath: ' + fp_tif_generic)
        print('Files must be named using the convention: <FILENAME>_raw.tif')
        print('_________________________________________________________________________________')
        print('_________________________________________________________________________________')
        sys.exit()

if stain == 'NTB':
    # Extract the BLUE channel, for NTB brains
    create_input_spec_ini_all(name='input_spec.ini', stack=stack, prep_id='None', version='None', resol='raw')
    command = ["python", "extract_channel.py", "input_spec.ini", "2", "Ntb"]
    completion_message = 'Extracted BLUE channel.'
    call_and_time(command, completion_message=completion_message)

    # Create Thumbnails of each raw image
    create_input_spec_ini_all(name='input_spec.ini', stack=stack, prep_id='None', version='Ntb', resol='raw')
    command = ["python", "rescale.py", "input_spec.ini", "thumbnail", "-f", "0.03125"]
    completion_message = 'Generated thumbnails.'
    call_and_time(command, completion_message=completion_message)

    # Normalize intensity using thumbnails
    create_input_spec_ini_all(name='input_spec.ini', stack=stack, prep_id='None', version='Ntb', resol='thumbnail')
    command = ["python", "normalize_intensity.py", "input_spec.ini", "NtbNormalized"]
    completion_message = 'Normalized intensity.'
    call_and_time(command, completion_message=completion_message)

if stain == 'Thionin':
    # Create Thumbnails of eachraw image
    create_input_spec_ini_all(name='input_spec.ini', stack=stack, prep_id='None', version='None', resol='raw')
    command = ["python", "rescale.py", "input_spec.ini", "thumbnail", "-f", "0.03125"]
    completion_message = 'Generated thumbnails.'
    call_and_time(command, completion_message=completion_message)

    # Extract the BLUE channel, for Thionin brains
    create_input_spec_ini_all(name='input_spec.ini', stack=stack, prep_id='None', version='None', resol='raw')
    command = ["python", "extract_channel.py", "input_spec.ini", "2", "gray"]
    completion_message = 'Extracted BLUE channel.'
    call_and_time(command, completion_message=completion_message)

    # Create Thumbnails of each gray image
    create_input_spec_ini_all(name='input_spec.ini', stack=stack, prep_id='None', version='gray', resol='raw')
    command = ["python", "rescale.py", "input_spec.ini", "thumbnail", "-f", "0.03125"]
    completion_message = 'Generated thumbnails.'
    call_and_time(command, completion_message=completion_message)

print('\nNow check slice orientations before alignment, correct any mistakes.')
