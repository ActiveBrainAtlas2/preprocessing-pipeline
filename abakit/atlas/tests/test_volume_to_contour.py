from util import get_test_origin_and_volume,get_test_contours_and_origin
from abakit.atlas.VolumeToContour import VolumeToContour
import numpy as np

def test_volume_to_contour():
    '''Tests the VolumeToContour class which turns a 3D mask to a set of contours. 
     The test create a mockup volume and checks if the correct contours are generated.'''
    converter = VolumeToContour()
    origin,volume = get_test_origin_and_volume()
    test_contours,test_origin = get_test_contours_and_origin()
    contours = converter.volume_to_contours(volume['test'])
    ncontours = len(contours)
    for i in range(ncontours):
        test_contour_points = np.array(test_contours['test'][i+test_origin[2]])-np.array(test_origin[:2])
        test_contour_points = np.hstack([test_contour_points,np.ones([len(test_contour_points),1])*i])
        answer_contour_points = contours[i]
        assert np.all([i in test_contour_points for i in answer_contour_points])
