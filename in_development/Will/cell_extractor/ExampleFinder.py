import sys
import cv2
import pandas as pd
import numpy as np
import os
from numpy.linalg import norm
from time import time
import glob
import pickle as pkl
from cell_extractor.CellDetectorBase import CellDetectorBase,get_sections_with_annotation_for_animali,\
    get_sections_without_annotation_for_animali
import concurrent.futures

class ExampleFinder(CellDetectorBase):
    def __init__(self,animal,section, *args, **kwargs):
        super().__init__(animal,section, *args, **kwargs)
        self.t0=time()
        print('section=%d, SECTION_DIR=%s'%(self.section,self.CH3_SECTION_DIR))
        self.thresh=2000
        self.radius=40
        self.max_segment_size = 100000
        self.cell_counter = 0
        self.Examples=[]
        self.Stats_list=[]
        self.diff_list=[]

    def find_examples(self):    
        self.load_manual_annotation()
        for tile in range(10):
            self.load_and_preprocess_image(tile)
            self.find_connected_segments(self.difference_ch3)
            if self.n_segments>2:
                self.load_manual_labels_in_tilei(tile)
                self.is_possitive_segment=np.zeros(self.n_segments) 
                self.positive_segment_locations=np.zeros([self.n_segments,2])
                if self.n_manual_label>0:   
                    self.labels_with_no_matching_segments=[]
                    for labeli in range(self.n_manual_label):
                        cloest_segment_id,labelx,labely = self.find_cloest_connected_segment_to_manual_labeli(labeli)
                        self.is_possitive_segment[cloest_segment_id]=1
                        self.positive_segment_locations[cloest_segment_id,:]=[labelx,labely]
                tilei_examples=self.get_examples(tile)
                print(len(tilei_examples))
                self.Examples.append(tilei_examples)
        
    def load_manual_annotation(self):
        file_list = glob.glob(os.path.join(self.CH3_SECTION_DIR, f'*premotor*{self.section}*.csv'))
        if file_list != []:
            dfpath = file_list[0]
            self.manual_annotation = pd.read_csv(dfpath)
        else:
            self.manual_annotation = None

    def get_examples(self,tile):
        origin = self.get_tile_origin(tile)
        Examples=[]
        for labeli in range(len(self.is_possitive_segment)):
            _,_,width,height,area = self.connected_segment_info[2][labeli,:]
            if area>self.max_segment_size: 
                continue
            segment_row,segment_col= self.segment_location[labeli,:] 
            row_start = int(segment_row-self.radius)
            col_start = int(segment_col-self.radius)
            if row_start < 0 or col_start < 0:
                continue
            row_end = int(segment_row+self.radius)
            col_end = int(segment_col+self.radius)
            if row_end > self.tile_height or col_end > self.tile_width:
                continue
            if self.is_possitive_segment[labeli] == 1:
                print('positive label')
                print(len(self.Examples),len(Examples))
            if self.difference_ch3[row_start:row_end,col_start:col_end].size ==0:
                breakpoint()
            if self.difference_ch1[row_start:row_end,col_start:col_end].size == 0 :
                breakpoint()
            example={'animal':self.animal,
                     'section':self.section,
                     'index':self.cell_counter,
                     'label':int(self.is_possitive_segment[labeli]),
                     'area':area,
                     'row':segment_row,
                     'col':segment_col,
                     'origin':origin,
                     'height':height,
                     'width':width,
                     'image_CH3':self.difference_ch3[row_start:row_end,col_start:col_end],
                     'image_CH1':self.difference_ch1[row_start:row_end,col_start:col_end]}
            self.cell_counter+=1
            Examples.append(example)
        return Examples

    def get_tilei(self,tilei,channel = 3):
        folder = getattr(self, f'CH{channel}_SECTION_DIR')
        file = f'{self.section:03}tile-{tilei}.tif'
        infile = os.path.join(folder, file)
        img = np.float32(cv2.imread(infile, -1))
        return img
    
    def subtract_blurred_image(self,image):
        small=cv2.resize(image,(0,0),fx=0.05,fy=0.05, interpolation=cv2.INTER_AREA)
        blurred=cv2.GaussianBlur(small,ksize=(21,21),sigmaX=10)
        relarge=cv2.resize(blurred, image.T.shape,interpolation=cv2.INTER_AREA)
        difference=image-relarge
        return difference
    
    def load_manual_labels_in_tilei(self,tilei):
        if self.manual_annotation != None:
            manual_annotation_array = self.manual_annotation[['y','x']] 
            self.manual_labels_in_tile,self.n_manual_label = \
                self.get_manual_annotation_in_tilei(manual_annotation_array,tilei)
        else:
            self.n_manual_label = 0
            
    def find_connected_segments(self,image):
        self.connected_segment_info=cv2.connectedComponentsWithStats(np.int8(image>self.thresh))
        self.n_segments,self.segment_masks,self.segment_stats,self.segment_location \
            = cv2.connectedComponentsWithStats(np.int8(image>self.thresh))
        if self.n_segments>2:
            self.Stats_list.append([self.n_segments,self.segment_masks,self.segment_stats,self.segment_location])
            self.n_connected_segments = self.connected_segment_info[2].shape[0]
            self.segment_location=np.int32(self.segment_location)  
            self.segment_location = np.flip(self.segment_location,1)
        
    
    def load_and_preprocess_image(self,tile):
        self.ch3_image = self.get_tilei(tile,channel = 3)
        self.ch1_image = self.get_tilei(tile,channel = 1)
        print(tile)
        self.difference_ch3 = self.subtract_blurred_image(self.ch3_image)
        self.difference_ch1 = self.subtract_blurred_image(self.ch1_image)
        self.diff_list.append(self.difference_ch3)


    def find_cloest_connected_segment_to_manual_labeli(self,labeli):
        labelx,labely=self.manual_labels_in_tile[labeli]
        self.segment_distance_to_label=norm(self.segment_location-self.manual_labels_in_tile[labeli],axis=1)
        self.cloest_segment_id=np.argmin(self.segment_distance_to_label)  
        cloest_segment_distance = np.min(self.segment_distance_to_label)
        self.segment_id_at_label_location=self.segment_masks[labelx,labely] 
        if self.label_is_not_in_cloest_segment():
            self.labels_with_no_matching_segments.append((labeli,cloest_segment_distance,self.segment_id_at_label_location,self.cloest_segment_id))
        return self.cloest_segment_id , labelx , labely

    def label_is_not_in_cloest_segment(self):
        return self.cloest_segment_id !=self.segment_id_at_label_location

def process_all_sections_with_annotation(animal):
    sections_with_csv = get_sections_with_annotation_for_animali(animal)
    process_all_sections_in_list(animal,sections_with_csv)

def process_all_sections_without_annotation(animal):
    sections_without_csv = get_sections_without_annotation_for_animali(animal)
    process_all_sections_in_list(animal,sections_without_csv)

def process_all_sections_in_list(animal,section_list):
    base = CellDetectorBase(animal)
    for sectioni in section_list:
        print(f'processing section {sectioni}')
        extractor = ExampleFinder(animal,sectioni)
        extractor.find_examples()
        extractor.save_examples()

def parallel_process_all_sections(animal,njobs = 40):
    sections_with_csv = get_sections_without_annotation_for_animali(animal)
    with concurrent.futures.ProcessPoolExecutor(max_workers=njobs) as executor:
        results = []
        for sectioni in sections_with_csv:
            print(sectioni)
            results.append(executor.submit(test_one_section,animal,sectioni))
        print('done')

def test_one_section(animal,section,disk):
    extractor = ExampleFinder(animal=animal,section=section,disk=disk)
    extractor.find_examples()
    extractor.save_examples()

if __name__ == '__main__':
    animal = 'DK52'
    base = CellDetectorBase(animal)
    section_list = base.get_sections_without_example()
    process_all_sections_in_list(animal,section_list)
    # test_one_section('DK55',180)
    # process_all_sections_with_annotation('DK52')
    # process_all_sections_without_annotation('DK52')
    
