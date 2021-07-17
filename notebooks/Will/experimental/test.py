import sys
sys.path.append('/home/zhw272/programming/pipeline_utility')
import os
from src.lib.comparison_tools import compare_lists
import numpy as np
# flist1 = os.listdir('/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK63/preps/CH1/full/')
# flist2 = os.listdir('/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK63/preps/CH1/full_aligned/')
# compare_lists(flist1,flist2)

def get_image_size(filepath):
    result_parts = str(check_output(["identify", filepath]))
    results = result_parts.split()
    width, height = results[2].split('x')
    return width, height

from subprocess import Popen, run, check_output
root = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK63/preps/CH2/full_cleaned/'
flist = os.listdir(root)
print(len(flist))
w = []
h = []
for file in flist:
    filepath = root + file
    width, height = get_image_size(filepath)
    w.append(int(width))
    h.append(int(height))
np.where(np.array(w)!=54500)[0]
np.where(np.array(h)!=35500)[0]

print()
    # check_output(["identify", filepath])