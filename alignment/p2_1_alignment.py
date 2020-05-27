"""
This was formerly align_v3.py. This is the first script in a series that is meant
to be run in python2.
"""
import os
import argparse


from old_methods import run_distributed

def setup(stack):
    elastix_output_dir = '/mnt/data/CSHL_data_processed/{}/{}_elastix_output'.format(stack, stack)
    params_fp =  'Parameters_Rigid_MutualInfo_noNumberOfSpatialSamples_4000Iters.txt'


    filepath = '/mnt/data/CSHL_data_processed/{}/cleaned'.format(stack, stack)
    image_name_list = sorted(os.listdir(filepath))
    run_distributed("python %(script)s \"%(output_dir)s\" \'%%(kwargs_str)s\' -p %(param_fp)s -r" % \
                    {'script': os.path.join(os.getcwd(), 'p2_alignment_sequential.py'),
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
