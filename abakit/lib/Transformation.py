import SimpleITK as sitk
import numpy as np
from copy import copy
class Transformation:
    """a wrapper around sitk transformations to transform point sets
    """
    #TODO this does not work with the affine transformation type right now.  Sitk objects are hard to pickle, the method 
    # we have right now circumvent this for the rigid transformation but not for affine
    def __init__(self,fixed_and_regular_parameters,type):
        self.fixed_and_regular_parameters = fixed_and_regular_parameters
        self.type = type
    
    def inverse_transform_points(self,points):
        """inverse transform a set of points

        Args:
            points (array like): list pf x,y,z coordinate

        Returns:
            array like: list of transformed x,y,z coordinates
        """        
        self.create_inverse_transform()
        transformed_points = self.transform_points(points,self.inverse_transform.TransformPoint)
        return transformed_points
    
    def forward_transform_points(self,points):
        """Forward transforms the points

        Args:
            points (array like): list of x,y,z, coordinates

        Returns:
            array like: list of x,t,z coordinate after forward transformation
        """        
        self.create_transform()
        transformed_points = self.transform_points(points,self.transform.TransformPoint)
        return transformed_points

    def transform_points(self,points,tranform_function):
        """Transform a set of points according to a given transformation
        transform: and instance of SimpleITK.SimpleITK.Transform
        points: a numpy array of shape (number of points) X (number of dimensions)
        return moved: a numpy array of the same shape as points"""
        points = np.array(points)
        self.create_transform()
        transpose = False
        if points.shape[1] != 3 and points.shape[0] == 3:
            points = points.T
            transpose = True
        npoints,_=points.shape
        transformed_points=np.zeros(points.shape)
        for pointi in range(npoints):
            transformed_points[pointi]=tranform_function(points[pointi,:].tolist())
        if transpose:
            transformed_points = transformed_points.T
        return transformed_points
    
    def create_inverse_transform(self):
        """create the inverse transform as needed from the forward transform

        Returns:
            sitk transform: the inverse transform
        """        
        self.create_transform()
        if not hasattr(self,'inverse_transform'):
            self.inverse_transform = self.transform.GetInverse()
        return self.inverse_transform
    
    def create_transform(self):
        """create the transformation as needed from the fixed and regular parameters.
           this is needed as sitk does not play nicely with pickling
        """        
        if not hasattr(self,'transform'):
            self.transform = eval(self.type)
            self.transform.SetFixedParameters(self.fixed_and_regular_parameters[0])
            self.transform.SetParameters(self.fixed_and_regular_parameters[1])
    
    def forward_transform_volume(self,volume,downsample_factor = 1):
        self.create_transform()
        volume = self.transform_volume(volume,self.transform,downsample_factor)
        return volume
    
    def inverse_transform_volume(self,volume,downsample_factor = 1):
        self.create_inverse_transform()
        volume = self.transform_volume(volume,self.inverse_transform,downsample_factor)
        return volume        
    
    def transform_volume(self,volume,itk_tranform_object,downsample_factor = 1):
        volume = copy(volume)
        structures = list(volume.origins.keys())
        for structurei in structures:
            origini = np.array(volume.origins[structurei])*downsample_factor
            # volumei = volume.volumes[structurei]
            volume.origins[structurei] = np.array(itk_tranform_object.TransformPoint(origini))/downsample_factor
            # volume.volumes[structurei] = self.transform_np_array(volumei,itk_tranform_object)
        return volume
    
    def transform_np_array(self,volume, transform):
        volume = sitk.GetImageFromArray(volume)
        reference_image = volume
        interpolator = sitk.sitkCosineWindowedSinc
        default_value = 100.0
        volume =  sitk.Resample(volume, reference_image, transform,
                            interpolator, default_value)
        volume = sitk.GetArrayFromImage(volume)
        return volume