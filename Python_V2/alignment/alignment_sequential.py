import os
import sys
import re
import subprocess
import json
import argparse

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.alignment_utility import create_if_not_exists, execute_command


parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='Align consecutive images. Possible bad alignment pairs are written into a separate file.')

parser.add_argument("output_dir", type=str, help="output dir. Files for each pairwise transform are stored in sub-folder <currImageName>_to_<prevImageName>.")
parser.add_argument("kwargs_str", type=str, help="json-encoded list of dict (keyworded inputs). Each dict entry has four keys: prev_fp (previous image file path), curr_fp (current image file path).")
parser.add_argument("-p", "--param_fp", type=str, help="elastix parameter file path", default=None)

args = parser.parse_args()

output_dir = args.output_dir
kwargs_str = json.loads(args.kwargs_str)
param_fp = args.param_fp

ELASTIX_BIN = '/usr/bin/elastix'

failed_pairs = []

# every "kwarg" corresponds to a pair of images
for kwarg in kwargs_str:

    prev_img_name = kwarg['prev_img_name']
    curr_img_name = kwarg['curr_img_name']
    prev_fp = kwarg['prev_fp']
    curr_fp = kwarg['curr_fp']

    new_dir = '{}_to_{}'.format(curr_img_name, prev_img_name)
    output_subdir = os.path.join(output_dir, new_dir)

    if os.path.exists(output_subdir) and 'TransformParameters.0.txt' in os.listdir(output_subdir):
        sys.stderr.write('Result for aligning %s to %s already exists.\n' % (curr_img_name, prev_img_name))
        print('{} to {} already exists and so skipping.'.format(curr_img_name, prev_img_name))
        continue

    command = ['rm', '-rf', output_subdir]
    subprocess.run(command)
    create_if_not_exists(output_subdir)
    param_fp = os.path.join(os.getcwd(), param_fp)
    """
    command = [ELASTIX_BIN, '-f', prev_fp, '-m', curr_fp, '-p', param_fp, '-out', output_subdir]
    print(" ".join(command))
    ret = subprocess.Popen(command)
    #sys.exit()
    ret.wait()

    if ret.returncode > 0:
        failed_pairs.append((prev_img_name, curr_img_name))
    """
    ret = execute_command(
        '%(elastix_bin)s -f \"%(fixed_fp)s\" -m \"%(moving_fp)s\" -out \"%(output_subdir)s\" -p \"%(param_fp)s\"' % \
        {'elastix_bin': ELASTIX_BIN,
         'param_fp': param_fp,
         'output_subdir': output_subdir,
         'fixed_fp': prev_fp,
         'moving_fp': curr_fp
         })

    if ret == 1:
        failed_pairs.append((prev_img_name, curr_img_name))
    else:
        with open(os.path.join(output_subdir, 'elastix.log'), 'r') as f:
            t = f.read()
            g = re.search("Final metric value  = (.*?)\n", t)
            assert g is not None
            metric = float(g.groups()[0])
            sys.stderr.write("Metric = %.2f\n" % metric)

hostname = subprocess.check_output("hostname", shell=True).strip().decode('utf-8')

if len(failed_pairs) > 0:
    with open(os.path.join(output_dir, 'intra_stack_alignment_failed_pairs_%s.txt' % (hostname.split('.')[0])), 'w') as f:
        for pf, cf in failed_pairs:
            f.write(pf + ' ' + cf + '\n')

