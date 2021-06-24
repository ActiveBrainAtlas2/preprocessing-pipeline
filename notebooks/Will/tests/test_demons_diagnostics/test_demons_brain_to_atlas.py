#%%
import sys
sys.path.append('/home/zhw272/programming/pipeline_utility/')
from notebooks.Will.toolbox.IOs.pickle_io import save_pickle,load_pickle
from notebooks.Will.demons_assessment_brain_to_atlas import get_deviation_from_atlas_com, get_transformed_coms
from notebooks.Will.toolbox.rough_alignment.diagnostics import get_atlas_com,get_reference_com
from notebooks.Will.toolbox.plotting.com_offset_box_plot import plot_offsets,save_offsets

#%%
com_diff = get_deviation_from_atlas_com()
#%%
transformed_coms = get_transformed_coms()
# %%
save_pickle(com_diff,file_name='brain_to_atlas_diff',folder='demons_com_diff')
#%%
com_diff = load_pickle(file_name='brain_to_atlas_diff',folder='demons_com_diff')

# %%
save_pickle(transformed_coms,file_name='brain_to_atlas_transformed_com',folder='demons_com_diff')

# %%
com_diff = get_deviation_from_atlas_com(transformed_coms)
# %%
plot_offsets(com_diff)
# %%
save_offsets(com_diff,file_name='com_diff_scatter_demons',folder='demons_diagnostics_brain_to_atlas',title='demons_brain_to_atlas')
# %%
