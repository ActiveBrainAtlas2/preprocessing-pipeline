#%%
import sys
sys.path.append('/home/zhw272/programming/pipeline_utility')
from notebooks.Will.demons_assessment_brain_to_atlas import get_DK52_com_aligned_to_prepi,get_demons_transform
#%%
prepi = 'DK39'
coms = get_DK52_com_aligned_to_prepi(prepi)
# %%
demons_transform = get_demons_transform(prepi)
# %%
print(demons_transform)
# %%
import numpy as np
origin = np.array([31.2,26,40])+np.array([1,1,1])
demons_transform.TransformPoint(origin)
# %%
point = origin + np.array([1,1,1])
transformed_point = demons_transform.TransformPoint(point)
print(transformed_point-point)
# %%
point = origin + np.array([0.5,0.5,0.5])
transformed_point = demons_transform.TransformPoint(point)
print(transformed_point-point)
# %%
