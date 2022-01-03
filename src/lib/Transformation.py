import SimpleITK as sitk
from SimpleITK.SimpleITK import Transform
import numpy as np

class Transformation:

    def __init__(self,transform):
        self.transform = transform
    
    def inverse_transform_points(self,points):
        _ = self.get_inverse_transform()
        transformed_points = self.transform_points(points,self.inverse_transform.TransformPoint)
        return transformed_points
    
    def forward_transform_points(self,points):
        transformed_points = self.transform_points(points,self.transform.TransformPoint)
        return transformed_points

    def transform_points(self,points,tranform_function):
        """Transform a set of points according to a given transformation
        transform: and instance of SimpleITK.SimpleITK.Transform
        points: a numpy array of shape (number of points) X (number of dimensions)
        return moved: a numpy array of the same shape as points"""
        transpose = False
        if points.shape[1] != 3 and points.shape[0] == 3:
            points = points.T
            transpose = True
        npoints,_=points.shape
        transformed_points=np.zeros(points.shape)
        for pointi in range(npoints):
            transformed_points[pointi]=tranform_function(points[pointi,:])
        if transpose:
            transformed_points = transformed_points.T
        return transformed_points
    
    def get_inverse_transform(self):
        if not hasattr(self,'inverse_transform'):
            self.inverse_transform = self.transform.GetInverse()
        return self.inverse_transform