#%%
import sys
sys.path.append('/home/zhw272/programming/pipeline_utility/')
from notebooks.Will.toolbox.IOs.pickle_io import save_pickle,load_pickle
from notebooks.Will.demons_assessment_brain_to_atlas import get_deviation_from_atlas_com 
get_demons_com_offset = get_deviation_from_atlas_com
from notebooks.Will.affine_assessment_brain_to_atlas import get_deviation_from_atlas_com
get_affine_com_offset = get_deviation_from_atlas_com
from notebooks.Will.toolbox.plotting.plot_com_offset import plot_offset_box
from notebooks.Will.toolbox.IOs.save_figures_to_pdf import save_figures_to_pdf
#%% run if no save files present
demons_com_offset1 = get_demons_com_offset()
affine_com_offset1 = get_affine_com_offset()

#%%
demons_com_offset = load_pickle(file_name='brain_to_atlas_diff',folder='demons_com_diff')
affine_com_offset = load_pickle(file_name='brain_to_atlas_diff',folder='affine_com_diff')

# %%
fig_demons = plot_offset_box(demons_com_offset,title='rough alignment demons')
fig_affine = plot_offset_box(affine_com_offset,title='rough alignment affine')

# %%
save_figures_to_pdf([fig_demons,fig_affine],'rough_alignment_comparison','demons_vs_affine')
# %%
