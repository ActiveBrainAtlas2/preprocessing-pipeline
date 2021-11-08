import sys
import numpy as np
import pickle as pkl
from cell_extractor import compute_image_features 
import cv2
import pandas as pd
from cell_extractor.CellDetectorBase import CellDetectorBase,get_sections_with_annotation_for_animali,parallel_process_all_sections
import os
class FeatureFinder(CellDetectorBase):
    def __init__(self,animal,section):
        super().__init__(animal,section)
        self.features = []
        print('DATA_DIR=%s'%(self.CH3))
        self.connected_segment_threshold=2000
        self.load_or_calulate_average_cell_image()
    
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

    def calculate_moment_and_hu_moment(self,example,channel = 3):
        append_string_to_every_key = lambda dictionary, post_fix : dict(zip([keyi + post_fix for keyi in dictionary.keys()],dictionary.values()))
        image = example[f'image_CH{channel}']
        Stats=cv2.connectedComponentsWithStats(np.int8(image>self.connected_segment_threshold))
        connected_segments=Stats[1]
        middle_seg_mask = self.get_middle_segment_mask(connected_segments)  
        moments = self.calculate_moments(middle_seg_mask)
        moments = append_string_to_every_key(moments,f'CH_{channel}')
        self.featurei.update(moments)
        huMoments = self.calculate_hu_moments(moments)       
        self.featurei.update({'h%d'%i:huMoments[i,0]+f'_CH_{channel}'  for i in range(7)})
        
    def calculate_features(self):
        self.load_examples()
        for tilei in range(len(self.Examples)):
            print(tilei)
            examplei = self.Examples[tilei]
            if examplei != []:
                for example in examplei:
                    self.featurei={}
                    self.copy_information_from_examples(example)
                    self.calculate_correlation_and_energy(example,channel=1)
                    self.calculate_correlation_and_energy(example,channel=3)
                    if self.connected_segment_detected_in_image(example):
                        self.calculate_moment_and_hu_moment(example,channel=1)
                        self.calculate_moment_and_hu_moment(example,channel=3)
                    self.features.append(self.featurei)

    def calculate_average_cell_images(self,examples,channel = 3):
        images = []
        for examplei in examples:
            images.append(examplei[f'image_CH{channel}'])
        images = np.stack(images)
        average = np.average(images,axis=0)
        average = (average - average.mean())/average.std()
        return average
    
    def load_or_calulate_average_cell_image(self):
        if os.path.exists(self.AVERAGE_CELL_IMAGE_DIR_CH1) and os.path.exists(self.AVERAGE_CELL_IMAGE_DIR_CH3):
            self.average_image_ch1 = pkl.load(open(self.AVERAGE_CELL_IMAGE_DIR_CH1,'rb'))
            self.average_image_ch3 = pkl.load(open(self.AVERAGE_CELL_IMAGE_DIR_CH3,'rb'))
        else:
            examples = self.load_all_examples_in_brain()
            self.average_image_ch1 = self.calculate_average_cell_images(examples,channel = 1)
            self.average_image_ch3 = self.calculate_average_cell_images(examples,channel = 3)
            pkl.dump(open(self.average_image_ch1,self.AVERAGE_CELL_IMAGE_DIR_CH1,'wb'))
            pkl.dump(open(self.average_image_ch3,self.AVERAGE_CELL_IMAGE_DIR_CH3,'wb'))

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

def parallel_process_all_sections(animal,njobs = 40):
    base = CellDetectorBase(animal)
    sections_with_csv = base.get_sections_with_csv()
    with concurrent.futures.ProcessPoolExecutor(max_workers=njobs) as executor:
        for sectioni in sections_with_csv:
            results = executor.submit(test_one_section,animal,sectioni) 

if __name__ == '__main__':
    # parallel_process_all_sections('DK55')
    calculate_all_sections_of_animali('DK55')