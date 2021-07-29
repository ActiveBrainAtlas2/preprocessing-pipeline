"""

 #Notes from the manual regarding MOMENTS vs GEOMETRY:

 The CenteredTransformInitializer supports two modes of operation. In the first mode, the centers of
 the images are computed as space coordinates using the image origin, size and spacing. The center of
 the fixed image is assigned as the rotational center of the transform while the vector going from the
 fixed image center to the moving image center is passed as the initial translation of the transform.
 In the second mode, the image centers are not computed geometrically but by using the moments of the
 intensity gray levels.

 Keep in mind that the scale of units in rotation and translation is quite different. For example, here
 we know that the first element of the parameters array corresponds to the angle that is measured in radians,
 while the other parameters correspond to the translations that are measured in millimeters

"""

import os
import numpy as np
from matplotlib import pyplot as plt
import SimpleITK as sitk
from IPython.display import clear_output



def create_matrix(final_transform):
    finalParameters = final_transform.GetParameters()
    fixedParameters = final_transform.GetFixedParameters()
    #print(finalParameters)
    #print(fixedParameters)
    #return
    rot_rad, xshift, yshift = finalParameters
    center = np.array(fixedParameters)

    R = np.array([[np.cos(rot_rad), -np.sin(rot_rad)],
                  [np.sin(rot_rad), np.cos(rot_rad)]])
    shift = center + (xshift, yshift) - np.dot(R, center)
    T = np.vstack([np.column_stack([R, shift]), [0, 0, 1]])
    return T

def create_warp_transforms(animal, transforms, transforms_resol, resolution):
    #transforms_resol = op['resolution']
    transforms_scale_factor = convert_resolution_string_to_um(animal, resolution=transforms_resol) / convert_resolution_string_to_um(animal, resolution=resolution)
    tf_mat_mult_factor = np.array([[1, 1, transforms_scale_factor], [1, 1, transforms_scale_factor]])
    transforms_to_anchor = {
        img_name:
            convert_2d_transform_forms(np.reshape(tf, (3, 3))[:2] * tf_mat_mult_factor) for
        img_name, tf in transforms.items()}

    return transforms_to_anchor

def convert_2d_transform_forms(arr):
    """
    Just creates correct size matrix
    """
    return np.vstack([arr, [0,0,1]])


def start_plot():
    global metric_values, multires_iterations
    metric_values = []
    multires_iterations = []


# Callback invoked when the EndEvent happens, do cleanup of data and figure.
def end_plot():
    global metric_values, multires_iterations
    del metric_values
    del multires_iterations
    # Close figure, we don't want to get a duplicate of the plot latter on.
    plt.close()


# Callback invoked when the sitkMultiResolutionIterationEvent happens, update the index into the
# metric_values list.
def update_multires_iterations():
    global metric_values, multires_iterations
    multires_iterations.append(len(metric_values))


# Callback invoked when the IterationEvent happens, update our data and display new figure.
def plot_values(registration_method):
    global metric_values, multires_iterations

    metric_values.append(registration_method.GetMetricValue())
    # Clear the output area (wait=True, to reduce flickering), and plot current data
    clear_output(wait=True)
    # Plot the similarity metric values
    plt.plot(metric_values, 'r')
    plt.plot(multires_iterations, [metric_values[index] for index in multires_iterations], 'b*')
    plt.xlabel('Iteration Number', fontsize=12)
    plt.ylabel('Metric Value', fontsize=12)
    plt.show()

def command_iteration(method):
    print("{0:3} = {1:10.5f} : {2}".format(method.GetOptimizerIteration(),
                                           method.GetMetricValue(),
                                           method.GetOptimizerPosition()))





def register_test(INPUT, fixed_index, moving_index):
    pixelType = sitk.sitkFloat32
    fixed_file = os.path.join(INPUT, f'{fixed_index}.tif')
    moving_file = os.path.join(INPUT, f'{moving_index}.tif')
    fixed = sitk.ReadImage(fixed_file, pixelType);
    moving = sitk.ReadImage(moving_file, pixelType)

    initial_transform = sitk.CenteredTransformInitializer(
        fixed, moving,
        sitk.Euler2DTransform(),
        sitk.CenteredTransformInitializerFilter.MOMENTS)

    R = sitk.ImageRegistrationMethod()
    R.SetInitialTransform(initial_transform, inPlace=True)
    R.SetMetricAsCorrelation() # -0439
    #R.SetMetricAsMeanSquares()
    #R.SetMetricAsMattesMutualInformation()
    R.SetMetricSamplingStrategy(R.REGULAR) # random = 0.442 # regular -0.439
    R.SetMetricSamplingPercentage(0.2)
    R.SetInterpolator(sitk.sitkLinear)
    # Optimizer settings.
    R.SetOptimizerAsRegularStepGradientDescent(learningRate=1,
                                               minStep=1e-4,
                                               numberOfIterations=100,
                                               gradientMagnitudeTolerance=1e-8)
    R.SetOptimizerScalesFromPhysicalShift()

    # Connect all of the observers so that we can perform plotting during registration.
    R.AddCommand(sitk.sitkStartEvent, start_plot)
    R.AddCommand(sitk.sitkEndEvent, end_plot)
    R.AddCommand(sitk.sitkMultiResolutionIterationEvent, update_multires_iterations)
    R.AddCommand(sitk.sitkIterationEvent, lambda: plot_values(R))


    final_transform = R.Execute(sitk.Cast(fixed, sitk.sitkFloat32),
                                                   sitk.Cast(moving, sitk.sitkFloat32))

    return final_transform, fixed, moving, R
    

def register(INPUT, fixed_index, moving_index):
    pixelType = sitk.sitkFloat32
    fixed_file = os.path.join(INPUT, f'{fixed_index}.tif')
    moving_file = os.path.join(INPUT, f'{moving_index}.tif')
    fixed = sitk.ReadImage(fixed_file, pixelType);
    moving = sitk.ReadImage(moving_file, pixelType)
    initial_transform = sitk.CenteredTransformInitializer(
        fixed, moving,
        sitk.Euler2DTransform(),
        sitk.CenteredTransformInitializerFilter.MOMENTS)
    R = sitk.ImageRegistrationMethod()
    R.SetInitialTransform(initial_transform, inPlace=True) # -0.5923
    R.SetMetricAsCorrelation()
    R.SetMetricSamplingStrategy(R.REGULAR)
    R.SetMetricSamplingPercentage(0.2)
    R.SetInterpolator(sitk.sitkLinear)
    # Optimizer settings.
    R.SetOptimizerAsRegularStepGradientDescent(learningRate=1,
                                               minStep=1e-4,
                                               numberOfIterations=100,
                                               gradientMagnitudeTolerance=1e-8)
    R.SetOptimizerScalesFromPhysicalShift()
    # Perform registration
    return R.Execute(sitk.Cast(fixed, sitk.sitkFloat32),
                                                   sitk.Cast(moving, sitk.sitkFloat32))


def register_files(fixed, moving):

    # now translation
    R1 = sitk.ImageRegistrationMethod()
    R1.SetInitialTransform(sitk.TranslationTransform(fixed.GetDimension()), inPlace=True) # -0.5923
    R1.SetMetricAsCorrelation() # -0439
    #R1.SetMetricAsMattesMutualInformation(50)
    #R1.SetMetricAsJointHistogramMutualInformation(100,10)
    R1.SetMetricSamplingStrategy(R1.REGULAR) # random = 0.442 # regular -0.439
    R1.SetMetricSamplingPercentage(0.2)
    R1.SetInterpolator(sitk.sitkLinear)
    # Optimizer settings.
    R1.SetOptimizerAsRegularStepGradientDescent(learningRate=0.5,
                                               minStep=1e-4,
                                               numberOfIterations=125,
                                               gradientMagnitudeTolerance=1e-8)
    R1.SetOptimizerScalesFromPhysicalShift()
    R1.AddCommand(sitk.sitkStartEvent, start_plot)
    R1.AddCommand(sitk.sitkEndEvent, end_plot)
    R1.AddCommand(sitk.sitkMultiResolutionIterationEvent, update_multires_iterations)
    R1.AddCommand(sitk.sitkIterationEvent, lambda: plot_values(R1))

    translation_transform = R1.Execute(sitk.Cast(fixed, sitk.sitkFloat32),
                                                   sitk.Cast(moving, sitk.sitkFloat32))

    moving_translated = sitk.Resample(moving, fixed, translation_transform, sitk.sitkLinear, 0.0,
                                     moving.GetPixelID())

    xshift, yshift = translation_transform.GetParameters()
    # 2nd transform, rotation

    rotation_transform = sitk.CenteredTransformInitializer(
        fixed, moving_translated,
        sitk.Euler2DTransform(),
        sitk.CenteredTransformInitializerFilter.MOMENTS)

    R2 = sitk.ImageRegistrationMethod()
    R2.SetInitialTransform(rotation_transform, inPlace=True)
    #R.SetMetricAsMattesMutualInformation(50)
    R2.SetMetricAsCorrelation() # -0439
    #R.SetMetricAsMeanSquares() # different scale, rot=-0.11
    R2.SetMetricSamplingStrategy(R2.REGULAR) # random = 0.442 # regular -0.439
    #On the other hand, if the images are detailed,
    # it may be necessary to use a much higher proportion, such as 20% to 50%.
    R2.SetMetricSamplingPercentage(0.2)
    #R.SetUseSampledPointSet(False)
    R2.SetInterpolator(sitk.sitkLinear)
    # Optimizer settings.
    R2.SetOptimizerAsRegularStepGradientDescent(learningRate=1,
                                               minStep=1e-4,
                                               numberOfIterations=60,
                                               gradientMagnitudeTolerance=1e-8)
    R2.SetOptimizerScalesFromPhysicalShift()
    R2.AddCommand(sitk.sitkStartEvent, start_plot)
    R2.AddCommand(sitk.sitkEndEvent, end_plot)
    R2.AddCommand(sitk.sitkMultiResolutionIterationEvent, update_multires_iterations)
    R2.AddCommand(sitk.sitkIterationEvent, lambda: plot_values(R2))


    rotation_transform = R2.Execute(sitk.Cast(fixed, sitk.sitkFloat32),
                                                   sitk.Cast(moving_translated, sitk.sitkFloat32))

    rotation , _, _ = rotation_transform.GetParameters()


    composite_transform = sitk.CompositeTransform([rotation_transform, translation_transform])

    return composite_transform, rotation, xshift, yshift



def register_translation(fixed, moving):
    # 1st transform is translation
    R1 = sitk.ImageRegistrationMethod()
    R1.SetInitialTransform(sitk.TranslationTransform(fixed.GetDimension()), inPlace=True) # -0.5923
    R1.SetMetricAsCorrelation() # -0439
    #R1.SetMetricAsJointHistogramMutualInformation(50)
    R1.SetMetricSamplingStrategy(R1.REGULAR) # random = 0.442 # regular -0.439
    R1.SetMetricSamplingPercentage(0.5)
    R1.SetInterpolator(sitk.sitkLinear)
    # Optimizer settings.
    R1.SetOptimizerAsRegularStepGradientDescent(learningRate=1,
                                               minStep=1e-4,
                                               numberOfIterations=280,
                                               gradientMagnitudeTolerance=1e-8)
    R1.SetOptimizerScalesFromPhysicalShift()
    R1.AddCommand(sitk.sitkStartEvent, start_plot)
    R1.AddCommand(sitk.sitkEndEvent, end_plot)
    R1.AddCommand(sitk.sitkMultiResolutionIterationEvent, update_multires_iterations)
    R1.AddCommand(sitk.sitkIterationEvent, lambda: plot_values(R1))

    translation_transform = R1.Execute(sitk.Cast(fixed, sitk.sitkFloat32),
                                                   sitk.Cast(moving, sitk.sitkFloat32))

    x, y = translation_transform.GetParameters()
    return translation_transform, 0, x, y

def register_rotation(fixed, moving):
    rotation_transform = sitk.CenteredTransformInitializer(
        fixed, moving,
        sitk.Similarity2DTransform())

    R2 = sitk.ImageRegistrationMethod()
    R2.SetInitialTransform(rotation_transform, inPlace=True)
    #R2.SetShrinkFactorsPerLevel([1, 1, 1])
    #R2.SetSmoothingSigmasPerLevel([2, 1, 1])
    R2.SetMetricAsCorrelation() # -0439
    #R2.SetMetricAsJointHistogramMutualInformation(75,2)
    #R2.SetMetricAsMattesMutualInformation(50)
    #R2.SetMetricAsMeanSquares()
    R2.SetMetricSamplingStrategy(R2.REGULAR) # random = 0.442 # regular -0.439
    R2.SetMetricSamplingPercentage(0.2)
    #R2.SetMetricAsJointHistogramMutualInformation(20)

    R2.SetOptimizerAsRegularStepGradientDescent(learningRate=1.0,
                                               minStep=1e-4,
                                               numberOfIterations=100,
                                               gradientMagnitudeTolerance=1e-8)
    #R2.SetOptimizerAsGradientDescent(learningRate=0.75,
    #                                numberOfIterations=200,
    #                                estimateLearningRate=R2.EachIteration)

    #R2.SetOptimizerScalesFromPhysicalShift()
    R2.SetInterpolator(sitk.sitkLinear)
    R2.AddCommand(sitk.sitkStartEvent, start_plot)
    R2.AddCommand(sitk.sitkEndEvent, end_plot)
    R2.AddCommand(sitk.sitkMultiResolutionIterationEvent, update_multires_iterations)
    R2.AddCommand(sitk.sitkIterationEvent, lambda: plot_values(R2))


    rotation_transform = R2.Execute(sitk.Cast(fixed, sitk.sitkFloat32),
                                                   sitk.Cast(moving, sitk.sitkFloat32))
    return rotation_transform




def register2d(INPUT, fixed_index, moving_index):
    pixelType = sitk.sitkFloat32
    fixed_file = os.path.join(INPUT, f'{fixed_index}.tif')
    moving_file = os.path.join(INPUT, f'{moving_index}.tif')

    fixed = sitk.ReadImage(fixed_file, pixelType);
    moving = sitk.ReadImage(moving_file, pixelType)

    rotation_transform = sitk.CenteredTransformInitializer(
        fixed, moving,
        sitk.Similarity2DTransform(), sitk.CenteredTransformInitializerFilter.MOMENTS)

    R2 = sitk.ImageRegistrationMethod()
    R2.SetInitialTransform(rotation_transform, inPlace=True)
    R2.SetMetricAsCorrelation() # -0439
    R2.SetMetricSamplingStrategy(R2.REGULAR) # random = 0.442 # regular -0.439
    R2.SetMetricSamplingPercentage(0.2)
    R2.SetOptimizerAsRegularStepGradientDescent(learningRate=1.0,
                                               minStep=1e-4,
                                               numberOfIterations=100,
                                               gradientMagnitudeTolerance=1e-8)
    R2.SetOptimizerScalesFromPhysicalShift()
    R2.SetInterpolator(sitk.sitkLinear)

    final_transform = R2.Execute(sitk.Cast(fixed, sitk.sitkFloat32),
                                                   sitk.Cast(moving, sitk.sitkFloat32))
    finalParameters = final_transform.GetParameters()
    fixedParameters = final_transform.GetFixedParameters()
    scale, rot_rad, xshift, yshift = finalParameters
    center = np.array(fixedParameters)

    rot_rad *= scale

    rotation = np.array([[np.cos(rot_rad), -np.sin(rot_rad)],
                  [np.sin(rot_rad), np.cos(rot_rad)]])

    t = center + (xshift, yshift) - np.dot(rotation, center)
    #T = np.vstack([np.column_stack([R, shift]), [0, 0, 1]])
    return rotation, t, rot_rad, xshift, yshift, final_transform

def register_simple(INPUT, fixed_index, moving_index):
    pixelType = sitk.sitkFloat32
    fixed_file = os.path.join(INPUT, f'{fixed_index}.tif')
    moving_file = os.path.join(INPUT, f'{moving_index}.tif')
    fixed = sitk.ReadImage(fixed_file, pixelType)
    moving = sitk.ReadImage(moving_file, pixelType)

    elastixImageFilter = sitk.ElastixImageFilter()
    elastixImageFilter.SetFixedImage(fixed)
    elastixImageFilter.SetMovingImage(moving)
    #elastixImageFilter.SetParameterMap(sitk.GetDefaultParameterMap("rigid"))
    rigid_params = elastixImageFilter.GetDefaultParameterMap("rigid")


    rigid_params['ASGDParameterEstimationMethod']=['Original']
    rigid_params['AutomaticTransformInitialization']=['false']
    rigid_params['AutomaticTransformInitializationMethod']=['GeometricalCenter']
    rigid_params['FiniteDifferenceDerivative']=['false']
    rigid_params['FixedImageBSplineInterpolationOrder']=['1']
    rigid_params['FixedKernelBSplineOrder']=['0']
    rigid_params['FixedLimitRangeRatio']=['0.01']
    rigid_params['MaxBandCovSize']=['192']
    rigid_params['MaximumStepLength']=['1']
    rigid_params['MaximumStepLengthRatio']=['1']
    rigid_params['MovingKernelBSplineOrder']=['3']
    rigid_params['MovingLimitRangeRatio']=['0.01']
    rigid_params['NumberOfBandStructureSamples']=['10']
    rigid_params['NumberOfFixedHistogramBins']=['32']
    rigid_params['NumberOfGradientMeasurements']=['0']
    rigid_params['NumberOfHistogramBins']=['32']
    rigid_params['NumberOfJacobianMeasurements']=['1000']
    rigid_params['NumberOfMovingHistogramBins']=['32']
    rigid_params['ShowExactMetricValue']=['false']
    rigid_params['SigmoidInitialTime']=['0']
    rigid_params['SigmoidScaleFactor']=['0.1']
    rigid_params['SP_A']=['20']
    rigid_params['UseAdaptiveStepSizes']=['true']
    rigid_params['UseConstantStep']=['false']
    rigid_params['UseFastAndLowMemoryVersion']=['true']
    rigid_params['UseJacobianPreconditioning']=['false']
    rigid_params['UseMultiThreadingForMetrics']=['true']
    rigid_params['UseRandomSampleRegion']=['false']

    rigid_params['Metric']=['AdvancedNormalizedCorrelation']
    rigid_params['SubtractMean']=['true']   

    rigid_params['FixedInternalImagePixelType']=['float']
    rigid_params['MovingInternalImagePixelType']=['float']
    rigid_params['FixedImageDimension']=['2']
    rigid_params['MovingImageDimension']=['2']
    rigid_params['FixedImagePyramid']=['FixedSmoothingImagePyramid']
    rigid_params['MovingImagePyramid']=['MovingSmoothingImagePyramid']
    rigid_params['NumberOfResolutions']=['6']

    rigid_params['MaximumNumberOfSamplingAttempts']=['0']


    translation_params = elastixImageFilter.GetDefaultParameterMap('translation')
 
    translation_params['AutomaticParameterEstimation']=['true']
    translation_params['CheckNumberOfSamples']=['true']
    translation_params['MaximumNumberOfIterations']=['120']
    translation_params['NumberOfGradientMeasurements']=['0']
    translation_params['NumberOfJacobianMeasurements']=['1000']
    translation_params['NumberOfSamplesForExactGradient']=['100000']
    translation_params['NumberOfSpatialSamples']=['5000']
    rigid_params['UseDirectionCosines']=['true']

    elastixImageFilter.SetParameterMap(rigid_params)
    elastixImageFilter.AddParameterMap(translation_params)
    elastixImageFilter.LogToConsoleOff()

    elastixImageFilter.Execute()
    return elastixImageFilter.GetTransformParameterMap()[0]["TransformParameters"]

