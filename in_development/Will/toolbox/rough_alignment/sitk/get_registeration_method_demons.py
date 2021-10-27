import SimpleITK as sitk
from notebooks.Will.toolbox.rough_alignment.sitk.registration_method_util import *

def get_demons_transform(fixed_image, moving_image, transform):
    registration_method = init_regerstration_method()
    set_default_demons_simiparity_metric(registration_method)
    set_optimizer(registration_method)
    initial_demons_transform = get_initial_demons_transform(fixed_image,transform)
    registration_method.SetInitialTransform(initial_demons_transform)
    set_multi_resolution_parameters(registration_method,shrinkFactors=[4])
    set_report_events(registration_method)
    registration_method.Execute(fixed_image, moving_image)
    return initial_demons_transform

def set_default_demons_simiparity_metric(registration_method):
    registration_method.SetMetricAsDemons(10)

def set_optimizer(registration_method):
    registration_method.SetOptimizerAsGradientDescent(
        learningRate=1.0,
        numberOfIterations=100,
        convergenceMinimumValue=1e-6,
        convergenceWindowSize=10
    )
    registration_method.SetOptimizerScalesFromPhysicalShift()

def get_initial_demons_transform(fixed_image,affine_transform):
    transform_to_displacment_field_filter = sitk.TransformToDisplacementFieldFilter()
    transform_to_displacment_field_filter.SetReferenceImage(fixed_image)
    demons_transform = sitk.DisplacementFieldTransform(transform_to_displacment_field_filter.Execute(affine_transform))
    demons_transform.SetSmoothingGaussianOnUpdate(
        varianceForUpdateField=0.0,
        varianceForTotalField=2.0
    )
    return demons_transform
