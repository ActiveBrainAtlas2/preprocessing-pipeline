"""
This gets the CSV data of the 3 foundation brains' annotations.
These annotations were done by Lauren, Beth, Yuncong and Harvey
(i'm not positive about this)
The annotations are full scale vertices.

This code takes the contours and does the following:
1. create 3d volumn from the contours
2. find the center of mass
3. saving COMs in the database, saving COM and volumns in the file system
"""
import os
import sys
import cv2
import numpy as np
from tqdm import tqdm
from scipy.ndimage.measurements import center_of_mass
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility/src')
sys.path.append(PATH)
DOWNSAMPLE_FACTOR = 32
from atlas.BrainStructureManager import BrainStructureManager

class VolumeMaker(BrainStructureManager):
    def __init__(self,animal):
        super().__init__(animal)

    def calculate_origin_COM_and_volume(self,contour_for_structurei,structurei):
        section_mins = []
        section_maxs = []
        for _, contour_points in contour_for_structurei.items():
            contour_points = np.array(contour_points)
            section_mins.append(np.min(contour_points, axis=0))
            section_maxs.append(np.max(contour_points, axis=0))
        min_z = min([int(i) for i in contour_for_structurei.keys()])
        min_x,min_y = np.min(section_mins, axis=0)
        max_x,max_y = np.max(section_maxs, axis=0)
        xspan = max_x - min_x
        yspan = max_y - min_y
        PADDED_SIZE = (int(yspan+5), int(xspan+5))
        volume = []
        for _, contour_points in sorted(contour_for_structurei.items()):
            vertices = np.array(contour_points) - np.array((min_x, min_y))
            contour_points = (vertices).astype(np.int32)
            volume_slice = np.zeros(PADDED_SIZE, dtype=np.uint8)
            volume_slice = cv2.polylines(volume_slice, [contour_points], isClosed=True, color=1, thickness=1)
            volume_slice = cv2.fillPoly(volume_slice, pts=[contour_points], color=1)
            volume.append(volume_slice)
        volume = np.array(volume).astype(np.bool8)
        volume = np.swapaxes(volume,0,2)
        to_um = 32 * self.get_resolution()
        com = np.array(center_of_mass(volume))
        self.COM[structurei] = (com+np.array((min_x,min_y,min_z)))*np.array([to_um,to_um,20])
        self.origins[structurei] = np.array((min_x,min_y,min_z))
        self.volumes[structurei] = volume

    def compute_COMs_origins_and_volumes(self):
        self.load_aligned_contours()
        for structurei in tqdm(self.structures):
            contours_of_structurei = self.aligned_contours[structurei]
            self.calculate_origin_COM_and_volume(contours_of_structurei,structurei)
        
    def show_steps(self):
        # self.compare_point_dictionaries([self.COM,self.origins])
        self.plot_volume_stack()
    


if __name__ == '__main__':
    animals = ['MD585', 'MD589', 'MD594']
    for animal in animals:
        volumemaker = VolumeMaker(animal)
        volumemaker.compute_COMs_origins_and_volumes()
        volumemaker.show_steps()
        volumemaker.save_coms()
        volumemaker.save_origins()
        volumemaker.save_volumes()