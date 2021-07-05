#%%
import sys
sys.path.append('/home/zhw272/programming/pipeline_utility/')
from notebooks.Will.demons_asscessment_atlast_to_brain import *
from notebooks.Will.toolbox.plotting.plot_coms import compare_two_coms,reshape_com
#%%
DK52_com = get_reference_com('DK52')
#%%
atlas_com = get_atlas_com()
rotation,translation = align_point_sets(atlas_com.T,DK52_com.T)
transformed_atlas_coms = []
for com in atlas_com:
    transformed_atlas_coms.append(rotation@com.reshape(3) + translation.reshape(3))
transformed_atlas_coms = np.array(transformed_atlas_coms)
#%%
transformed_atlas_coms = get_atlas_com_aligned_to_DK52()
# %%
compare_two_coms(transformed_atlas_coms,DK52_com,('Transformed','DK52'))
# %%
compare_two_coms(atlas_com,DK52_com,('Atlas','DK52'))
# %%
def print_two_coms(com1,com2):
    com1 = reshape_com(com1)
    com2 = reshape_com(com2)
    assert com1.shape[0] == com2.shape[0]
    npoints = com1.shape[0]
    for pointi in range(npoints):
        print(com1[pointi],com2[pointi])
