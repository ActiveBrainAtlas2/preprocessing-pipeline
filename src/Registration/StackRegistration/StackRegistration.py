import SimpleITK as sitk
from math import floor
from Registration.StackRegistration.RegistrationStatusReport import RegistrationStatusReport
from Registration.StackRegistration.SitkIOs import SitkIOs
from Registration.StackRegistration.ApplyTransform import ApplyTransform
from Registration.Registration import Registration

class StackRegistration(Registration):

    def __init__(self):
        """init_regerstration_method [creates the ImageRegistrationMethod object with default linear interpolator]
        """
        super().__init__()
        self.registration_method = sitk.ImageRegistrationMethod()
        self.registration_method.SetInterpolator(sitk.sitkLinear)
        self.status_reporter = RegistrationStatusReport(self.registration_method)
        self.io = SitkIOs()
        self.applier = ApplyTransform(sitk.Transform(3, sitk.sitkIdentity))
    
    def load_fixed_image_from_np_array(self,np_array):
        self.fixed = self.io.array_to_image(np_array)

    def load_moving_image_from_np_array(self,np_array):
        self.moving = self.io.array_to_image(np_array)

    def load_fixed_image_from_directory(self,fix_image_dir):
        self.fixed = self.io.load_image_from_directory(fix_image_dir)
    
    def load_moving_image_from_directory(self,moving_image_dir):
        self.moving = self.io.load_image_from_directory(moving_image_dir)

    def set_initial_transformation(self):
        """set_centering_transform_as_initial_starting_point [alignes the center of two images stacks as an initial starting point for registeration]
        :param centering_transform: [transformation to center the images]
        :type centering_transform: [sitk transformation object]
        """
        self.transform = sitk.CenteredTransformInitializer(
            self.fixed, self.moving,
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
        """ set_optimizer [configure gradient descent as the optimizer of the registration process]
            some optimizer parameters include:
            learningRate,
            numberOfIterations,
            convergenceMinimumValue,
            convergenceWindowSize
        """
        self.registration_method.SetOptimizerAsGradientDescent(**parameters)
        self.registration_method.SetOptimizerScalesFromPhysicalShift()

    def set_optimizer_as_regular_step_gradient_descent(self,parameters):
        """ set_optimizer [configure gradient descent as the optimizer of the registration process]
            some optimizer parameters include:
            learningRate,
            minStep,
            numberOfIterations, 
            relaxationFactor=0.5, 
            gradientMagnitudeTolerance=1e-4
        """
        self.registration_method.SetOptimizerAsRegularStepGradientDescent(**parameters)
        self.registration_method.SetOptimizerScalesFromPhysicalShift()

    def set_optimizer_as_gradient_descent_line_search(self,parameters):
        """set_optimizer [configure gradient descent as the optimizer of the registration process]
           some optimizer parameters include:
           learningRate,
           numberOfIterations,
           convergenceMinimumValue,
           convergenceWindowSize=10,
           lineSearchLowerLimit=0, 
           lineSearchUpperLimit=5.0, 
           lineSearchEpsilon=0.01, 
           lineSearchMaximumIterations=20
        """
        self.registration_method.SetOptimizerAsGradientDescentLineSearch(**parameters)
        self.registration_method.SetOptimizerScalesFromPhysicalShift()
    
    def set_optimizer_as_LBFGS2 (self,parameters):
        """set_optimizer [configure gradient descent as the optimizer of the registration process]
           some optimizer parameters include:
           solutionAccuracy=1e-5,
           numberOfIterations=0,
           hessianApproximateAccuracy=6, 
           deltaConvergenceDistance=0, 
           deltaConvergenceTolerance=1e-5, 
           lineSearchMaximumEvaluations=40, 
           lineSearchMinimumStep=1e-20, 
           lineSearchMaximumStep=1e20, 
           lineSearchAccuracy=1e-4
        """
        self.registration_method.SetOptimizerAsLBFGS2 (**parameters)
        self.registration_method.SetOptimizerScalesFromPhysicalShift()

    def set_mutual_information_as_similarity_metrics(self,numberOfHistogramBins=50,
                samping_percentage = 0.01):
        """set_mutual_information_as_similarity_metric [configure mututal information as the similarity metric of the registration process]
        """
        self.registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=
                numberOfHistogramBins)
        self.registration_method.SetMetricSamplingStrategy(self.registration_method.RANDOM)
        self.registration_method.SetMetricSamplingPercentage(samping_percentage)
    
    def set_least_squares_as_similarity_metrics(self,samping_percentage = 0.01):
        self.registration_method.SetMetricAsMeanSquares()
        self.registration_method.SetMetricSamplingStrategy(self.registration_method.RANDOM)
        self.registration_method.SetMetricSamplingPercentage(samping_percentage)
    
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
        self.registration_method.Execute(self.fixed, self.moving)
        self.applier.transform = self.transform