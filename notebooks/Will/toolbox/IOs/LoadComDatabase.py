from bdb import Breakpoint
import sys
import numpy as np
from notebooks.Will.toolbox.IOs.LoadCom import LoadCom
import os
import pickle
class LoadComPickle(LoadCom):
    def __init__(self):
        """__init__ [loads com from local save in pickles and set the coms in attributes]
        """
        save_dict = pickle.load(open(os.path.join(sys.path[0], 'com_save_7-1-2021.p'),'rb'))
        com_keys = ['atlas_com', 'beth_coms', 'beth_corrected_coms', 'bili_aligned_coms', 'bili_aligned_corrected_coms', 'kui_airlab_coms']
        for key in com_keys:
            exec("self.%s = save_dict[key]" % (key))

    def get_atlas_com(self):
        """get Atlas com diction as of June 2021"""
        atlas_com_phys = self._convert_com_dict_units(self.atlas_com,self._atlas_to_physical)
        return atlas_com_phys

    def get_prepi_com(self,prepi):
        """get beth's annotation dictionary for one brain at June 2021, the uncorrected coms are labeled inactive in a following update"""
        prepi_com = self._convert_com_dict_units(self.beth_coms[prepi],self._image_to_physical) 
        return prepi_com

    def get_corrected_prepi_com(self,prepi):
        """get beth's corrected annotation dictionary for one brain at June 2021"""
        com = self._combine_og_and_corrected_beth_annotation(self.beth_coms[prepi],self.beth_corrected_coms[prepi])
        prepi_com = self._convert_com_dict_units(com,self._image_to_physical) 
        return prepi_com

    def get_corrected_dk52_com(self):
        """get beth's corrected annotation dictionary for DK52 brain at June 2021"""
        return self.get_corrected_prepi_com('DK52')

    def get_dk52_com(self):
        """get beth's annotated com dictionary for DK52 brain at June 2021"""
        return self.get_prepi_com('DK52')

    def get_corrected_prep_coms(self):
        """get beth's corrected annotated com dictionary for a list of brains at June 2021"""
        prep_list = self.get_prep_list_for_rough_alignment_test()
        corrected_prep_coms = []
        for prepi in prep_list:
            corrected_com = self._combine_og_and_corrected_beth_annotation(self.beth_coms[prepi],self.beth_corrected_coms[prepi])
            corrected_prep_coms.append(self._convert_com_dict_units(corrected_com,self._image_to_physical))
        return corrected_prep_coms
        
    def get_prep_coms(self):
        """get beth's annotated com dictionary for a list of brains at June 2021"""
        prep_coms = [self._convert_com_dict_units(com_dict,self._image_to_physical) for name,com_dict in self.beth_coms.items()]
        return prep_coms

    def _combine_og_and_corrected_beth_annotation(self,og,corrected):
        """This function fills in the uncorrected com if Beth have not created an annotation for it.  This step is only necessary for this perticular com save"""
        og_landmarks = list(og.keys())
        corrected_landmarks = list(corrected.keys())
        for landmarki in og_landmarks:
            if landmarki not in corrected_landmarks:
                corrected[landmarki] = og[landmarki]
        return corrected

