from CellDetectorBase import CellDetectorBase
import os
import matplotlib.pyplot as plt
from tifffile import imread
import numpy as np
from scipy.signal import argrelextrema,find_peaks
import cv2
from concurrent.futures.process import ProcessPoolExecutor

class BorderFinder(CellDetectorBase):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.BORDER_INFO = os.path.join(self.ANIMAL_PATH,'border_info.pkl')
        self.folder = f'/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{self.animal}/preps/CH1/thumbnail/'
        self.SCALING_FACTOR = 0.03125

    def load_images(self):
        files = os.listdir(self.folder)
        self.imgs = []
        for file in files:
            img = imread(self.folder+file)
            self.imgs.append(img)

    def find_thresholds(self):
        self.thresholds = []
        bins = np.linspace(0,2000,100)
        for img in self.imgs:
            data = img.flatten()
            line,bins = np.histogram(data,bins)
            peaks = find_peaks(-line,prominence=10)[0][0]
            self.thresholds.append(peaks)

    def find_max_contour(self):
        self.max_contours = []
        for i,threshold in enumerate(self.thresholds):
            mask = self.imgs[i]>threshold
            mask = np.array(mask*255).astype('uint8')
            _, thresh = cv2.threshold(mask, 200, 255, 0)
            contours = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
            areas = area = [cv2.contourArea(i) for i in contours]
            max_id = np.argmax(areas)
            max_con = contours[max_id]
            max_con = max_con.reshape(-1,2)
            self.max_contours.append(max_con)

    def find_border_regions(self):
        self.borders = []
        for i,max_con in enumerate(self.max_contours):
            self.borders.append(find_border(max_con,self.imgs[i].shape))

    def find_border_cells(self):
        detections = self.load_detections()
        is_border_cell = np.zeros(len(detections))==1
        for sectioni in detections.section.unique():
            in_section = detections.section==sectioni
            detection_in_section = detections[in_section]
            coords = np.array([[i.col*self.SCALING_FACTOR,i.row*self.SCALING_FACTOR] for i in detection_in_section.iterrow()]).astype(int)
            in_border = np.array([self.borders[sectioni][i] for i in coords])
            is_border_cell[in_section]=in_border

    def run_commands_in_parallel_with_executor(self, file_keys, workers, function):
        if self.function_belongs_to_a_pipeline_object(function):
            function = self.make_picklable_copy_of_function(function)
            with ProcessPoolExecutor(max_workers=workers) as executor:
                results = executor.map(function, *file_keys)
        return results

def find_border(max_con,shape):
    mask = np.zeros(shape)
    mask = cv2.fillPoly(mask, pts =[max_con.reshape(-1,1,2)], color=(255,255,255))
    kernel   = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (100,100))
    morphed  = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    kernel   = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (50,50))
    eroded  = cv2.morphologyEx(mask, cv2.MORPH_ERODE, kernel)
    return morphed-eroded