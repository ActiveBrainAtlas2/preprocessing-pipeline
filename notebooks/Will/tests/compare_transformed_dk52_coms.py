#%%
import sys
import numpy as np
sys.path.append('/home/zhw272/programming/pipeline_utility')
from notebooks.Will.toolbox.rough_alignment.apply_affine_transform import transform_point_affine
from notebooks.Will.toolbox.IOs.get_calculated_transforms import get_affine_transform
from notebooks.Will.toolbox.IOs.get_bilis_json_file import *
from utilities.brain_specimens.get_com import *
from notebooks.Will.toolbox.plotting.plot_com_offset import *
from notebooks.Will.toolbox.IOs.pickle_io import load_pickle
from notebooks.Will.toolbox.IOs.get_landmark_lists import get_all_landmarks_in_specimens
from notebooks.Will.toolbox.brain_lists import get_prep_list_for_rough_alignment_test
from notebooks.Will.toolbox.IOs.get_bilis_coms import *
#%%
DK52_com = get_com_dict(prep_id = 'DK52',person_id = 2,input_type_id=1)
prepi = 'DK39'
prepi_com = get_com_dict(prep_id = prepi,person_id = 2,input_type_id=2)
affine_transform = get_affine_transform(prepi)
DK52_com_aligned =  transform_point_affine(affine_transform,np.array(list(DK52_com.values())))
kui_dk52_dict_physical = get_kui_dk52_com_dict_physical()
transformed_kui_52_39 = get_transformed_com_dict(prepi)
affine_com_offset = load_pickle(file_name='brain_to_atlas_diff',folder='affine_com_diff')
atlas_centers = get_atlas_centers()
bili_aligned_com = get_brain_coms( person_id = 1, input_type_id = 4)
#%%
fig = []
fig.append(plot_offset_between_two_com_sets(DK52_com,prepi_com,
                            get_prep_list_for_rough_alignment_test,get_all_landmarks_in_specimens,
                            'Beth annotation DK52 to DK39 offset'))

fig.append(plot_offset_between_two_com_sets(kui_dk52_dict_physical,prepi_com,
                            get_prep_list_for_rough_alignment_test,get_all_landmarks_in_specimens,
                            'Kui DK52 to Beth DK39 offset'))

fig.append(plot_offset_between_two_com_sets(DK52_com_aligned,prepi_com,
                            get_prep_list_for_rough_alignment_test,get_all_landmarks_in_specimens,
                            'Beth annotation transformed DK52 DK39 offset'))

fig.append(plot_offset_between_two_com_sets(transformed_kui_52_39,prepi_com,
                            get_prep_list_for_rough_alignment_test,get_all_landmarks_in_specimens,
                            'Kui DK52 transformed to Beth DK39 offset'))

fig.append(plot_offset_from_coms_to_a_reference(affine_com_offset,atlas_centers,
                            get_prep_list_for_rough_alignment_test,get_all_landmarks_in_specimens,
                            'Kui DK52 transformed to Beth DK39 offset'))

fig.append(plot_offset_from_coms_to_a_reference(bili_aligned_com,atlas_centers,
                            get_bili_prep_list,get_bili_structure_list,
                            'Kui DK52 transformed and aligned to atlas to atlas offset'))