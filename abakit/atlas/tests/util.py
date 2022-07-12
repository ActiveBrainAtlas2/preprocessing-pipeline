from abakit.atlas.VolumeMaker import VolumeMaker
import numpy as np
def get_test_volume_maker():
    '''Creates a VolumeMaker Instance that contains the test contour and creates the volumes'''
    test_contours,_= get_test_contours_and_origin()
    maker = VolumeMaker('DK55')
    maker.set_aligned_contours(test_contours)
    maker.compute_COMs_origins_and_volumes()
    return maker

def get_test_origin_and_volume():
    '''returns 3d mask and origin that is created by the VolumeMaker class'''
    maker = get_test_volume_maker()
    return maker.origins,maker.volumes

def get_correct_test_volume():
    '''returns 3d mask that should be created from the contours'''
    test_volume = np.zeros([8,8,2])==1
    test_volume[:3,:3,0] = True
    test_volume[1:4,1:4,1] = True
    return test_volume

def get_test_contours_and_origin():
    '''returns the test contours'''
    contours = {}
    contours[1] = [[1,3],[3,3],[3,1],[1,1]]
    contours[2] = [[2,4],[4,4],[4,2],[2,2]]
    origin = [1,1,1]
    return {'test':contours},origin