import os
import sys
import argparse

#from utilities2015 import *
#from metadata import *
#from data_manager import *

from distributed_utilities import run_

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='Rename thumbnail images according to our naming format with consecutive section numbers')

parser.add_argument("input_spec", type=str, help="Path to input files specification as ini file")
parser.add_argument("channel", type=int, help="Channel index, -1 to produce gray from RGB.")
parser.add_argument("out_version", type=str, help="Output image version")
parser.add_argument("-j", "--njobs", type=int, help="Number of parallel jobs", default=1)
args = parser.parse_args()

input_spec = load_ini(args.input_spec)

stack = input_spec['stack']
prep_id = input_spec['prep_id']
if prep_id == 'None':
    prep_id = None
resol = input_spec['resol']
version = input_spec['version']
if version == 'None':
    version = None
image_name_list = input_spec['image_name_list']
if image_name_list == 'all':
    image_name_list = DataManager.load_sorted_filenames(stack=stack)[0].keys()

create_if_not_exists(DataManager.get_image_dir_v2(stack=stack, prep_id=prep_id, resol=resol, version=args.out_version))

if args.channel == -1:
    run_distributed('convert \"%(in_fp)s\" -set colorspace Gray -separate -average \"%(out_fp)s\"',
                kwargs_list=[{'in_fp': DataManager.get_image_filepath_v2(stack=stack, prep_id=prep_id, 
                                        resol=resol, version=version, fn=img_name),
                                       'out_fp': DataManager.get_image_filepath_v2(stack=stack, prep_id=prep_id, 
                                        resol=resol, version=args.out_version, fn=img_name)}
                                       for img_name in image_name_list],
                argument_type='single',
                jobs_per_node=args.njobs,
                local_only=True)
else:
    run_distributed('convert \"%%(in_fp)s\" -channel %(channel)s -separate \"%%(out_fp)s\"' % {'channel': 'RGB'[args.channel]},
                kwargs_list=[{'in_fp': DataManager.get_image_filepath_v2(stack=stack, prep_id=prep_id, 
                                        resol=resol, version=version, fn=img_name),
                                       'out_fp': DataManager.get_image_filepath_v2(stack=stack, prep_id=prep_id, 
                                        resol=resol, version=args.out_version, fn=img_name)}
                                       for img_name in image_name_list],
                argument_type='single',
                jobs_per_node=args.njobs,
                local_only=True)

