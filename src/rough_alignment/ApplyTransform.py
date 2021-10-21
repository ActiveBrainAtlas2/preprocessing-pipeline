import SimpleITK as sitk
import numpy as np
from rough_alignment.SitkIOs import SitkIOs
class ApplyTransform:

    def __init__(self,transform):
        self.transform = transform
        self.io = SitkIOs()
    
    def transform_and_resample(self,image_to_transform,image_for_resampling):
        transformed_image = sitk.Resample(image_to_transform, image_for_resampling, self.transform,
            sitk.sitkLinear, 0.0, image_to_transform.GetPixelID())
        return transformed_image

    def transform_image(self,image):
        transformed_image = sitk.Resample(image, image, self.transform,
            sitk.sitkLinear, 0.0, image.GetPixelID())
        return transformed_image

    def transform_and_resample_np_array(self,array_to_transform,array_to_resample):
        image_to_transform = self.io.array_to_image(array_to_transform)
        image_to_resample = self.io.array_to_image(array_to_resample)
        transformed_image = self.transform_and_resample(image_to_transform,image_to_resample)
        return sitk.GetArrayFromImage(transformed_image)

    def transform_np_array(self,array):
        image = self.io.array_to_image(array)
        image = self.transform_image(image)
        return sitk.GetArrayFromImage(image)
    
    def inverse_transform_points(self,points):
        _ = self.get_inverse_transform()
        transformed_points = self.transform_points(points,self.inverse_transform.TransformPoint)
        return transformed_points
    
    def forward_transform_points(self,points):
        _ = self.get_transform()
        transformed_points = self.transform_points(points,self.transform.TransformPoint)
        return transformed_points

    def transform_points(self,points,transform_function):
        """Transform a set of points according to a given transformation
        transform: and instance of SimpleITK.SimpleITK.Transform
        points: a numpy array of shape (number of points) X (number of dimensions)
        return moved: a numpy array of the same shape as points"""
        npoints,_=points.shape
        transformed_points=np.zeros(points.shape)
        for pointi in range(npoints):
            transformed_points[pointi]=transform_function(points[pointi,:])
        return transformed_points
    
    def get_transform(self):
        return self.transform
    
    def transform_boolean_array(self,boolean_array):
        postive_points = np.where(boolean_array)[0]
        transformed_points = []
        for point in postive_points:
            transformed = self.transform.TransformPoint(point)
            transformed_points.append(transformed)
        transformed_points = transformed_points - transformed_points.min(0)
        transformed_size = transformed 

    
    def get_inverse_transform(self):
        if not hasattr(self,'inverse_transform'):
            self.inverse_transform = self.transform.GetInverse()
        return self.inverse_transform
