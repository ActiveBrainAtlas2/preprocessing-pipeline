import SimpleITK as sitk
from rough_alignment.Registration import Registration

class AffineRegistration(Registration):

    def __init__(self):
        super().__init__()
        self.transformation_type = sitk.AffineTransform(3)

    def calculate_affine_transform(self,gradient_descent_setting = None):
        self.register_with_defaults(gradient_descent_setting)

