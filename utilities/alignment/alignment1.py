"""
This was formerly align_v3.py
"""
import os
import sys
import argparse

from old_methods import run_distributed


def setup(stack):
    prep_id = None
    resol = 'thumbnail'
    version = 'NtbNormalized'
    elastix_output_dir = "/mnt/data/CSHL_data_processed/DK43/DK43_elastix_output"
    params_fp =  "Parameters_Rigid_MutualInfo_noNumberOfSpatialSamples_4000Iters.txt"

    """
    to get the files below, it was calling:
    'prev_fp': DataManager.get_image_filepath_v2(stack=stack, fn=image_name_list[i-1], prep_id=prep_id, resol=resol, version=version),
    'curr_fp': DataManager.get_image_filepath_v2(stack=stack, fn=image_name_list[i], prep_id=prep_id, resol=resol, version=version)
    """

    filepath = '/mnt/data/CSHL_data_processed/{}/thumbnail'.format(stack)
    image_name_list = sorted(os.listdir(filepath))
    run_distributed("python %(script)s \"%(output_dir)s\" \'%%(kwargs_str)s\' -p %(param_fp)s -r" % \
                    {'script': os.path.join(os.getcwd(), 'align_sequential.py'),
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
