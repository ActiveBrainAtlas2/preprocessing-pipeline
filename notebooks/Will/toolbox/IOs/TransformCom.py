from bdb import Breakpoint
import sys
import numpy as np
sys.path.append('/home/zhw272/programming/pipeline_utility/')
from notebooks.Will.toolbox.rough_alignment.apply_affine_transform import transform_dict_affine
from notebooks.Will.toolbox.rough_alignment.apply_demons_transform import transform_dict_demons
from notebooks.Will.toolbox.IOs.get_calculated_transforms import get_affine_transform,get_demons_transform
from utilities.alignment.align_point_sets import get_rigid_transformation_from_dicts,apply_rigid_transformation_to_com_dict
from notebooks.Will.toolbox.IOs.get_bilis_json_file import get_tranformation
from utilities.alignment.align_point_sets import apply_rigid_transformation_to_com_dict_list
class TransformCom:
    def __init__(self,load_com_class):
        self.getcom = load_com_class

    def get_DK52_rigid_transformation(self):
        DK52_com = self.getcom.get_dk52_com()
        atlas_com = self.getcom.get_atlas_com()
        rigid_transformation = get_rigid_transformation_from_dicts(DK52_com,atlas_com)
        return rigid_transformation

    def get_itk_affine_transformed_coms(self):
        prep_list = self.getcom.get_prep_list_for_rough_alignment_test()
        transformed_com_list = []
        for prepi in prep_list:
            affine_transform = get_affine_transform(prepi)
            prepicom = self.getcom.get_corrected_prepi_com(prepi)
            transformed_com = transform_dict_affine(affine_transform,prepicom)
            transformed_com_list.append(transformed_com)
        return transformed_com_list

    def get_itk_demons_transformed_coms(self):
        prep_list = self.getcom.get_prep_list_for_rough_alignment_test()
        transformed_com_list = []
        for prepi in prep_list:
            print('loading demons '+prepi)
            demons_transform = get_demons_transform(prepi)
            prepicom = self.getcom.get_corrected_prepi_com(prepi)
            transformed_com = transform_dict_demons(demons_transform,prepicom)
            transformed_com_list.append(transformed_com)
        return transformed_com_list

    def get_airlab_transformed_coms(self):
        prep_list = self.getcom.get_prep_list_for_rough_alignment_test()
        transformed_com_list = []
        for prepi in prep_list:
            affine_transform = get_tranformation(prepi)
            prepicom = self.getcom.get_corrected_prepi_com(prepi)
            transformed_com = self.apply_airlab_transformation_to_com_dict(prepicom,affine_transform)
            transformed_com_list.append(transformed_com)
        return transformed_com_list
    
    def apply_airlab_transformation_to_com_dict(self,com_dict,transform,imaging_resolution = np.array([0.325,0.325,20])):
        for landmark,com in com_dict.items():
            com = np.array(com, dtype=float)/imaging_resolution
            com_dict[landmark] = transform.forward_point(com)*imaging_resolution
        return com_dict

    def get_beth_coms_aligned_to_atlas(self):
        prep_list = self.getcom.get_prep_list_for_rough_alignment_test()
        prep_list.append('DK52')
        transformed_com_list = []
        atlas_com = self.getcom.get_atlas_com()
        for prepi in prep_list:
            prepicom = self.getcom.get_corrected_prepi_com(prepi)
            rigid_transformation = get_rigid_transformation_from_dicts(prepicom,atlas_com)
            transformed_com = apply_rigid_transformation_to_com_dict(prepicom,rigid_transformation)
            transformed_com_list.append(transformed_com)
        return transformed_com_list

    def apply_dk52_to_atlas_rigid_transform_to_com_dict_list(self,com_dict_list):
        rigid_transformation = self.get_DK52_rigid_transformation()
        rigid_transformed_coms = apply_rigid_transformation_to_com_dict_list(com_dict_list,rigid_transformation)
        return rigid_transformed_coms