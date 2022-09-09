import numpy as np
import SimpleITK as sitk

class Registration:
    def __init__(self):
        self.fixed = None
        self.moving = None
        self.transformation_type = sitk.Transform(3, sitk.sitkIdentity)
    
    def calculate_transform(self):
        raise NotADirectoryError()

    def get_transform(self):
        if not hasattr(self, 'transform'):
            self.calculate_transform()
        return self.transform

    def get_inverse_transform(self):
        self.get_transform()
        self.inverse_transform = self.transform.GetInverse()
        return self.inverse_transform
    
    def transform_dictionary(self,point_dictionary):
        keys = point_dictionary.keys()
        values = np.array(list(point_dictionary.values()))
        transformed = self.transform_points(values)
        return dict(zip(keys,transformed))
    
    def inverse_transform_dictionary(self,point_dictionary):
        keys = point_dictionary.keys()
        values = np.array(list(point_dictionary.values()))
        transformed = self.inverse_transform_points(values)
        return dict(zip(keys,transformed))

    def transform_points(self,points):
        self.get_inverse_transform()
        transformed=np.zeros(points.shape)
        for i in range(points.shape[0]):
            transformed[i]=self.inverse_transform.TransformPoint(points[i,:])
        return transformed
    
    def inverse_transform_points(self,points):
        self.get_transform()
        transformed=np.zeros(points.shape)
        for i in range(points.shape[0]):
            transformed[i]=self.transform.TransformPoint(points[i,:])
        return transformed
    
    def get_transformed_moving_point(self):
        return self.transform_points(self.moving)