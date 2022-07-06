import sys
from toolbox.IOs.LoadCom import LoadCom
import os
import pickle
import sys
import numpy as np
from abakit.lib.Controllers.SqlController import SqlController
controller = SqlController('DK52')

class LoadComDatabase(LoadCom):

    def get_atlas_com(self):
        return controller.get_atlas_centers()

    def get_prepi_com(self,prepi):
        com = controller.get_com_dict(prepi,input_type_id=1,person_id=2,active=True)
        return com

    def get_corrected_prepi_com(self,prepi):
        return controller.get_com_dict(prepi,input_type_id=2,person_id=2,active=True)

    def get_corrected_dk52_com(self):
        return self.get_corrected_prepi_com('DK52')

    def get_dk52_com(self):
        return self.get_prepi_com('DK52')

    def get_corrected_prep_coms(self):
        prep_list = self.get_prep_list_for_rough_alignment_test()
        corrected_prep_coms = []
        for prepi in prep_list:
            corrected_com = self.combined_og_and_corrected_beth_annotation(self.get_prepi_com(prepi),self.get_corrected_prepi_com(prepi))
            corrected_prep_coms.append(corrected_com)
        return corrected_prep_coms

    def get_prep_coms(self):
        prep_list = self.get_prep_list_for_rough_alignment_test()
        prep_coms = [self.get_prepi_com(prepi) for prepi in prep_list]
        return prep_coms

    def combined_og_and_corrected_beth_annotation(self,og,corrected):
        og_landmarks = list(og.keys())
        corrected_landmarks = list(corrected.keys())
        for landmarki in og_landmarks:
            if landmarki not in corrected_landmarks:
                corrected[landmarki] = og[landmarki]
        return corrected
