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
import cv2
import numpy as np
from scipy.ndimage.measurements import center_of_mass

from abakit.atlas.volume2contour import average_masks

class VolumeMaker:

    def calculate_origin_and_volume_for_one_segment(self,segmenti,interpolate=0):
        segment_contours = self.aligned_contours[segmenti]
        segment_contours = self.sort_contours(segment_contours)
        origin,section_size = self.get_origin_and_section_size(segment_contours)
        volume = []
        for _, contour_points in segment_contours.items():
            vertices = np.array(contour_points) - origin[:2]
            contour_points = (vertices).astype(np.int32)
            volume_slice = np.zeros(section_size, dtype=np.uint8)
            volume_slice = cv2.polylines(volume_slice, [contour_points], isClosed=True, color=1, thickness=1)
            volume_slice = cv2.fillPoly(volume_slice, pts=[contour_points], color=1)
            volume.append(volume_slice)
        volume = np.array(volume).astype(np.bool8)
        volume = np.swapaxes(volume,0,2)
        for _ in range(interpolate):
            volume,origin = self.interpolate_volumes(volume,origin)
        self.origins[segmenti] = origin
        self.volumes[segmenti] = volume
    
    def get_origin_and_section_size(self,segment_contours):
        section_mins = []
        section_maxs = []
        for _, contour_points in segment_contours.items():
            contour_points = np.array(contour_points)
            section_mins.append(np.min(contour_points, axis=0))
            section_maxs.append(np.max(contour_points, axis=0))
        min_z = min([int(i) for i in segment_contours.keys()])
        min_x,min_y = np.min(section_mins, axis=0)
        max_x,max_y = np.max(section_maxs, axis=0)
        xspan = max_x - min_x
        yspan = max_y - min_y
        origin = np.array([min_x,min_y,min_z])
        size = np.array([xspan,yspan]).astype(int)+5
        return origin,size

    def compute_origins_and_volumes_for_all_segments(self,interpolate=0):
        self.origins = {}
        self.volumes = {}
        self.segments = self.aligned_contours.keys()
        for segmenti in self.segments:
            self.calculate_origin_and_volume_for_one_segment(segmenti,interpolate=interpolate)
    
    def get_COM_in_pixels(self,structurei):
        com = np.array(center_of_mass(self.volumes[structurei]))
        return (com+self.origins[structurei])
    
    def sort_contours(self,contour_for_segmenti):
        sections = [int(section) for section in contour_for_segmenti]
        section_order = np.argsort(sections)
        keys = np.array(list(contour_for_segmenti.keys()))[section_order]
        values = np.array(list(contour_for_segmenti.values()), dtype=object)[section_order]
        return dict(zip(keys,values))

    def set_aligned_contours(self,contours):
        self.aligned_contours = contours
        self.structures = list(self.aligned_contours.keys())  
    
    def interpolate_volumes(self,volume,origin):
        nsections = volume.shape[2]
        origin = np.array(origin)
        origin = origin*np.array([1,1,2])
        interpolated = np.zeros((volume.shape[0],volume.shape[1],2*nsections))
        for sectioni in range(nsections):
            interpolated[:,:,sectioni*2] = volume[:,:,sectioni]
            if sectioni > 0:
                next = interpolated[:,:,sectioni*2]
                last = interpolated[:,:,sectioni*2-2]
                interpolated[:,:,sectioni*2-1] = average_masks(next,last)
        return interpolated,origin