#%%
import numpy as np
import sys
sys.path.append('/scratch/programming/preprocessing-pipeline/src')
from atlas.Atlas import Atlas
import cv2
import matplotlib.pyplot as plt
from lib.sqlcontroller import SqlController
controller = SqlController('DK39')

atlas = Atlas(atlas = 'atlasV7')
atlas.load_volumes()
atlas.load_com()
atlas.convert_unit_of_com_dictionary(atlas.COM, atlas.fixed_brain.um_to_pixel)
atlas.origins = atlas.get_origin_from_coms()
structure,volume = list(atlas.volumes.items())[0]
# %%
def volume_to_contours(volume):
    volume = volume > np.quantile(volume,0.95)
    nsections = volume.shape[2]
    all_contours = []
    for sectioni in range(nsections):
        mask = volume[:,:,sectioni]
        mask = np.array(mask*255).astype('uint8')
        _, thresh = cv2.threshold(mask, 200, 255, 0)
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        assert len(contours)<=1
        if len(contours) ==1: 
            contours = contours[0].reshape(-1,2)
            contours = np.hstack((contours,np.ones(len(contours)).reshape(-1,1)*sectioni))
            all_contours.append(contours)
    return all_contours

# %%
contours = {}
for structure,volume in atlas.volumes.items():
    print(structure)
    contours[structure] = volume_to_contours(volume)
# %%
for str,polygons in contours.items():
    print(str)
    origin = atlas.origins[str]
    for polygoni in polygons:
        polygon_points = (polygoni+origin)*atlas.fixed_brain.pixel_to_um
        segment_id = controller.get_new_segment_id()
        for pointi in polygon_points:
            controller.add_annotation_point_row('Atlas',34,1,pointi,54,str,ordering=0,segment_id=segment_id)
print('done')
# %%
