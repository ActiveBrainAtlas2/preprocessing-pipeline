import sys
import numpy as np
import pickle as pkl
from cell_extractor import compute_image_features 
import cv2
import pandas as pd
from cell_extractor.CellDetectorBase import CellDetectorBase,get_sections_with_annotation_for_animali

class FeatureFinder(CellDetectorBase):
    def __init__(self,animal,section):
        super().__init__(animal,section)
        self.features = []
        print('DATA_DIR=%s'%(self.CH3))
        self.connected_segment_threshold=2000
    
    def copy_information_from_examples(self,example):
        for key in ['animal','section','index','label','area','height','width']:
            self.featurei[key] = example[key]
        self.featurei['row'] = example['row']+example['origin'][0]
        self.featurei['col'] = example['col']+example['origin'][1]

    def calculate_correlation_and_energy(self,image):
        corr,energy = compute_image_features.calc_img_features(image,self.average_image)
        self.featurei['corr'] = corr
        self.featurei['energy'] = energy

    def connected_segment_detected_in_image(self,image):
        Stats=cv2.connectedComponentsWithStats(np.int8(image>self.connected_segment_threshold))
        return Stats[1] is not None
    
    def get_middle_segment_mask(self,segments):
        middle=np.array(np.array(segments.shape)/2,dtype=np.int16)
        middle_seg=segments[middle[0],middle[1]]
        middle_seg_mask = np.uint8(segments==middle_seg)
        return middle_seg_mask
    
    def calculate_moments(self,middle_seg_mask):
        return cv2.moments(middle_seg_mask)
    
    def calculate_hu_moments(self,moments):
        return cv2.HuMoments(moments)

    def calculate_moment_and_hu_moment(self,image):
        Stats=cv2.connectedComponentsWithStats(np.int8(image>self.connected_segment_threshold))
        connected_segments=Stats[1]
        middle_seg_mask = self.get_middle_segment_mask(connected_segments)  
        moments = self.calculate_moments(middle_seg_mask)
        self.featurei.update(moments)
        huMoments = self.calculate_hu_moments(moments)       
        self.featurei.update({'h%d'%i:huMoments[i,0]  for i in range(7)})
        
    def calculate_features(self):
        self.load_examples()
        for tilei in range(len(self.Examples)):
            print(tilei)
            examplei = self.Examples[tilei]
            if examplei != []:
                self.average_image = self.calculate_average_cell_images(examplei)
                for example in examplei:
                    image = example['image_CH3']
                    self.featurei={}
                    self.copy_information_from_examples(example)
                    self.calculate_correlation_and_energy(image)
                    if self.connected_segment_detected_in_image(image):
                        self.calculate_moment_and_hu_moment(image)
                    self.features.append(self.featurei)

    def calculate_average_cell_images(self,examples):
        images = []
        for examplei in examples:
            images.append(examplei['image_CH3'])
        images = np.stack(images)
        average = np.average(images,axis=0)
        average = (average - average.mean())/average.std()
        return average

def calculate_all_sections_of_animali(animal):
    sections_with_csv = get_sections_with_annotation_for_animali(animal)
    for sectioni in sections_with_csv:
        print(f'processing section {sectioni}')
        finder = FeatureFinder(animal,sectioni)
        finder.calculate_features()
        finder.save_features()

def test_one_section(animal,section):
    finder = FeatureFinder(animal,section)
    finder.calculate_features()
    finder.save_features()

if __name__ == '__main__':
    # test_one_section('DK55',180)
    calculate_all_sections_of_animali('DK55')