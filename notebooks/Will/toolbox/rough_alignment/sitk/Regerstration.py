import SimpleITK as sitk
from math import floor
from RegistrationStatusReport import RegistrationStatusReport
from SitkIOs import SitkIOs

class Registration:

    def __init__(self):
        """init_regerstration_method [creates the ImageRegistrationMethod object with default linear interpolator]
        """
        self.registration_method = sitk.ImageRegistrationMethod()
        self.registration_method.SetInterpolator(sitk.sitkLinear)
        self.status_reporter = RegistrationStatusReport()
        self.fixed_image = None
        self.moving_image = None
        self.transform = None
        self.io = SitkIOs()

    def load_fixed_image_from_directory(self,fix_image_dir):
        self.fixed_image = self.io.load_image(fix_image_dir)
    
    def load_moving_image_from_directory(self,moving_image_dir):
        self.moving_image = self.io.load_image(moving_image_dir)

    def set_initial_transformation(self, initial_transform):
        """set_centering_transform_as_initial_starting_point [alignes the center of two images stacks as an initial starting point for registeration]
        :param centering_transform: [transformation to center the images]
        :type centering_transform: [sitk transformation object]
        """
        self.transform = sitk.AffineTransform(initial_transform)
        self.registration_method.SetInitialTransform(self.transform)

    def set_multi_resolution_parameters(self,shrinkFactors=[4, 2, 1]):
        """set_multi_resolution_parameters [configure options for multi-resolotion events registeration would happen at each resolution level]

        :param shrinkFactors: [down sampling factors for multi-resolution events], defaults to [4, 2, 1]
        :type shrinkFactors: list, optional
        """
        self.registration_method.SetShrinkFactorsPerLevel(shrinkFactors=shrinkFactors)
        smoothingSigmas = [floor(factori/2) for factori in shrinkFactors]
        self.registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=smoothingSigmas)
        self.registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()
    
    def set_optimizer_as_gradient_descent(self):
        """set_optimizer [configure gradient descent as the optimizer of the registration process]
        """
        self.SetOptimizerAsGradientDescent(
            learningRate=1.0,
            numberOfIterations=100,
            convergenceMinimumValue=1e-6,
            convergenceWindowSize=10
        )
        self.SetOptimizerScalesFromPhysicalShift()

    def set_mutual_information_as_similarity_metrics(self):
        """set_mutual_information_as_similarity_metic [configure mututal information as the similarity metric of the registration process]
        """
        self.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
        self.SetMetricSamplingStrategy(self.RANDOM)
        self.SetMetricSamplingPercentage(0.01)
            
    def get_transform(self):
        return self.transform