import sys
sys.path.append('/home/zhw272/programming/pipeline_utility/src')
sys.path.append('/home/zhw272/programming/pipeline_utility/')
from toolbox.IOs.LoadComPickle import LoadComPickle
from toolbox.IOs.LoadComDatabase import LoadComDatabase
from toolbox.plotting.ComBoxPlot import ComBoxPlot
from toolbox.IOs.TransformCom import TransformCom
from toolbox.IOs.get_landmark_lists import get_all_landmarks_in_specimens

# getcom = LoadComPickle()
getcom = LoadComDatabase()
gettc = TransformCom(getcom)
prep_coms = getcom.get_prep_coms()
DK52_coms = getcom.get_dk52_com()
atlas_coms = getcom.get_atlas_com()
itk_affine_transformed_coms = gettc.get_itk_affine_transformed_coms()
# itk_deomons_transformed_coms = gettc.get_itk_demons_transformed_coms()
itk_affine_rigid_transformed_coms = gettc.apply_dk52_to_atlas_rigid_transform_to_com_dict_list(itk_affine_transformed_coms)
# itk_deomons_rigid_transformed_coms = gettc.apply_dk52_to_atlas_rigid_transform_to_com_dict_list(itk_deomons_transformed_coms)
beth_aligned_coms = gettc.get_beth_coms_aligned_to_atlas()

boxplot = ComBoxPlot(getcom.get_prep_list,get_all_landmarks_in_specimens)
#first two plots uses a list of brains containing DK52
# boxplot.get_fig_offset_from_coms_to_a_reference(prep_coms,DK52_coms,title = 'difference between DKXX coms to DK52')
#DK52 is not used in image to image alignment analysis
boxplot.prep_list_function = lambda:['DK39', 'DK41', 'DK43', 'DK54', 'DK55']
# boxplot.plot_offset_from_coms_to_a_reference(beth_aligned_coms,atlas_coms,'Beth Aligned to Atlas')

# boxplot.postfix = '123'
# boxplot.column_types = ['dx','dy','dz']
# comlists = {' itk:Demons':itk_deomons_rigid_transformed_coms,' itk:affine':itk_affine_rigid_transformed_coms,' Beth':beth_aligned_coms}
# boxplot.get_fig_two_com_dict_list_against_reference(comlists,atlas_coms,'Roungh Alignment Comparison')

# boxplot.get_fig_offset_from_coms_to_a_reference(beth_aligned_coms,atlas_coms,'Beth Aligned to Atlas')
boxplot.get_fig_offset_from_coms_to_a_reference(itk_affine_transformed_coms,DK52_coms,title = 'difference between itk affine transformed DKXX coms to DK52')
# boxplot.get_fig_offset_from_coms_to_a_reference(itk_affine_rigid_transformed_coms,atlas_coms,
# title = 'difference between itk affine transformed DKXX coms to Atlias after rigid alignment')

#---run the following to add boxplots from demons transform (slow)---
# itk_demons_transformed_coms = gettc.get_itk_demons_transformed_coms(getcom.get_corrected_prepi_com)
# itk_demons_transformed_coms_copy = copy.deepcopy(itk_demons_transformed_coms)
# itk_demons_rigid_transformed_coms = [apply_rigid_transformation_to_com_dict(com,rigid_transformation) for com in itk_demons_transformed_coms_copy]
# boxplot.get_fig_offset_from_coms_to_a_reference(itk_demons_transformed_coms,DK52_coms,
#     title = 'difference between itk demons transformed DKXX coms to DK52')
# boxplot.get_fig_offset_from_coms_to_a_reference(itk_demons_rigid_transformed_coms,atlas_coms,
#     title = 'difference between itk demons transformed DKXX coms to Atlias after rigid alignment')

boxplot.save_pdf(file_name = '7.27db')
