import SimpleITK as sitk
from rough_alignment.Registration import StackRegistration

class BSplineRegistration(StackRegistration):

    def __init__(self):
        super().__init__()

    def set_initial_transformation(self):
        transformDomainMeshSize=[2]*self.fixed.GetDimension()
        self.transform = sitk.BSplineTransformInitializer(self.fixed,
                                      transformDomainMeshSize )
        self.registration_method.SetInitialTransformAsBSpline(self.transform,
                               inPlace=True,
                               scaleFactors=[1,2,5])

    def calculate_default_bspline_transform(self,gradient_descent_setting = None):
        self.register_with_defaults(gradient_descent_setting)


