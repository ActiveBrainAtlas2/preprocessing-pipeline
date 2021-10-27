import numpy as np
import SimpleITK as sitk

class Registration:
    def __init__(self):
        self.fixed = None
        self.moving = None
        self.transformation_type = sitk.Transform(3, sitk.sitkIdentity)
    
    def get_transfrom(self):
        if not hasattr(self, 'transform'):
            raise NotImplementedError()
        return self.transform

    def get_inverse_transform(self):
        self.get_transfrom()
        self.inverse_transform = self.transform.GetInverse()
        return self.inverse_transform
    
    def get_transformed_point(self):
        """Transform a set of points according to a given transformation
            transform: and instance of SimpleITK.SimpleITK.Transform
            points: a numpy array of shape (number of points) X (number of dimensions)
            
            return moved: a numpy array of the same shape as points"""
        self.get_inverse_transform()
        n,m=self.moving.shape
        moved=np.zeros(self.moving.shape)
        for i in range(n):
            moved[i]=self.inverse_transform.TransformPoint(self.moving[i,:])
        return moved