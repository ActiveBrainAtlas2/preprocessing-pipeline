import sys
sys.path.append('/home/zhw272/programming/pipeline_utility')
import os
from src.lib.comparison_tools import compare_lists
flist1 = os.listdir('/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK63/preps/CH1/full/')
flist2 = os.listdir('/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK63/preps/CH1/full_aligned/')
compare_lists(flist1,flist2)

