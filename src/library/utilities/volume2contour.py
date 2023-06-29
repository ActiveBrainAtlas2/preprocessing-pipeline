import numpy as np
import cv2


class VolumeToContour:

    def volume_to_contours(self,volume):
        nsections = volume.shape[2]
        all_contours = []
        for sectioni in range(nsections):
            mask = volume[:,:,sectioni]
            mask = np.array(mask*255).astype('uint8')
            mask = np.pad(mask,[1,1])
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
    
    def add_contours_to_database(self,contours,origins,prep_id = 'Atlas',user_id = 34,input_type = 1):
        polygon_id = 54
        controller = SqlController(prep_id)
        for str in contours.keys():
            polygons = contours[str]
            print(str)
            origin = origins[str] -1
            volume_id = controller.get_new_segment_id()
            if not controller.annotation_points_row_exists(prep_id, user_id, input_type, polygon_id, str):
                try: 
                    for polygoni in polygons:
                        polygon_points = (polygoni+origin)*np.array([10,10,20])
                        polygon_id = controller.get_new_segment_id()
                        for pointi in polygon_points:
                                controller.add_annotation_point_row(f'Atlas',user_id,input_type,pointi,polygon_id,str,ordering=0,polygon_id=polygon_id,volume_id = volume_id)
                except:
                    print(str)
    
    def rotate_volume(self, volume):
        pass

def distance_transform(image):
    image = np.array(image).astype(np.uint8)
    return cv2.distanceTransform(image, cv2.DIST_L2, 5)

def average_masks(mask1, mask2):
    d1 = distance_transform(mask1) - distance_transform(np.logical_not(mask1));   
    d2 = distance_transform(mask2) - distance_transform(np.logical_not(mask2));   
    d1 = d1.astype(np.float64)
    d2 = d2.astype(np.float64)
    return (d1+d2) > 0; 