
print()
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import distance_matrix
import pickle as pk
from cell_extractor.CellDetectorBase import CellDetectorBase


class DetectorMetrics(CellDetectorBase):

    def __init__(self,animal,round=1):
        super().__init__(animal,round = round)
        self.qc_annotation_input_path = '/scratch/programming/preprocessing-pipeline/in_development/yoav/marked_cell_detector/data2/'
        self.pair_distance = 30

    def load_qc_annotations(self):
        dfs=self.load_human_qc()+self.load_machine_detection()
        self.qc_annotations=pd.concat(dfs)
        self.qc_annotations.columns=['x','y','section','name']
        self.qc_annotations['x']=np.round(self.qc_annotations['x'])
        self.qc_annotations['y']=np.round(self.qc_annotations['y'])
        self.nannotations = len( self.qc_annotations)
    
    def load_human_qc(self):
        self.annotation_category_and_filepath = {
            'manual_train':       self.qc_annotation_input_path+'/DK55_premotor_manual_2021-12-09.csv',
            'manual_negative':    self.qc_annotation_input_path+'/DK55_premotor_manual_negative_round1_2021-12-09.csv',
            'manual_positive':    self.qc_annotation_input_path+'/DK55_premotor_manual_positive_round1_2021-12-09.csv'}
        dfs=[]
        for name,path in self.annotation_category_and_filepath.items():
            df= pd.read_csv(path,header=None)
            df['name']=name
            dfs.append(df)
        return dfs

    def calculate_distance_matrix(self):
        df = self.qc_annotations.copy()
        df['section']*=1000
        self.distances=distance_matrix(np.array(df.iloc[:,:3]),np.array(df.iloc[:,:3]))

    def find_union(self,A,B):
        for b in B:
            if not b in A:
                A.append(b)
        return A,A

    def check(self,L,include=None,exclude=None,size_min=None,size_max=None):
        """ Return true if names in yes appear in L, names in no do not appear, 
            and the length of the list is between min_size and max_size"""
        if not include is None:
            for e in include:
                if not e in L:
                    return False
        if not exclude is None:
            for e in exclude:
                if e in L:
                    return False
        if not size_min is None:
                if len(L)<size_min:
                    return False
        if not size_max is None:
                if len(L)>size_max:
                    return False
        return True
    
    def find_close_pairs(self):
        very_close=self.distances<self.pair_distance
        close_pairs=np.transpose(np.nonzero(very_close))
        self.close_pairs=close_pairs[close_pairs[:,0]< close_pairs[:,1],:]
        self.npairs = len(self.close_pairs)
    
    def find_set_of_points_that_are_close_to_each_other(self):
        def find_all_pairs_that_are_close():
            self.pairs={}
            for i in range(self.nannotations):
                self.pairs[i]=[i]
            for i in range(self.npairs):
                first,second=self.close_pairs[i]
                self.pairs[first],self.pairs[second]=self.find_union(self.pairs[first],self.pairs[second])
        def find_category_of_close_pairs():
            categories=list(self.qc_annotations.iloc[:,-1])
            self.pair_categories={}
            for key in self.pairs:
                self.pair_categories[key]=[categories[i] for i in self.pairs[key]]
        def remove_duplicate_pairs():
            for i in range(len(self.pairs)):
                if not i in self.pairs:
                    continue
                for j in self.pairs[i]:
                    if j != i and j in self.pairs:
                        del self.pairs[j]
        find_all_pairs_that_are_close()
        print('before removing duplicates',len(self.pairs))
        remove_duplicate_pairs()
        print('after removing duplicates',len(self.pairs))
        find_category_of_close_pairs()
    
    def get_pairs_in_category(self,pair_category_criteria = lambda x : True):
        is_category = []
        for i in self.pairs:
            annotationi = self.qc_annotations.iloc[i,:]
            if pair_category_criteria(self.pair_categories[i]):
                is_category.append((i,annotationi))
        return is_category

    def calculate_and_save_qualifications(self):
        self.load_qc_annotations()
        self.calculate_distance_matrix()
        self.find_close_pairs()
        self.find_set_of_points_that_are_close_to_each_other()
        self.get_train_section_qualification()
        self.get_all_section_qualifications()
        self.print_qualifications(self.all_section_quantifications)
        self.print_qualifications(self.train_section_quantifications)
        pk.dump((self.all_section_quantifications,self.train_section_quantifications),open(self.QUALIFICATIONS,'wb'))

    def get_train_section_qualification(self):
        self.train_section_quantifications={}
        category_name_and_criteria = {
            'Computer Detected, Human Missed'           :lambda pair_categories : self.check(pair_categories,include=['computer_sure'],size_max=1),
            'total train'                               :lambda pair_categories : self.check(pair_categories,include=['manual_train']),
            'Human mind change'                         :lambda pair_categories : self.check(pair_categories,include=['manual_negative','manual_train']),
            'original training set after mind change'   :lambda pair_categories : self.check(pair_categories,include=['manual_train'],exclude=['manual_negative'])}
        for category,criteria in category_name_and_criteria.items():
            self.train_section_quantifications[category] = self.get_pairs_in_category(pair_category_criteria = criteria)
    
    def get_all_section_qualifications(self):
        self.all_section_quantifications = {}
        category_name_and_criteria = {
            'computer missed, human detected'   :lambda pair_categories : self.check(pair_categories,include=['manual_positive'],exclude=['computer_sure','computer_unsure'],size_max=1),
            'computer sure, human negative'     :lambda pair_categories : self.check(pair_categories,include=['computer_sure','manual_negative'],size_max=2),
            'computer  UNsure, human negative'  :lambda pair_categories : self.check(pair_categories,include=['computer_unsure','manual_negative'],size_max=2),
            'computer UNsure, human positive'   :lambda pair_categories : self.check(pair_categories,include=['computer_unsure','manual_positive'],size_max=2),
            'Total computer UNsure'             :lambda pair_categories : self.check(pair_categories,include=['computer_unsure'],size_max=2),
            'computer UNsure, human unmarked'   :lambda pair_categories : self.check(pair_categories,include=['computer_unsure'],size_max=1),
            'computer sure, human unmarked'     :lambda pair_categories : self.check(pair_categories,include=['computer_sure'],size_max=1),
            'More than 2 labels'                :lambda pair_categories : self.check(pair_categories,exclude=['manual_train'],size_min=3)
        }
        for category,criteria in category_name_and_criteria.items():
            self.all_section_quantifications[category] = self.get_pairs_in_category(pair_category_criteria = criteria)

    def print_qualifications(self,qualifications):
        for keyi in qualifications:
            print(keyi)
            print(len(qualifications[keyi]))


class DetectorMetricsDK55Round1(DetectorMetrics):
    def __init__(self,*args,**kwrds):
        super().__init__(*args,**kwrds)
    
    def load_machine_detection(self):
        self.machine_detection_filepath ={
            'computer_sure':      self.qc_annotation_input_path+'/DK55_premotor_sure_detection_2021-12-09.csv',
            'computer_unsure':    self.qc_annotation_input_path+'/DK55_premotor_unsure_detection_2021-12-09.csv'}
        dfs=[]
        for name,path in self.machine_detection_filepath.items():
            df= pd.read_csv(path,header=None)
            df['name']=name
            dfs.append(df)
        return dfs


if __name__=='__main__':
    mec = DetectorMetricsDK55Round1('DK55',round =1)
    mec.calculate_and_save_qualifications()