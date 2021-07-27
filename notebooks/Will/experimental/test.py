import sys
sys.path.append('/home/zhw272/programming/pipeline_utility')
sys.path.append('/home/zhw272/programming/pipeline_utility/src')
from notebooks.Will.toolbox.IOs.LoadComDatabase import LoadComDatabase
from notebooks.Will.toolbox.IOs.TransformCom import TransformCom
from notebooks.Will.toolbox.plotting.ComBoxPlot import ComBoxPlot
from notebooks.Will.toolbox.IOs.get_landmark_lists import get_all_landmarks_in_specimens
getcom = LoadComDatabase()
tc = TransformCom(getcom)
boxplot = ComBoxPlot(getcom.get_prep_list,get_all_landmarks_in_specimens)
beth = getcom.get_corrected_prep_coms()
itk_ra = tc.get_itk_rough_alignment()
airlab_ra = tc.get_airlab_rough_alignment()
# boxplot.plot_offset_between_two_com_sets(beth,itk_ra,'beth vs itk')
# boxplot.plot_offset_between_two_com_sets(beth,airlab_ra,'beth vs airlab')
