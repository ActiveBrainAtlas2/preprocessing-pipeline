#%%
import sys
sys.path.append('/home/zhw272/programming/pipeline_utility/')
import plotly.express as px
from notebooks.Will.demons_asscessment_atlas_to_brain import get_demons_diagonastics,prepare_table_for_plot,get_reference_com
import pickle
import numpy as np
import plotly.graph_objects as go
from notebooks.Will.toolbox.plotting.plot_coms import compare_two_coms
# %%
reference_coms,transformed_coms,atlas_com_aligned_to_DK52 = get_demons_diagonastics()
#%%
results = { 'reference_coms':reference_coms,
            'transformed_coms':transformed_coms,
            'atlas_com_aligned_to_DK52':atlas_com_aligned_to_DK52}
pickle.dump((results),open('/home/zhw272/data/demons_diag.p','wb'))
#%%
results = pickle.load(open('/home/zhw272/data/demons_diag.p','rb'))
reference_coms,transformed_coms,atlas_com_aligned_to_DK52 =results.values()
#%%
DK52_com = get_reference_com('DK52')
#%%
transformation_displacement = []
affine_to_manual = []
demons_to_manual = []
improvement = []
for prepi in range(5):
    transformation_displacement.append(transformed_coms[prepi] - atlas_com_aligned_to_DK52)
    affine_to_manual.append(atlas_com_aligned_to_DK52 - reference_coms[prepi])
    demons_to_manual.append(transformed_coms[prepi]- reference_coms[prepi])
    improvement.append(np.abs(affine_to_manual[-1])-np.abs(demons_to_manual[-1]))
#%%
df_displacement = prepare_table_for_plot(transformation_displacement)
plot_folder = '/home/zhw272/plots/'
fig = px.scatter(df_displacement, x="structure", y="value", color="type", hover_data=['brain'])
fig.write_html(plot_folder+'demons_box_plot_displacement.html')

df_manual = prepare_table_for_plot(demons_to_manual)
plot_folder = '/home/zhw272/plots/'
fig = px.scatter(df_manual, x="structure", y="value", color="type", hover_data=['brain'])
fig.write_html(plot_folder+'demons_box_plot_deviation_from_manual.html')

df_manual = prepare_table_for_plot(affine_to_manual)
plot_folder = '/home/zhw272/plots/'
fig = px.scatter(df_manual, x="structure", y="value", color="type", hover_data=['brain'])
fig.write_html(plot_folder+'affine_box_plot_deviation_from_manual.html')

df_manual = prepare_table_for_plot(improvement)
plot_folder = '/home/zhw272/plots/'
fig = px.scatter(df_manual, x="structure", y="value", color="type", hover_data=['brain'])
fig.write_html(plot_folder+'improvement_box_plot.html')
# %%
for prepi in range(5):
    comi = reference_coms[prepi]
    transformed_comi = transformed_coms[prepi]
    fig = go.Figure(data=go.Scatter3d(x=comi[:,0], y=comi[:,1],z = comi[:,2], mode='markers'))
    fig.add_trace(go.Scatter3d(x=transformed_comi[:,0], y=transformed_comi[:,1],z = transformed_comi[:,2], mode='markers'))
    fig.show()
# %%
dk52 = get_reference_com('DK52')
#%%
fig = go.Figure(data=go.Scatter3d(x=dk52[:,0], y=dk52[:,1],z = dk52[:,2], mode='markers'))
fig.add_trace(go.Scatter3d(x=atlas_com_aligned_to_DK52[:,0], y=atlas_com_aligned_to_DK52[:,1],z = atlas_com_aligned_to_DK52[:,2], mode='markers'))
fig.show()
#%%
for prepi in range(5):
    comi = reference_coms[prepi]
    transformed_comi = transformed_coms[prepi]
    fig = go.Figure(data=go.Scatter3d(x=comi[:,0], y=comi[:,1],z = comi[:,2], mode='markers'))
    fig.add_trace(go.Scatter3d(x=atlas_com_aligned_to_DK52[:,0], y=atlas_com_aligned_to_DK52[:,1],z = atlas_com_aligned_to_DK52[:,2], mode='markers'))
    fig.show()
# %%
compare_two_coms(transformed_coms[0],reference_coms[0],('transformed_atlas','DK39'))

# %%
compare_two_coms(transformed_coms[0],reference_coms[0],('transformed_atlas','DK39'))
