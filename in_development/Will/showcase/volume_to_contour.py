import numpy as np
import sys
sys.path.append('/scratch/programming/preprocessing-pipeline/src')
import cv2
import matplotlib.pyplot as plt
from lib.sqlcontroller import SqlController
from scipy.ndimage.measurements import center_of_mass
from abakit.atlas.Assembler import get_v7_volume_and_origin
controller = SqlController('Atlas')
volumes,origins = get_v7_volume_and_origin(side = '_L')
def volume_to_contours(volume):
    # volume = volume > 0.8
    nsections = volume.shape[2]
    all_contours = []
    for sectioni in range(nsections):
        mask = volume[:,:,sectioni]
        mask = np.array(mask*255).astype('uint8')
        mask = np.pad(mask,[1,1])
        # mask = np.flipud(mask)
        # mask = np.fliplr(mask)
        # mask = np.rot90(mask,3)
        mask = mask.T
        _, thresh = cv2.threshold(mask, 200, 255, 0)
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) ==1: 
            contours = contours[0].reshape(-1,2) -1
            contours = np.hstack((contours,np.ones(len(contours)).reshape(-1,1)*sectioni))
            all_contours.append(contours)
        elif len(contours) >1: 
            id = np.argmax([len(i) for i in contours])
            all_contours.append(contours[id])
    return all_contours
contours = {}
for structure,volume in volumes.items():
    # print(structure)
    contours[structure] = volume_to_contours(volume)

for str in contours.keys():
    polygons = contours[str]
    print(str)
    origin = origins[str] -1
    volume_id = controller.get_new_segment_id()
    if not controller.annotation_points_row_exists('Atlas', 34, 1, 54, str):
        try: 
            for polygoni in polygons:
                polygon_points = (polygoni+origin)*np.array([10,10,20])
                polygon_id = controller.get_new_segment_id()
                for pointi in polygon_points:
                        controller.add_annotation_point_row(f'Atlas',34,1,pointi,54,str,ordering=0,polygon_id=polygon_id,volume_id = volume_id)
        except:
            print(str)
print('done')
