"""
This was formerly align_v3.py. It has been renamed to more easily track the sequence of operations.
This file just sets up the DIR path of the input and output files.
It calls a method called run_distributed which spawns multiple python processes to run the next script:
align_sequential. This is the program that runs the command line tool: elastix
"""
import os, sys
import argparse

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.alignment_utility import run_distributed
from utilities.file_location import FileLocationManager



def setup(stack):
    fileLocationManager = FileLocationManager(stack)
    elastix_output_dir = fileLocationManager.elastix_dir
    params_fp =  "Parameters_Rigid_MutualInfo_noNumberOfSpatialSamples_4000Iters.txt"

    filepath = fileLocationManager.masked
    image_name_list = sorted(os.listdir(filepath))
    run_distributed(stack, "python %(script)s \"%(output_dir)s\" \'%%(kwargs_str)s\' -p %(param_fp)s" % \
                    {'script': os.path.join(os.getcwd(), 'alignment_elastix.py'),
                    'output_dir': elastix_output_dir,
                     'param_fp': params_fp
                    },
                    kwargs_list=[{'prev_img_name': image_name_list[i-1],
                                  'curr_img_name': image_name_list[i],
                                  'prev_fp': os.path.join(filepath, image_name_list[i-1]),
                                  'curr_fp': os.path.join(filepath, image_name_list[i])
                                 }
                                for i in range(1, len(image_name_list))],
                    argument_type='list', jobs_per_node=16, local_only=True)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    args = parser.parse_args()
    animal = args.animal
    setup(animal)
