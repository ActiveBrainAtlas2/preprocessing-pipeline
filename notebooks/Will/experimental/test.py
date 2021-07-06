import sys
sys.path.append('/home/zhw272/programming/pipeline_utility')
from notebooks.Will.experimental.get_coms_from_pickle import *
affine_transformed_coms_itk,affine_aligned_coms_itk = get_itk_affine_transformed_coms()