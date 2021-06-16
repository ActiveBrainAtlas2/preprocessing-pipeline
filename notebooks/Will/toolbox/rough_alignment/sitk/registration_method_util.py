import SimpleITK as sitk
from math import floor

def init_regerstration_method():
    registration_method = sitk.ImageRegistrationMethod()
    registration_method.SetInterpolator(sitk.sitkLinear)
    return registration_method

def set_centering_transform_as_initial_starting_point(registration_method, centering_transform):
    affine_transform = sitk.AffineTransform(centering_transform)
    registration_method.SetInitialTransform(affine_transform)
    return affine_transform

def set_multi_resolution_parameters(registration_method,shrinkFactors=[4, 2, 1]):
    registration_method.SetShrinkFactorsPerLevel(shrinkFactors=shrinkFactors)
    smoothingSigmas = [floor(factori/2) for factori in shrinkFactors]
    registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=smoothingSigmas)
    registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()

def set_report_events(registration_method):
    registration_method.AddCommand(sitk.sitkStartEvent, start_optimization)
    registration_method.AddCommand(sitk.sitkIterationEvent, lambda: print_values(registration_method))
    registration_method.AddCommand(sitk.sitkMultiResolutionIterationEvent, report_multi_resolution_events)