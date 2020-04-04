import os
import argparse

from utilities.data_manager_v2 import DataManager
from utilities.a_driver_utilities import call_and_time, create_input_spec_ini_all
from utilities.metadata import REPO_DIR
from utilities.sqlcontroller import SqlController

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='Generates binary masks for every image to segment the pixels containing the brain.')

parser.add_argument("stack", type=str, help="The name of the stack")
parser.add_argument("stain", type=str, help="Either \'NTB\' or \'Thionin\'.")
args = parser.parse_args()
stack = args.stack
stain = args.stain

if stain == 'NTB':
    # Generate masks
    create_input_spec_ini_all( name='input_spec.ini', stack=stack, \
                prep_id='alignedPadded', version='NtbNormalized', resol='thumbnail')
    fp = os.path.join(os.environ['DATA_ROOTDIR'],'CSHL_data_processed',stack,\
                      stack+'_prep1_thumbnail_initSnakeContours.pkl')
    command = [ 'python', 'masking.py', 'input_spec.ini', fp]
    completion_message = 'Automatic mask creation finished.'
    call_and_time( command, completion_message=completion_message)

if stain == 'Thionin':
    # Generate masks
    create_input_spec_ini_all( name='input_spec.ini', stack=stack, \
                prep_id='alignedPadded', version='gray', resol='thumbnail')
    fp = os.path.join(os.environ['DATA_ROOTDIR'],'CSHL_data_processed',stack,\
                      stack+'_prep1_thumbnail_initSnakeContours.pkl')
    command = [ 'python', 'masking.py', 'input_spec.ini', fp]
    completion_message = 'Automatic mask creation finished.'
    call_and_time( command, completion_message=completion_message)

print('\nMask generation finished, check using the following command:\n')
print('`python ../src/gui/mask_editing_tool_v4.py $stack NtbNormalized`')
