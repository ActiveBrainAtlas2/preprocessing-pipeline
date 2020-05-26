"""
was formerly warp_crop.py
"""
import argparse
import sys
import os
import subprocess
import numpy as np

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.file_location import FileLocationManager



parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description="""A versatile warp/crop script. 
Usage 1: warp_crop.py --input_spec in.ini --op_id align1crop1
This is the high-level usage. The operations are defined as ini files in the operation_configs/ folder.

Usage 2: warp_crop.py --input_fp in.tif --output_fp out.tif --op warp 0.99,0,0,0,1.1,0 --op crop 100,100,20,10
This is the low-level usage. Note that the user must ensure the warp parameters and crop coordinates are consistent with the resolution of the input image.
"""
)

#parser.add_argument("--stack", type=str)
parser.add_argument("--op", action='append', nargs=2)
parser.add_argument("--input_fp", type=str, help="input filepath")
parser.add_argument("--output_fp", type=str, help="output filepath")
parser.add_argument("--njobs", type=int, help="Number of parallel jobs", default=1)

args = parser.parse_args()

input_fp = args.input_fp
output_fp = args.output_fp

print('input fp is ', input_fp)
print('input fp is ', output_fp)
