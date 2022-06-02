
print()
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import distance_matrix
import pickle as pk
from cell_extractor.CellDetectorBase import CellDetectorBase


class AnnotationProximityTool(CellDetectorBase):
    '''
    This tool finds and groups annotations that are really close together.
    The aim is to identify annotations of the same cell that are marked by different detector or annotatators
    '''

    def __init__(self,*arg,**kwarg):
        super().__init__(*arg,**kwarg)
        self.pair_distance = 30

    def calculate_distance_matrix(self):
        print('calculating distance matrix')
        df = self.annotations_to_compare.copy()
        df['section']*=1000
        self.distances=distance_matrix(np.array(df.iloc[:,:3]),np.array(df.iloc[:,:3]))

    def find_union(self,A,B):
        for b in B:
            if not b in A:
                A.append(b)
        return A,A

    def check(self,L,include=None,exclude=None,size_min=None,size_max=None):
        """ Return true if names in include appear in L, names in exclude do not appear in L, 
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
        print('finding points that are close to each other')
        very_close=self.distances<self.pair_distance
        close_pairs=np.transpose(np.nonzero(very_close))
        self.close_pairs=close_pairs[close_pairs[:,0]< close_pairs[:,1],:]
        self.npairs = len(self.close_pairs)
    
    def group_and_label_close_pairs(self):
        print('grouping and labeling points that are close to each other')
        def group_close_paris():
            self.pairs={}
            for i in range(self.nannotations):
                self.pairs[i]=[i]
            for i in range(self.npairs):
                first,second=self.close_pairs[i]
                self.pairs[first],self.pairs[second]=self.find_union(self.pairs[first],self.pairs[second])
        def find_category_of_close_pairs():
            categories=list(self.annotations_to_compare.iloc[:,-1])
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
        group_close_paris()
        print('before removing duplicates',len(self.pairs))
        remove_duplicate_pairs()
        print('after removing duplicates',len(self.pairs))
        find_category_of_close_pairs()
    
    def get_pairs_in_category(self,pair_category_criteria = lambda x : True):
        is_category = []
        for i in self.pairs:
            annotationi = self.annotations_to_compare.iloc[i,:]
            if pair_category_criteria(self.pair_categories[i]):
                is_category.append((i,annotationi))
        return is_category

    def print_quantification(self,quantification):
        for keyi in quantification:
            print(keyi)
            print(len(quantification[keyi]))
    
    def set_annotations_to_compare(self,annotations):
        '''annotations_to_compare should be a dataframe with the columns:
           x:       x coordinate, float
           y:       y coordinate, float
           section: section number, int/float
           name:    category of the annotation. str
        '''
        self.annotations_to_compare = annotations
        self.nannotations = len(annotations)
    
    def find_equivalent_points(self):
        self.calculate_distance_matrix()
        self.find_close_pairs()
        self.group_and_label_close_pairs()


class DetectorMetricsDK55(AnnotationProximityTool):
    def __init__(self,animal = 'DK55',sure_file_name = '/DK55_premotor_sure_detection_2021-12-09.csv',unsure_file_name = '/DK55_premotor_unsure_detection_2021-12-09.csv', *args,**kwrds):
        super().__init__(animal,*args,**kwrds)
        self.sure_file_name = sure_file_name
        self.unsure_file_name = unsure_file_name
        self.qc_annotation_input_path = '/home/zhw272/programming/pipeline_utility/in_development/yoav/marked_cell_detector/data2/'

    def load_annotations_to_compare(self):
        dfs=self.load_human_qc()+self.load_machine_detection()
        self.annotations_to_compare=pd.concat(dfs)
        self.annotations_to_compare.columns=['x','y','section','name']
        self.annotations_to_compare['x']=np.round(self.annotations_to_compare['x'])
        self.annotations_to_compare['y']=np.round(self.annotations_to_compare['y'])
        self.nannotations = len( self.annotations_to_compare)
    
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
    
    def load_machine_detection(self):
        self.machine_detection_filepath ={
            'computer_sure':      self.qc_annotation_input_path+self.sure_file_name,
            'computer_unsure':    self.qc_annotation_input_path+self.unsure_file_name}
        dfs=[]
        for name,path in self.machine_detection_filepath.items():
            df= pd.read_csv(path,header=None)
            df['name']=name
            dfs.append(df)
        return dfs
    
    def calculate_qualification(self):
        self.load_annotations_to_compare()
        self.calculate_distance_matrix()
        self.find_close_pairs()
        self.group_and_label_close_pairs()
        self.get_train_section_quantification()
        self.get_all_section_quantification()
        self.print_quantification(self.all_section_quantifications)
        self.print_quantification(self.train_section_quantifications)
    
    def calculate_and_save_quantification(self):
        self.calculate_qualification()
        pk.dump((self.all_section_quantifications,self.train_section_quantifications),open(self.quantification,'wb'))

    def get_train_section_quantification(self):
        self.train_section_quantifications={}
        category_name_and_criteria = {
            'Computer Detected, Human Missed'           :lambda pair_categories : self.check(pair_categories,include=['computer_sure'],size_max=1),
            'total train'                               :lambda pair_categories : self.check(pair_categories,include=['manual_train']),
            'Human mind change'                         :lambda pair_categories : self.check(pair_categories,include=['manual_negative','manual_train']),
            'original training set after mind change'   :lambda pair_categories : self.check(pair_categories,include=['manual_train'],exclude=['manual_negative'])}
        for category,criteria in category_name_and_criteria.items():
            self.train_section_quantifications[category] = self.get_pairs_in_category(pair_category_criteria = criteria)
    
    def get_all_section_quantification(self):
        self.all_section_quantifications = {}
        category_name_and_criteria = {
            'computer missed, human detected'   :lambda pair_categories : self.check(pair_categories,include=['manual_positive'],exclude=['computer_sure','computer_unsure'],size_max=1),
            'computer sure, human negative'     :lambda pair_categories : self.check(pair_categories,include=['computer_sure','manual_negative'],size_max=2),
            'computer  UNsure, human negative'  :lambda pair_categories : self.check(pair_categories,include=['computer_unsure','manual_negative'],size_max=2),
            'computer UNsure, human positive'   :lambda pair_categories : self.check(pair_categories,include=['computer_unsure','manual_positive'],size_max=2),
            'Total computer UNsure'             :lambda pair_categories : self.check(pair_categories,include=['computer_unsure'],size_max=2),
            'computer UNsure, human unmarked'   :lambda pair_categories : self.check(pair_categories,include=['computer_unsure'],size_max=1),
            'computer sure, human unmarked'     :lambda pair_categories : self.check(pair_categories,include=['computer_sure'],size_max=1),
            'More than 2 labels'                :lambda pair_categories : self.check(pair_categories,exclude=['manual_train'],size_min=3)}
        for category,criteria in category_name_and_criteria.items():
            self.all_section_quantifications[category] = self.get_pairs_in_category(pair_category_criteria = criteria)


if __name__=='__main__':
    mec = DetectorMetricsDK55('DK55',round =1)
    mec.calculate_qualification()
