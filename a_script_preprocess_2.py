import os
import argparse
from utilities.a_driver_utilities import call_and_time, create_input_spec_ini_all
from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager
from utilities.metadata import REPO_DIR

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='Generates image translation and rotation alignment parameters, one "anchor" file is chosen which all other images are aligned to. User can choose to pass an images filename in to be the anchor image, otherwise the anchor image will be chosen automatically. Image alignment parameters are applied and the new aligned image stack is saved as so called "prep1" images. The background is padded white for T stain and black for NTB stain.')

parser.add_argument("stack", type=str, help="The name of the stack")
parser.add_argument("stain", type=str, help="Either \'NTB\' or \'Thionin\'.")
parser.add_argument('--anchor_fn', default="auto", type=str)
args = parser.parse_args()
stack = args.stack
stain = args.stain
stain = stain.lower()
anchor_fn = args.anchor_fn

fileLocationManager = FileLocationManager(stack)


def create_from_none_to_aligned_file():
    # images_root_folder = os.path.join(ROOT_DIR, stack, 'preps')
    elastix_output = fileLocationManager.elastix_dir
    custom_output = fileLocationManager.custom_output
    none_to_aligned_fp = os.path.join(fileLocationManager.brain_info, 'from_none_to_aligned.ini')
    transforms_to_anchor = os.path.join(fileLocationManager.brain_info, 'transforms_to_anchor.csv')
    from_none_to_aligned_content = '[DEFAULT]\n\
type=warp\n\
\n\
base_prep_id=None\n\
dest_prep_id=aligned\n\
\n\
# For align\n\
elastix_parameter_fp=' + REPO_DIR + '/preprocess/parameters/Parameters_Rigid_MutualInfo_noNumberOfSpatialSamples_4000Iters.txt\n\
elastix_output_dir=' + elastix_output + '\n\
custom_output_dir=' + custom_output + '\n\
\n\
# For compose\n\
anchor_image_name=' + anchor_fn + '\n\
transforms_csv=' + transforms_to_anchor + '\n\
resolution=thumbnail'

    if not os.path.exists(os.path.dirname(elastix_output)):
        os.makedirs(os.path.dirname(elastix_output))
    if not os.path.exists(os.path.dirname(custom_output)):
        os.makedirs(os.path.dirname(custom_output))

    f = open(none_to_aligned_fp, "w")
    f.write(from_none_to_aligned_content)
    f.close()


def create_anchor_file(stack, anchor_fn='auto'):
    """
    This method gets the current entry from valid sections and writes it to a file
    Args:
        stack: animal
        anchor_fn: auto
    Returns: a string of the file name
    """
    if anchor_fn == 'auto':
        sqlController = SqlController()
        valid_sections = sqlController.get_valid_sections(stack)
        valid_section_keys = sorted(list(valid_sections))
        curr_section_index = len(valid_section_keys) // 2
        anchor_fn = valid_sections[valid_section_keys[curr_section_index]]['destination']

    # First designate an anchor to use
    anchor_text_fp = os.path.join(fileLocationManager.brain_info, 'anchor.txt')

    f = open(anchor_text_fp, "w")
    f.write(anchor_fn)
    f.close()
    # Returns the chosen anchor filename just in case it is being suto-selected
    return anchor_fn


# Create 2 files necessary for running the following 2 scripts
anchor_fn = create_anchor_file(stack, anchor_fn=anchor_fn)
create_from_none_to_aligned_file()

if stain == 'ntb':
    create_input_spec_ini_all(name='input_spec.ini', \
                              stack=stack, prep_id='None', version='NtbNormalized', resol='thumbnail')
    command = ['python', 'align_compose.py', 'input_spec.ini', '--op', 'from_none_to_aligned']
    completion_message = 'Finished preliminary alignment.'
    call_and_time(command, completion_message=completion_message)

    command = ['python', 'warp_crop.py', '--input_spec', 'input_spec.ini', '--op_id', 'from_none_to_padded', '--njobs',
               '8', '--pad_color', 'black']
    completion_message = 'Finished transformation to padded (prep1).'
    call_and_time(command, completion_message=completion_message)

if stain == 'thionin':
    create_input_spec_ini_all(name='input_spec.ini', \
                              stack=stack, prep_id='None', version='gray', resol='thumbnail')
    command = ['python', 'align_compose.py', 'input_spec.ini', '--op', 'from_none_to_aligned']
    completion_message = 'Finished preliminary alignment.'
    call_and_time(command, completion_message=completion_message)

    command = ['python', 'warp_crop.py', '--input_spec', 'input_spec.ini', '--op_id', 'from_none_to_padded', '--njobs',
               '8', '--pad_color', 'white']
    completion_message = 'Finished transformation to padded (prep1).'
    call_and_time(command, completion_message=completion_message)

print('\nNow manually fix any incorrect alignments. Custom GUI available with the following command:\n')
print('`python ../src/gui/preprocess_tool_v3.py UCSD001 --tb_version NtbNormalized/gray`')
