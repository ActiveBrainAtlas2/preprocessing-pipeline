import SimpleITK as sitk
from math import floor
from notebooks.Will.toolbox.rough_alignment.sitk.optimization_status_report_functions import *

def init_regerstration_method():
    """init_regerstration_method [creates the ImageRegistrationMethod object and setting the interpolator as linear]

    :return: [ImageRegistrationMethod object]
    :rtype: [sitk ImageRegistrationMethod object]
    """
    registration_method = sitk.ImageRegistrationMethod()
    registration_method.SetInterpolator(sitk.sitkLinear)
    return registration_method

def set_centering_transform_as_initial_starting_point(registration_method, centering_transform):
    """set_centering_transform_as_initial_starting_point [alignes the center of two images stacks as an initial starting point for registeration]

    :param registration_method: [sitk ImageRegistrationMethod object]
    :type registration_method: [sitk ImageRegistrationMethod object]
    :param centering_transform: [transformation to center the images]
    :type centering_transform: [sitk transformation object]
    :return: [description]
    :rtype: [type]
    """
    initial_transform = sitk.AffineTransform(centering_transform)
    registration_method.SetInitialTransform(initial_transform)
    return initial_transform

def set_multi_resolution_parameters(registration_method,shrinkFactors=[4, 2, 1]):
    """set_multi_resolution_parameters [configure options for multi-resolotion events registeration would happen at each resolution level]

    :param registration_method: [sitk ImageRegistrationMethod object]
    :type registration_method: [sitk ImageRegistrationMethod object]
    :param shrinkFactors: [down sampling factors for multi-resolution events], defaults to [4, 2, 1]
    :type shrinkFactors: list, optional
    """
    registration_method.SetShrinkFactorsPerLevel(shrinkFactors=shrinkFactors)
    smoothingSigmas = [floor(factori/2) for factori in shrinkFactors]
    registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=smoothingSigmas)
    registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()

def set_report_events(registration_method):
    """set_report_events [sets the events for reporting the status of the registeration]

    :param registration_method: [sitk ImageRegistrationMethod object]
    :type registration_method: [sitk ImageRegistrationMethod object]
    """
    registration_method.AddCommand(sitk.sitkStartEvent, start_optimization)
    registration_method.AddCommand(sitk.sitkIterationEvent, lambda: print_values(registration_method))
    registration_method.AddCommand(sitk.sitkMultiResolutionIterationEvent, report_multi_resolution_events)