import SimpleITK as sitk
import numpy as np
from scipy.ndimage.interpolation import affine_transform

class Transformation:

    def __init__(self,fixed,moving):
        self.fixed = fixed
        self.moving = moving

    def transform_moving_image(self):
        self.transformed_moving = sitk.Resample(self.moving, self.fixed, affine_transform,
            sitk.sitkLinear, 0.0, self.moving.GetPixelID())
    
    def inverse_transform_points(self,points):
        _ = self.get_inverse_transform()
        transformed_points = self.transform_points(points,self.inverse_transform.TransformPoint)
        return transformed_points
    
    def forward_transform_points(self,points):
        _ = self.get_transform()
        transformed_points = self.transform_points(points,self.transform.TransformPoint)
        return transformed_points

    def transform_points(self,points,tranform_function):
        """Transform a set of points according to a given transformation
        transform: and instance of SimpleITK.SimpleITK.Transform
        points: a numpy array of shape (number of points) X (number of dimensions)
        return moved: a numpy array of the same shape as points"""
        npoints,_=points.shape
        transformed_points=np.zeros(points.shape)
        for pointi in range(npoints):
            transformed_points[pointi]=tranform_function(points[pointi,:])
        return transformed_points
    
    def get_transform(self):
        if not hasattr(self,'transform'):
            self.transform = sitk.LandmarkBasedTransformInitializer(self.transform_type,
            list(self.fixed.flatten()),list(self.moving.flatten()))
            self.inverse_transform = self.transform.GetInverse()
        return self.transform
    
    def get_inverse_transform(self):
        if not hasattr(self,'transform'):
            _ = self.get_transform()
        if not hasattr(self,'inverse_transform'):
            self.inverse_transform = self.transform.GetInverse()
        return self.inverse_transform
    
    def get_fixed_image(self):
        sitk.GetArrayFromImage(self.fixed)

    def get_moving_image(self):
        sitk.GetArrayFromImage(self.moving)
    
    def get_transformed_moving_image(self):
        assert(hasattr(self,'transform_moving_image'))
        sitk.GetArrayFromImage(self.transform_moving_image)

class AffineTransform(Transformation):
    def __init__(self,fixed,moving):
        super(AffineTransform, self).__init__(fixed,moving)
        self.transform_type = sitk.AffineTransform(3)

class RigidTransform(Transformation):
    def __init__(self,fixed,moving):
        super(RigidTransform, self).__init__(fixed,moving)
        self.transform_type = sitk.VersorRigid3DTransform()
