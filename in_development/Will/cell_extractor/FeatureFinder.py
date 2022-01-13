import sys
import numpy as np
import pickle as pkl
from cell_extractor import compute_image_features 
import cv2
import pandas as pd
from cell_extractor.CellDetectorBase import CellDetectorBase,get_sections_with_annotation_for_animali,get_sections_without_annotation_for_animali
import os
class FeatureFinder(CellDetectorBase):
    """class to calculate feature vector for each extracted image pair (CH1, CH3)
    """
    def __init__(self,animal,section, *args, **kwargs):
        super().__init__(animal,section, *args, **kwargs)
        self.features = []
        print('DATA_DIR=%s'%(self.CH3))
        print(self.section,section)
        self.connected_segment_threshold=2000
        self.load_average_cell_image()
    
    def copy_information_from_examples(self,example):
        for key in ['animal','section','index','label','area','height','width']:
            self.featurei[key] = example[key]
        self.featurei['row'] = example['row']+example['origin'][0]
        self.featurei['col'] = example['col']+example['origin'][1]

    def calculate_correlation_and_energy(self,example,channel = 3):
        image = example[f'image_CH{channel}']
        average_image = getattr(self, f'average_image_ch{channel}')
        corr,energy = compute_image_features.calc_img_features(image,average_image)
        self.featurei[f'corr_CH{channel}'] = corr
        self.featurei[f'energy_CH{channel}'] = energy

    def connected_segment_detected_in_image(self,example,channel = 3):
        image = example[f'image_CH{channel}']
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
    
    def features_using_center_connectd_components(self,example):
        image1 = example[f'image_CH1']
        image3 = example[f'image_CH3']
        no,mask,statistics,center=cv2.connectedComponentsWithStats(np.int8(image3>self.connected_segment_threshold))
        middle_seg_mask = None
        if mask is not None:
            middle_segment_mask = self.get_middle_segment_mask(mask) 
            example['middle_segment_mask']=middle_segment_mask
            self.calc_center_features(image1,image3, middle_segment_mask)
   
    def calc_center_features(self,image1,image3, mask):
        def mask_mean(mask,image):
            mean_in=np.mean(image[mask==1])
            mean_all=np.mean(image.flatten())
            return (mean_in-mean_all)/(mean_in+mean_all)

        def append_string_to_every_key(dictionary, post_fix): 
            return dict(zip([keyi + post_fix for keyi in dictionary.keys()],dictionary.values()))
        
        def calc_moments_of_mask(mask):
            moments = self.calculate_moments(mask)
            huMoments = self.calculate_hu_moments(moments)
            moments = append_string_to_every_key(moments,f'CH_3')
            self.featurei.update(moments)
            self.featurei.update({'h%d'%i+f'_CH_3':huMoments[i,0]  for i in range(7)})
        
        def calc_contrasts_relative_to_mask(mask,image1,image3):
            self.featurei['contrast1']=mask_mean(mask,image1)
            self.featurei['contrast3']=mask_mean(mask,image3)
        
        calc_moments_of_mask(mask)
        calc_contrasts_relative_to_mask(mask,image1,image3)

    def calculate_features(self):
        """ Master function, calls methods to calculate the features that are then stored in self.features
        """
        self.load_examples()
        for tilei in range(len(self.Examples)):
            print(tilei)
            examplei = self.Examples[tilei]
            if examplei != []:
                for i in range(len(examplei)):
                    example=examplei[i]
                    self.featurei={}
                    self.copy_information_from_examples(example)
                    self.calculate_correlation_and_energy(example,channel=1)
                    self.calculate_correlation_and_energy(example,channel=3)
                    self.features_using_center_connectd_components(example)
                    self.features.append(self.featurei)
    
    def load_average_cell_image(self):
        if os.path.exists(self.AVERAGE_CELL_IMAGE_DIR):
            try:
                average_image = pkl.load(open(self.AVERAGE_CELL_IMAGE_DIR,'rb'))
            except IOError as e:
                print(e)
            self.average_image_ch1 = average_image['CH1']
            self.average_image_ch3 = average_image['CH3']

def calculate_all_sections_of_animali(animal):
    sections_with_csv = get_sections_without_annotation_for_animali(animal)
    for sectioni in sections_with_csv:
        print(f'processing section {sectioni}')
        finder = FeatureFinder(animal,sectioni)
        finder.calculate_features()
        finder.save_features()

def test_one_section(animal,section,disk):
    finder = FeatureFinder(animal,section = section,disk = disk)
    finder.calculate_features()
    finder.save_features()

def parallel_process_all_sections(animal,njobs = 40):
    base = CellDetectorBase(animal)
    sections_with_csv = base.get_sections_with_csv()
    with concurrent.futures.ProcessPoolExecutor(max_workers=njobs) as executor:
        for sectioni in sections_with_csv:
            results = executor.submit(test_one_section,animal,sectioni) 

if __name__ == '__main__':
    # parallel_process_all_sections('DK55')
    calculate_all_sections_of_animali('DK55')
    # test_one_section('DK55',180)