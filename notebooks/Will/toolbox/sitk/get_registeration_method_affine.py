from notebooks.Will.toolbox.sitk.registration_method_util import *

def get_affine_transform(fixed_image, moving_image, transform):
    registration_method = init_regerstration_method()
    set_mutual_information_as_similarity_metic(registration_method)
    set_optimizer(registration_method)
    transform = set_centering_transform_as_initial_starting_point(registration_method, transform)
    set_multi_resolution_parameters(registration_method)
    set_report_events(registration_method)
    registration_method.Execute(fixed_image, moving_image)
    return transform

def set_optimizer(registration_method):
    registration_method.SetOptimizerAsGradientDescent(
        learningRate=1.0,
        numberOfIterations=100,
        convergenceMinimumValue=1e-6,
        convergenceWindowSize=10
    )
    registration_method.SetOptimizerScalesFromPhysicalShift()

def set_mutual_information_as_similarity_metic(registration_method):
    registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
    registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
    registration_method.SetMetricSamplingPercentage(0.01)