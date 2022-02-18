from lib.UrlGenerator import UrlGenerator
from lib.SqlController import SqlController
import pickle
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import glob
controller = SqlController('DK52')
class ComLoader:

    def __init__(self):
        ...

    def load_detected_com(self):
        path = '/home/zhw272/Downloads/'
        pattern = '*_correct_coms.pkl'
        files = glob.glob(path+pattern)
        self.detected = {}
        for filei in files:
            animal_string_start = filei.index('DK')
            animali = filei[animal_string_start:animal_string_start+4]
            coms = pickle.load(open(filei,'rb'))
            comskeys = list(coms.keys())
            comvals = list(coms.values())
            comvals = [np.array(vali)*np.array([0.325,0.325,20]) for vali in comvals]
            self.detected[animali] = dict(zip(comskeys,comvals))

    def load_data(self):
        path = '/home/zhw272/Downloads/AtlasCOMsStack.pkl'
        file = open(path,'rb')
        self.aligned_atlas_coms  = pickle.load(file)
        self.animals = list(self.aligned_atlas_coms .keys())
        self.new_coms = {}
        self.stats = {}
        self.all_coms = {}
        for animali in self.animals:
            self.new_coms[animali] = controller.get_layer_data_entry(prep_id = animali,layer = 'COM_addition')
        self.coms = {}
        for animali in self.animals:
            self.coms[animali] = controller.get_com_dict(prep_id = animali)
            self.all_coms[animali] = self.coms[animali]
            self.all_coms[animali].update(self.new_coms[animali])
        print('done')