import argparse
import os
import numpy as np
from utilities.utilities2015 import load_ini, dict_to_csv, execute_command
from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager
from utilities.data_manager_v2 import DataManager

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description="""Align consecutive images. Possible bad alignment pairs are written into a separate file.
Usage 1: align_compose.py in.ini --op from_none_to_aligned
"""
)

parser.add_argument("input_spec", type=str, help="input specifier. ini")
parser.add_argument("--op", type=str, help="operation id")

args = parser.parse_args()
print('args', args)

input_spec = load_ini(args.input_spec)
stack = input_spec['stack']
sqlController = SqlController()
fileLocationManager = FileLocationManager(stack)



execute_command('python align_v3.py %s --op %s' % (args.input_spec, args.op))
# execute_command('python compose_v3.py %s --op %s' % (args.input_spec, args.op))



#image_name_list = input_spec['image_name_list']
image_name_list  = sqlController.get_image_list(stack, 'destination')
#if image_name_list == 'all':
#    #image_name_list = DataManager.load_sorted_filenames(stack=stack)[0].keys()
#    image_name_list = map(lambda x: x[0], sorted(DataManager.load_sorted_filenames(stack=input_spec['stack'])[0].items(), key=lambda x: x[1]))

#op = load_ini(os.path.join(DATA_ROOTDIR, 'CSHL_data_processed', input_spec['stack'], 'operation_configs', args.op + '.ini'))
op = load_ini(os.path.join(fileLocationManager.operation_configs,  args.op + '.ini'))
assert op['type'] == 'warp', "Op type  must be warp."
assert op['base_prep_id'] == input_spec['prep_id'], "Op requires %s, but input has prep %s." % (op['base_prep_id'], input_spec['prep_id'])

elastix_output_dir = fileLocationManager.elastix_dir
custom_output_dir = fileLocationManager.custom_output
toanchor_transforms_fp = op['transforms_csv']
#anchor_img_name = op['anchor_image_name']
anchor_img_name = image_name_list[0]
base_prep_id = op['base_prep_id']

#################################################

anchor_idx = image_name_list.index(anchor_img_name)

transformation_to_previous_sec = {}

for i in range(1, len(image_name_list)):

    transformation_to_previous_sec[i] = DataManager.load_consecutive_section_transform(moving_fn=image_name_list[i],
                                                                                       fixed_fn=image_name_list[i-1],
                                                                                       stack=input_spec['stack'])
    #transformation_to_previous_sec[i] = DataManager.load_consecutive_section_transform(moving_fn=image_name_list[i], fixed_fn=image_name_list[i-1], elastix_output_dir=elastix_output_dir, custom_output_dir=custom_output_dir)

transformation_to_anchor_sec = {}

# Converts every transformation
for moving_idx in range(len(image_name_list)):

    if moving_idx == anchor_idx:
        # transformation_to_anchor_sec[moving_idx] = np.eye(3)
        transformation_to_anchor_sec[image_name_list[moving_idx]] = np.eye(3)

    elif moving_idx < anchor_idx:
        T_composed = np.eye(3)
        for i in range(anchor_idx, moving_idx, -1):
            T_composed = np.dot(np.linalg.inv(transformation_to_previous_sec[i]), T_composed)
        # transformation_to_anchor_sec[moving_idx] = T_composed
        transformation_to_anchor_sec[image_name_list[moving_idx]] = T_composed

    else:
        T_composed = np.eye(3)
        for i in range(anchor_idx+1, moving_idx+1):
            T_composed = np.dot(transformation_to_previous_sec[i], T_composed)
        # transformation_to_anchor_sec[moving_idx] = T_composed
        transformation_to_anchor_sec[image_name_list[moving_idx]] = T_composed

    print(moving_idx, image_name_list[moving_idx], transformation_to_anchor_sec[image_name_list[moving_idx]])

#################################################

dict_to_csv(transformation_to_anchor_sec, toanchor_transforms_fp)

