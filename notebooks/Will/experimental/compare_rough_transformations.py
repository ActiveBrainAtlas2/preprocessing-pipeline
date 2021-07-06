import sys
import numpy as np
sys.path.append('/home/zhw272/programming/pipeline_utility')
from notebooks.Will.toolbox.rough_alignment.apply_affine_transform import transform_point_affine
from notebooks.Will.toolbox.rough_alignment.apply_demons_transform import transform_point_demons
from notebooks.Will.toolbox.IOs.get_calculated_transforms import get_affine_transform,get_demons_transform
from notebooks.Will.toolbox.IOs.get_bilis_json_file import *
from notebooks.Will.toolbox.plotting.plot_com_offset import *
from notebooks.Will.toolbox.plotting.plot_coms import *
from notebooks.Will.experimental.get_coms_from_pickle import *
from notebooks.Will.toolbox.IOs.get_landmark_lists import get_all_landmarks_in_specimens
from notebooks.Will.toolbox.IOs.get_bilis_coms import *
from utilities.alignment.align_point_sets import get_and_apply_transform
from matplotlib.backends.backend_pdf import PdfPages
import os
import pickle

def get_kui_transformed():
    prep_list = get_prep_list_for_rough_alignment_test()
    kui_transformed_com = []
    for prepi in prep_list:
        kui_transformed_com.append(get_transformed_com_dict(prepi))
    return kui_transformed_com

if __name__ == '__main__':
    atlas_com_dict = get_atlas_com()
    dk52_com = get_dk52_com()
    prep_coms = get_prep_coms()
    affine_transformed_coms_itk,affine_aligned_coms_itk = get_itk_affine_transformed_coms()
    # demons_transformed_coms_itk,demons_aligned_coms_itk = get_itk_demons_transformed_coms()
    transformed_coms_airlab,aligned_coms_airlab = get_airlab_transformed_coms()
    # kui_airlab_aligned_coms = get_kui_airlab()
    # kui_transformed_com = get_kui_transformed()
    atlas_prep_list = ['Atlas' for _ in range(5)]
    dk52_prep_list = ["DK52" for _ in range(5)]
    figs = []
    prep_list = get_prep_list_for_rough_alignment_test()
    # compare_two_com_dict(dk52_com,prep_coms[0],['DK52' , 'DK39'])
    # compare_two_com_dict(kui_transformed_com[0],prep_coms[0],['DK52 kui airlab' , 'DK39'])
    # compare_two_com_dict(transformed_coms_airlab[0],prep_coms[0],['DK52 beth airlab' , 'DK39'])
    # compare_two_com_dict(affine_transformed_coms_itk[0],prep_coms[0],['DK52 kui airlab' , 'DK39'])

    print('plotting DK52 annotation against atlas')
    fig = get_fig_two_com_dict(dk52_com,atlas_com_dict,['DK52' , 'Atlas'])
    figs.append(ploty_to_matplot(fig))
    print('plotting DK52 to annotation before image to image alignment')
    figs.append(get_fig_offset_from_coms_to_a_reference(prep_coms,dk52_com,
                            get_prep_list_for_rough_alignment_test,get_all_landmarks_in_specimens,
                            'DK52 to brain preps before alignment'))
    fig = get_fig_corresponding_coms_in_dict_to_reference(prep_coms,dk52_com,prep_list,dk52_prep_list)
    figs.append(ploty_to_matplot(fig))
    print('plotting DK52 after affine transform from itk')
    figs.append(get_fig_offset_between_two_com_sets(prep_coms,affine_transformed_coms_itk,
                                get_prep_list_for_rough_alignment_test,get_all_landmarks_in_specimens,
                                'DK52 to brain preps after affine transformation from Sitk'))
    prep_list_itk_transformed = ['itk affine transformed ' + prepi for prepi in prep_list]
    fig = get_fig_corresponding_coms_in_two_dicts(prep_coms,affine_transformed_coms_itk,prep_list,prep_list_itk_transformed)
    figs.append(ploty_to_matplot(fig))
    print('plotting DK52 after Demons transform from itk')
    figs.append(get_fig_offset_between_two_com_sets(prep_coms,demons_transformed_coms_itk,
                                get_prep_list_for_rough_alignment_test,get_all_landmarks_in_specimens,
                                'DK52 to brain preps after demons transformation from Sitk'))
    prep_list_itk_transformed = ['itk demons transformed ' + prepi for prepi in prep_list]
    fig = get_fig_corresponding_coms_in_two_dicts(prep_coms,demons_transformed_coms_itk,prep_list,prep_list_itk_transformed)
    figs.append(ploty_to_matplot(fig))
    print('plotting DK52 after affine transform from airlab')
    figs.append(get_fig_offset_between_two_com_sets(prep_coms,transformed_coms_airlab,
                                get_prep_list_for_rough_alignment_test,get_all_landmarks_in_specimens,
                                'DK52 to brain preps after transformation from Airlab'))
    prep_list_airlab_transformed = ['airlab transformed ' + prepi for prepi in prep_list]
    fig = get_fig_corresponding_coms_in_two_dicts(prep_coms,transformed_coms_airlab,prep_list,prep_list_airlab_transformed)
    figs.append(ploty_to_matplot(fig))
    print('plotting DK52 after rigid transform from itk')
    figs.append(get_fig_offset_from_coms_to_a_reference(affine_aligned_coms_itk,atlas_com_dict,
                                get_prep_list_for_rough_alignment_test,get_all_landmarks_in_specimens,
                                'Atlas to brain preps after Sitk after rigid alignment'))

    prep_list_itk_aligned = ['itk aligned ' + prepi for prepi in prep_list]
    fig = get_fig_corresponding_coms_in_dict_to_reference(affine_aligned_coms_itk,atlas_com_dict,prep_list,atlas_prep_list)
    figs.append(ploty_to_matplot(fig))
    print('plotting DK52 after rigid transform from airlab')
    figs.append(get_fig_offset_from_coms_to_a_reference(aligned_coms_airlab,atlas_com_dict,
                                get_prep_list_for_rough_alignment_test,get_all_landmarks_in_specimens,
                                'Atlas to brain preps after Airlab after rigid alignment'))
    prep_list_airlab_aligned = ['airlab aligned ' + prepi for prepi in prep_list]
    fig = get_fig_corresponding_coms_in_dict_to_reference(aligned_coms_airlab,atlas_com_dict,prep_list,atlas_prep_list)
    figs.append(ploty_to_matplot(fig))
    print('plotting kui dk52 com after rigid transform from itk')
    figs.append(get_fig_offset_from_coms_to_a_reference(kui_airlab_aligned_coms,atlas_com_dict,
                                get_prep_list_for_rough_alignment_test,get_all_landmarks_in_specimens,
                                'Atlas to Kui com after Airlab after rigid alignment'))
    prep_list_Kui_airlab_aligned = ['Kui airlab aligned ' + prepi for prepi in prep_list]
    fig = get_fig_corresponding_coms_in_dict_to_reference(kui_airlab_aligned_coms[:4],atlas_com_dict,prep_list[:4],atlas_prep_list[:4])
    figs.append(ploty_to_matplot(fig))
    
    save_path = '/home/zhw272/plots/affine_rough_alignment_comparison/'
    if not os.path.exists(save_path):
        os.mkdir(save_path)

    figi = 0
    with PdfPages(save_path+'affine_comparison.pdf') as pdf:
        for fig in figs:
            print(figi)
            pdf.savefig(fig)
            figi+=1