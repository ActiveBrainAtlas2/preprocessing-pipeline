import numpy as np
import SimpleITK as sitk

class PointSetAlignment:
    def __init__(self,fixed,moving):
        self.fixed = np.array(fixed)
        self.moving = np.array(moving)
        self.transformation_type = sitk.Transform(3, sitk.sitkIdentity)
    
    def get_transfrom(self):
        if not hasattr(self, 'transform'):
            self.transform = sitk.LandmarkBasedTransformInitializer(self.transformation_type,
                list(self.fixed.flatten()),list(self.moving.flatten()))
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

class RigidPointSetAlignment(PointSetAlignment):
    def __init__(self, fixed, moving):
        super().__init__(fixed,moving)
        self.transformation_type = sitk.VersorRigid3DTransform()

class AffinePointSetAlignment(PointSetAlignment):
    def __init__(self, fixed, moving):
        super().__init__(fixed,moving)
        self.transformation_type = sitk.AffineTransform(3)

def get_shared_key_and_array(fixed_dictionary,moving_dictionary):
    shared_keys = set(fixed_dictionary.keys()).intersection(set(moving_dictionary.keys()))
    fixed = np.array([fixed_dictionary[key] for key in shared_keys])
    moving = np.array([moving_dictionary[key] for key in shared_keys])
    return fixed,moving,shared_keys

def get_rigid_alignmented_points(fixed_dictionary,moving_dictionary):
    fixed,moving,shared_keys = get_shared_key_and_array(fixed_dictionary,moving_dictionary)
    rigid = RigidPointSetAlignment(fixed, moving)
    transformed_point = rigid.get_transformed_point()
    return dict(zip(shared_keys,transformed_point))

def get_affine_alignment_points(fixed_dictionary,moving_dictionary):
    fixed,moving,shared_keys = get_shared_key_and_array(fixed_dictionary,moving_dictionary)
    affine = AffinePointSetAlignment(fixed, moving)
    transformed_point = affine.get_transformed_point()
    return dict(zip(shared_keys,transformed_point))