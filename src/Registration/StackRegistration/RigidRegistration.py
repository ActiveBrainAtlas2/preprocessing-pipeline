import SimpleITK as sitk
from rough_alignment.Registration import ImageToImageRegistration

class RigidRegistration(ImageToImageRegistration):

    def __init__(self):
        super().__init__()
        self.transformation_type = sitk.Euler3DTransform()

    def calculate_rigid_transform(self,gradient_descent_setting = None):
        self.register_with_defaults(gradient_descent_setting)