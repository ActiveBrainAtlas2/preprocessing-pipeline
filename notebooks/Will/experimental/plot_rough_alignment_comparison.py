import notebooks.Will.experimental.get_coms_from_pickle as getcom
import notebooks.Will.toolbox.plotting.plot_com_offset as offsetplotter
import notebooks.Will.toolbox.plotting.plot_coms as complotter
from notebooks.Will.toolbox.IOs.get_landmark_lists import get_all_landmarks_in_specimens
from notebooks.Will.toolbox.IOs.save_figures_to_pdf import save_figures_to_pdf
import notebooks.Will.experimental.get_transformed_coms as gettc
import copy

prep_coms = getcom.get_prep_coms()
DK52_coms = getcom.get_dk52_com()
atlas_coms = getcom.get_atlas_com()
itk_affine_transformed_coms = gettc.get_itk_affine_transformed_coms()
rigid_transformation = gettc.get_DK52_rigid_transformation()
itk_demons_transformed_coms = gettc.get_itk_demons_transformed_coms()
itk_affine_transformed_coms_copy = copy.deepcopy(itk_affine_transformed_coms)
itk_demons_transformed_coms_copy = copy.deepcopy(itk_demons_transformed_coms)
itk_affine_rigid_transformed_coms = [gettc.apply_rigid_transformation_to_com_dict(com,rigid_transformation) for com in itk_affine_transformed_coms_copy]
itk_demons_rigid_transformed_coms = [gettc.apply_rigid_transformation_to_com_dict(com,rigid_transformation) for com in itk_demons_transformed_coms_copy]
prep_list_function = getcom.get_prep_list_for_rough_alignment_test
landmark_list_function = get_all_landmarks_in_specimens
figs = []
fig1 = offsetplotter.get_fig_offset_from_coms_to_a_reference(prep_coms,DK52_coms,
    prep_list_function = prep_list_function,
    landmark_list_function = landmark_list_function,
    title = 'difference between DKXX coms to DK52')
figs.append(fig1)
fig2 = offsetplotter.get_fig_offset_from_coms_to_a_reference(itk_affine_transformed_coms,DK52_coms,
    prep_list_function = prep_list_function,
    landmark_list_function = landmark_list_function,
    title = 'difference between itk affine transformed DKXX coms to DK52')
figs.append(fig2)
fig3 = offsetplotter.get_fig_offset_from_coms_to_a_reference(itk_demons_transformed_coms,DK52_coms,
    prep_list_function = prep_list_function,
    landmark_list_function = landmark_list_function,
    title = 'difference between itk demons transformed DKXX coms to DK52')
figs.append(fig3)
fig4 = offsetplotter.get_fig_offset_from_coms_to_a_reference(itk_affine_rigid_transformed_coms,atlas_coms,
    prep_list_function = prep_list_function,
    landmark_list_function = landmark_list_function,
    title = 'difference between itk affine transformed DKXX coms to Atlias after rigid alignment')
figs.append(fig4)
fig5 = offsetplotter.get_fig_offset_from_coms_to_a_reference(itk_demons_rigid_transformed_coms,atlas_coms,
    prep_list_function = prep_list_function,
    landmark_list_function = landmark_list_function,
    title = 'difference between itk demons transformed DKXX coms to Atlias after rigid alignment')
figs.append(fig5)
save_figures_to_pdf(figs,'rough alignment Diagnostics','')
