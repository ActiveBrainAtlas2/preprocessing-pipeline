import argparse
import os
import subprocess
import numpy as np
import sys
import json
import time

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='')

parser.add_argument("stack", type=str, help="The name of the stack")
args = parser.parse_args()
stack = args.stack

from utilities2015 import execute_command
from metadata import ROOT_DIR
#from preprocess_utilities import *
from data_manager_v2 import DataManager
#from a_driver_utilities import *


## Downsample and normalize images in the "_raw" folder
raw_folder = DataManager.setup_get_raw_fp( stack )
for img_name in os.listdir( raw_folder ):
    input_fp = os.path.join( raw_folder, img_name)
    base = os.path.splitext(img_name)[0]
    output_fp = os.path.join( ROOT_DIR, stack, 'thumbnail', base + '.png' )
    
    # Create output directory if it doesn't exist
    try:
        os.makedirs( DataManager.setup_get_thumbnail_fp(stack) )
    except:
        pass
    # Create thumbnails
    execute_command("convert \""+input_fp+"\" -resize 3.125% -auto-level -normalize \
                    -compress lzw \""+output_fp+"\"")
