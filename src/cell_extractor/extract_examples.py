import sys
import cv2
import pandas as pd
import numpy as np
import os
import cv2
from numpy.linalg import norm
from time import time
import glob
import pickle as pkl
from CellDetectorBase import CellDetectorBase

class SampleExtractor(CellDetectorBase):
    def __init__(self,animal,section):
        super().__init__(animal,section)
        self.t0=time()
        self.section=section
        print('section=%d, SECTION_DIR=%s'%(self.section,self.CH3_SECTION_DIR))
        self.thresh=2000
        self.min_example_size=int(100/2)
        self.max_segment_size = 100000
        self.cell_counter = 0
        self.Examples=[]
        self.Stats_list=[]
        self.diff_list=[]

    def find_examples(self):    
        self.load_manual_annotation()
        for tile in range(10):
            self.load_and_preprocess_image(tile)
            self.find_connected_segments(difference_ch3)
            if not self.found_connected_segments:
                continue
            self.load_manual_labels_in_tilei(tile)
            self.is_possitive_segment=np.zeros(self.n_connected_segments) 
            self.positive_segment_locations=np.zeros([self.n_connected_segments,2])
            if self.n_manual_label>0:   
                self.labels_with_no_matching_segments=[]
                for labeli in range(self.n_manual_label):
                    cloest_segment_id,labelx,labely = self.find_cloest_connected_segment_to_manual_labeli(labeli)
                    self.is_possitive_segment[cloest_segment_id]=1
                    self.positive_segment_locations[cloest_segment_id,:]=[labelx,labely]
                print('tile=%d positives=%d, unmatched (size=%d):\n '%(tile,sum(self.is_possitive_segment),
                len(self.labels_with_no_matching_segments)),self.labels_with_no_matching_segments)
            tilei_examples=self.get_examples()
            self.Examples.append(tilei_examples)

    def save_examples(self):
        out={'Examples':self.Examples}
        print('about to write',time()-self.t0)
        t1=time()
        with open(self.get_example_save_path()) as pkl_file:
            pkl.dump(out,pkl_file)
        print('finished writing ',time()-t1)
        
    def load_manual_annotation(self):
        dfpath = glob.glob(os.path.join(self.CH3_SECTION_DIR, f'*{self.section}*.csv'))[0]
        self.manual_annotation = pd.read_csv(dfpath)

    def get_examples(self):
        origin = self.get_tile_origin(tile)
        Examples=[]
        for labeli in range(len(self.is_possitive_segment)):
            _,_,width,height,area = self.connected_segment_info[2][labeli,:]
            if area>self.max_segment_size: 
                continue
            segment_col,segment_row= self.segment_location[labeli,:] 
            example_half_height=max(2*height,self.min_example_size)  
            example_half_width=max(2*width,self.min_example_size)
            row_start = int(segment_row-example_half_height)
            col_start = int(segment_col-example_half_width)
            row_end = int(segment_row+example_half_height)
            row_end = int(segment_col+example_half_width)
            example={'animal':animal,
                    'section':self.section,
                    'index':self.cell_counter,
                    'label':int(self.is_possitive_segment[labeli]),
                    'area':area,
                    'row':segment_row,
                    'col':segment_col,
                    'origin':origin,
                    'height':height,
                    'width':width,
                    'image_CH3':self.difference_ch3[row_start:row_end,col_start:row_end],
                    'image_CH1':self.difference_ch1[row_start:row_end,col_start:row_end]
                    }
            self.cell_counter+=1
            Examples.append(example)
        return Examples

    def get_tilei(self,tilei,channel = 3):
        folder = getattr(self, f'CH{channel}_SECTION_DIR')
        file = f'{self.section:03}tile-{tilei}.tif'
        infile = os.path.join(folder, file)
        img = np.float32(cv2.imread(infile, -1))
        print('tile=',tilei,end=',')
        return img
    
    def subtract_blurred_image(self,image):
        small=cv2.resize(image,(0,0),fx=0.05,fy=0.05, interpolation=cv2.INTER_AREA)
        blurred=cv2.GaussianBlur(small,ksize=(21,21),sigmaX=10)
        relarge=cv2.resize(blurred,(0,0),fx=20,fy=20) #,interpolation=cv2.INTER_AREA)
        difference=image-relarge
        return difference
    
    def load_manual_labels_in_tilei(self,tilei):
        tile_origin= self.get_tile_origin(tilei)
        manual_labels=np.int32(self.manual_annotation[['y','x']])-tile_origin   
        self.manual_labels_in_tile=[]
        for i in range(manual_labels.shape[0]):
            row,col=list(manual_labels[i,:])
            if row<0 or row>=self.tile_height or col<0 or col>=self.tile_width:
                continue
            self.manual_labels_in_tile.append(np.array([row,col]))
        if not self.manual_labels_in_tile ==[]:
            self.manual_labels_in_tile=np.stack(self.manual_labels_in_tile)
        else:
            self.manual_labels_in_tile = np.array([])
        print('Manual Detections = %d'%len(self.manual_labels_in_tile))
        self.n_manual_label = len(self.manual_labels_in_tile) 
    
    def find_connected_segments(self,image):
        self.connected_segment_info=cv2.connectedComponentsWithStats(np.int8(image>self.thresh))
        print('Computer Detections=',self.connected_segment_info[0],end=',')
        self.found_connected_segments = self.connected_segment_info[0]>2
        if not segments_found:
            print('skipping tile')
        else:
            self.Stats_list.append(self.connected_segment_info)
            self.n_connected_segments = self.connected_segment_info[2].shape[0]
            self.segment_map = self.connected_segment_info[1]
            self.segment_location=np.int32(self.connected_segment_info[3])  
            self.segment_location = np.flip(self.segment_location,1)
        
    
    def load_and_preprocess_image(self,tile):
        self.ch3_image = self.get_tilei(tile,channel = 3)
        self.ch1_image = self.get_tilei(tile,channel = 1)
        self.difference_ch3 = self.subtract_blurred_image(ch3_image)
        self.difference_ch1 = self.subtract_blurred_image(ch1_image)
        self.diff_list.append(difference_ch3)


    def find_cloest_connected_segment_to_manual_labeli(self,labeli):
        labelx,labely=self.manual_labels_in_tile[labeli]
        self.segment_distance_to_label=norm(self.segment_location-self.manual_labels_in_tile[labeli],axis=1)
        self.cloest_segment_id=np.argmin(self.segment_distance_to_label)  
        cloest_segment_distance = np.min(self.segment_distance_to_label)
        self.segment_id_at_label_location=self.segment_map[labelx,labely] 
        if self.label_is_not_in_cloest_segment():
            self.labels_with_no_matching_segments.append((labeli,cloest_segment_distance,self.segment_id_at_label_location,self.cloest_segment_id))
        return self.cloest_segment_id , labelx , labely

    def label_is_not_in_cloest_segment(self):
        return self.cloest_segment_id !=self.segment_id_at_label_location


if __name__ == '__main__':
    animal = 'DK55'
    extractor = SampleExtractor(animal,1)
    sections_with_csv = extractor.get_sections_with_csv()
    for sectioni in sections_with_csv:
        print(f'processing section {sectioni}')
        extractor = SampleExtractor(animal,sectioni)
        extractor.find_examples()
        extractor.save_examples()