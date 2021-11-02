import SimpleITK as sitk
import numpy as np
from Registration.StackRegistration.SitkIOs import SitkIOs
class ApplyTransform:

    def __init__(self,transform):
        self.transform = transform
        self.io = SitkIOs()
    
    def transform_and_resample(self,image_to_transform,image_for_resampling):
        transformed_image = sitk.Resample(image_for_resampling, image_to_transform, self.transform,
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
    
    def transform_boolean_array(self,boolean_array):
        postive_points = np.where(boolean_array)[0]
        transformed_points = []
        for point in postive_points:
            transformed = self.transform.TransformPoint(point)
            transformed_points.append(transformed)
        transformed_points = transformed_points - transformed_points.min(0)
        transformed_size = transformed 