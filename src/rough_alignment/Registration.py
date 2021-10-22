import SimpleITK as sitk
from math import floor
from rough_alignment.RegistrationStatusReport import RegistrationStatusReport
from rough_alignment.SitkIOs import SitkIOs
from rough_alignment.ApplyTransform import ApplyTransform
class Registration:

    def __init__(self):
        """init_regerstration_method [creates the ImageRegistrationMethod object with default linear interpolator]
        """
        self.registration_method = sitk.ImageRegistrationMethod()
        self.registration_method.SetInterpolator(sitk.sitkLinear)
        self.status_reporter = RegistrationStatusReport(self.registration_method)
        self.fixed_image = None
        self.moving_image = None
        self.transform = None
        self.io = SitkIOs()
        self.applier = ApplyTransform(sitk.Transform(3, sitk.sitkIdentity))
        self.transformation_type = sitk.Transform(3, sitk.sitkIdentity)
    
    def load_fixed_image_from_np_array(self,np_array):
        self.fixed_image = self.io.array_to_image(np_array)

    def load_moving_image_from_np_array(self,np_array):
        self.moving_image = self.io.array_to_image(np_array)

    def load_fixed_image_from_directory(self,fix_image_dir):
        self.fixed_image = self.io.load_image_from_directory(fix_image_dir)
    
    def load_moving_image_from_directory(self,moving_image_dir):
        self.moving_image = self.io.load_image_from_directory(moving_image_dir)

    def set_initial_transformation(self):
        """set_centering_transform_as_initial_starting_point [alignes the center of two images stacks as an initial starting point for registeration]
        :param centering_transform: [transformation to center the images]
        :type centering_transform: [sitk transformation object]
        """
        self.transform = sitk.CenteredTransformInitializer(
            self.fixed_image, self.moving_image,
            self.transformation_type,
            sitk.CenteredTransformInitializerFilter.GEOMETRY)
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
    
    def set_optimizer_as_gradient_descent(self,parameters):
        """set_optimizer [configure gradient descent as the optimizer of the registration process]
        """
        self.registration_method.SetOptimizerAsGradientDescent(**parameters)
        self.registration_method.SetOptimizerScalesFromPhysicalShift()

    def set_mutual_information_as_similarity_metrics(self,numberOfHistogramBins=50,
                samping_percentage = 0.01):
        """set_mutual_information_as_similarity_metic [configure mututal information as the similarity metric of the registration process]
        """
        self.registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=
                numberOfHistogramBins)
        self.registration_method.SetMetricSamplingStrategy(self.registration_method.RANDOM)
        self.registration_method.SetMetricSamplingPercentage(samping_percentage)
    
    def set_least_squares_as_similarity_metrics(self,samping_percentage = 0.01):
        self.registration_method.SetMetricAsMeanSquares()
        self.registration_method.SetMetricSamplingStrategy(self.registration_method.RANDOM)
        self.registration_method.SetMetricSamplingPercentage(samping_percentage)
            
    def get_transform(self):
        return self.transform
    
    def register_with_defaults(self,gradient_descent_setting = None):
        if gradient_descent_setting == None:
            gradient_descent_setting = dict(
                learningRate=0.0001,
                numberOfIterations=1000,
                convergenceMinimumValue=1e-8,
                convergenceWindowSize=10)
        self.set_mutual_information_as_similarity_metrics()
        self.set_optimizer_as_gradient_descent(gradient_descent_setting)
        self.set_multi_resolution_parameters()
        self.status_reporter.set_report_events()
        self.set_initial_transformation()
        self.registration_method.Execute(self.fixed_image, self.moving_image)
        self.applier.transform = self.transform