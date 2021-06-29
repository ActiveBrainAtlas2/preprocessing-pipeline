#%%
import sys
sys.path.append('/home/zhw272/programming/pipeline_utility')
from notebooks.Will.toolbox.rough_alignment.diagnostics import *
from notebooks.Will.toolbox.rough_alignment.apply_affine_transform import transform_point_affine
from notebooks.Will.toolbox.IOs.get_calculated_transforms import get_affine_transform
from notebooks.Will.toolbox.plotting.plot_coms import compare_two_coms,compare_multiple_coms
from notebooks.Will.toolbox.IOs.get_calculated_transforms import get_affine_transform
from notebooks.Will.toolbox.rough_alignment.sitk.utility import *
from notebooks.Will.toolbox.IOs.get_transfromed_com import get_transformed_prepi_com,get_transformed_com_dict
import matplotlib.pyplot as plt
import numpy as np
from notebooks.Will.toolbox.com_dict_tools import get_shared_coms
#%%
DK52_com = get_reference_com('DK52')
prepi = 'DK39'
prepi_com = get_reference_com(prepi)
print('loading demons transformation for prep: '+prepi)
affine_transform = get_affine_transform(prepi)
DK52_com_aligned =  transform_point_affine(affine_transform,DK52_com)
#%%
stact_to_physical = [0.325,0.325,20]
billi_dk52 = get_transformed_prepi_com(prepi)@np.diag(stact_to_physical)
#%%
billi_dk52_dict = get_transformed_com_dict(prepi)
prepi_dict = get_manual_annotation_from_beth(prepi)
#%%
bili_dk52_shared,prepi_shared,_ = get_shared_coms(billi_dk52_dict,prepi_dict)
stact_to_physical = [0.325,0.325,20]
bili_dk52_shared = bili_dk52_shared@np.diag(stact_to_physical)
#%%
name1 = 'DK52 transformed bili'
com1 = bili_dk52_shared

name2 = prepi
com2 = prepi_shared

compare_two_coms(com1,com2,[name1,name2])
#%%
name1 = 'DK52'
com1 = DK52_com

name2 = prepi
com2 = prepi_shared

compare_two_coms(com1,com2,[name1,name2])
#%%
com_list= [DK52_com_aligned,DK52_com,prepi_com]
brain_list = ['DK52_transformed','DK52',prepi]
compare_multiple_coms(com_list,brain_list)
#%%
compare_multiple_coms([billi_dk52],['DK52 transformed bili'])

# %%
