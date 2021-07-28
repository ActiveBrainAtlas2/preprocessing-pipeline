import sys
sys.path.append('/home/zhw272/programming/pipeline_utility')
sys.path.append('/home/zhw272/programming/pipeline_utility/src')
from notebooks.Will.toolbox.IOs.LoadComDatabase import LoadComDatabase
from notebooks.Will.toolbox.IOs.TransformCom import TransformCom,get_affine_transform
from notebooks.Will.toolbox.plotting.ComBoxPlot import ComBoxPlot
from notebooks.Will.toolbox.IOs.get_landmark_lists import get_all_landmarks_in_specimens
import numpy as np

getcom = LoadComDatabase()
tc = TransformCom(getcom)
boxplot = ComBoxPlot(getcom.get_prep_list,get_all_landmarks_in_specimens)
beth = getcom.get_corrected_prep_coms()
itk_ra = tc.get_itk_rough_alignment()
airlab_ra = tc.get_airlab_rough_alignment()

boxplot.plot_offset_between_two_com_sets(beth,itk_ra,'beth vs itk')
boxplot.plot_offset_between_two_com_sets(beth,airlab_ra,'beth vs airlab')

# def apply_at_to_np_array(array,at):
#     t_array = np.ones(array.shape)

# def get_value_from_offset_table(offset_table,prepi,type,structure):
#     to_include = np.logical_and(offset_table.brain == prepi,offset_table.structure == structure)
#     to_include = np.logical_and(to_include , offset_table.type == type )
#     return(float(offset_table[to_include].value))

# def get_dist(array):
#     nrow = array.shape[0]
#     dist = []
#     for rowi in range(nrow):
#         dist.append(np.sqrt(np.sum(np.square(array[rowi]))))
#     return np.array(dist)

# DKxx_to_DK52 = tc.get_itk_affine_transformed_coms()
# dk52 = getcom.get_dk52_com()
# offset_table_52_to_xx = boxplot._get_offset_table_from_two_com_sets(beth,itk_ra)
# offset_table_xx_to_52 = boxplot._get_offset_table_from_coms_to_a_reference(DKxx_to_DK52,dk52)
# #for DK39
# prepi = 'DK39'
# prepi_xx_to_52 = offset_table_xx_to_52[np.logical_and(offset_table_xx_to_52.brain == prepi,offset_table_xx_to_52.type == 'dist')]
# prepi_52_to_xx = offset_table_52_to_xx[np.logical_and(offset_table_52_to_xx.brain == prepi,offset_table_52_to_xx.type == 'dist')]
# vxx_to_52_str = set(prepi_xx_to_52.structure.to_list())
# v52_to_xx_str = set(prepi_52_to_xx.structure.to_list())
# common_str =list(vxx_to_52_str & v52_to_xx_str)
# nstr = len(common_str)
# diff_xx_to_52 = np.zeros([nstr,3])
# diff_52_to_xx = np.zeros([nstr,3])
# types = ['dx','dy','dz']
# for sti in range(nstr):
#     structure = common_str[sti]
#     for ti in range(3):
#         typei = types[ti]
#         diff_52_to_xx[sti,ti] = get_value_from_offset_table(offset_table_52_to_xx,prepi,typei,structure)
#         diff_xx_to_52[sti,ti] = get_value_from_offset_table(offset_table_xx_to_52,prepi,typei,structure)

# at_xx_to_52 = get_affine_transform(prepi)
# at_52_to_xx = at_xx_to_52.GetInverse()


# tf_52_to_xx = np.array([at_52_to_xx.TransformPoint(diff_xx_to_52[rowi]) for rowi in range(diff_xx_to_52.shape[0])])
# tf_dist_52_to_xx = get_dist(tf_52_to_xx)
# dist_52_to_xx = get_dist(diff_52_to_xx)

# structure = common_str[0]
# get_value_from_offset_table(offset_table_52_to_xx,prepi,'dx',structure)

