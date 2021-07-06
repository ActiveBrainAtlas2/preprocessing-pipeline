#%%
import sys
sys.path.append('/home/zhw272/programming/pipeline_utility/')
from notebooks.Will.toolbox.IOs.pickle_io import save_pickle,load_pickle
from notebooks.Will.affine_assessment_brain_to_atlas import get_deviation_from_atlas_com
from notebooks.Will.toolbox.rough_alignment.diagnostics import get_atlas_com,get_reference_com
from notebooks.Will.toolbox.plotting.plot_com_offset import plot_offsets_scatter,save_offsets_scatter
#%%
com_diff = get_deviation_from_atlas_com()
# %%
save_pickle(com_diff,file_name='brain_to_atlas_diff',folder='affine_com_diff')
#%%
com_diff = load_pickle(file_name='brain_to_atlas_diff',folder='affine_com_diff')
# %%
plot_offsets(com_diff)
# %%
save_offsets(com_diff,file_name='com_diff_scatter_affine',folder='affine_diagnostics_brain_to_atlas',title='demons_brain_to_atlas')
# %%
