import toolbox.rough_alignment.sitk.registration_method_util as regutil
def get_affine_transform(fixed_image, moving_image, transform):
    """get_affine_transform [using the registeration framework to find the best Affine transformation that alignes two sitk image ]

    :param fixed_image: [image stack of fixed brain]
    :type fixed_image: [sitk image object]
    :param moving_image: [image stack of moving brain]
    :type moving_image: [sitk image object]
    :param transform: [initial transformation to roughly align the images]
    :type transform: [sitk transform]
    :return: [Affine transformation from fixed brain to the moving brain]
    :rtype: [sitk transform]
    """
    registration_method = regutil.init_regerstration_method()
    set_mutual_information_as_similarity_metrics(registration_method)
    set_optimizer_as_gradient_descent(registration_method)
    transform = regutil.set_centering_transform_as_initial_starting_point(registration_method, transform)
    regutil.set_multi_resolution_parameters(registration_method)
    regutil.set_report_events(registration_method)
    registration_method.Execute(fixed_image, moving_image)
    return transform

def set_optimizer_as_gradient_descent(registration_method):
    """set_optimizer [configure gradient descent as the optimizer of the registration process]

    :param registration_method: [ImageRegistrationMethod object of sitk]
    :type registration_method: [sitk ImageRegistrationMethod]
    """
    registration_method.SetOptimizerAsGradientDescent(
        learningRate=1.0,
        numberOfIterations=100,
        convergenceMinimumValue=1e-6,
        convergenceWindowSize=10
    )
    registration_method.SetOptimizerScalesFromPhysicalShift()

def set_mutual_information_as_similarity_metrics(registration_method):
    """set_mutual_information_as_similarity_metic [configure mututal information as the similarity metric of the registration process]

    :param registration_method: [description]
    :type registration_method: [type]
    """
    registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
    registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
    registration_method.SetMetricSamplingPercentage(0.01)