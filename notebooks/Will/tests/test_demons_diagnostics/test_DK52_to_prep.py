#%%
import sys
sys.path.append('/home/zhw272/programming/pipeline_utility/')
from notebooks.Will.demons_assessment_brain_to_atlas import *
from notebooks.Will.toolbox.IOs.get_stack_image_sitk import *
#%%
prep_list = get_prep_list_for_rough_alignment_test()
prepi = prep_list[0]
prepi
#%%

DK52_aligned = get_DK52_com_aligned_to_prepi(prepi)
DK52_com = get_reference_com('DK52')
#%%
DK52_stack = load_stack_from_prepi("DK52")
prepi_stack = load_stack_from_prepi(prepi)
# %%
import matplotlib.pyplot as plt
from notebooks.Will.toolbox.IOs.get_path import get_subpath_to_tif_files
import os

def load_image(prepi,z=0):
    tiff_path = get_subpath_to_tif_files(prepi)
    list_of_tiffs = os.listdir(tiff_path)
    list_of_tiffs = sorted(list_of_tiffs)
    return plt.imread(tiff_path/list_of_tiffs[z])

# %%
section = load_image('DK52',200)
plt.imshow(section)
# %%
prepi = 'DK52'
tiff_path = get_subpath_to_tif_files(prepi)
list_of_tiffs = os.listdir(tiff_path)
list_of_tiffs = sorted(list_of_tiffs)
list_of_tiffs
# %%
from notebooks.Will.toolbox.IOs.get_stack_image_np import *
get_nsections('DK52')

# %%
