import os
import numpy as np
from matplotlib import pyplot as plt
import SimpleITK as sitk
from IPython.display import clear_output

from utilities.alignment_utility import convert_resolution_string_to_um


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


def register_from_tutorial(INPUT, fixed_index, moving_index, filter):
    fixed_file = os.path.join(INPUT, f'{fixed_index}.tif')
    moving_file = os.path.join(INPUT, f'{moving_index}.tif')
    fixed = sitk.ReadImage(fixed_file, sitk.sitkUInt16);
    moving = sitk.ReadImage(moving_file, sitk.sitkUInt16)

    initial_transform = sitk.CenteredTransformInitializer(
        fixed, moving,
        sitk.Euler2DTransform(),
        sitk.CenteredTransformInitializerFilter.GEOMETRY)

    R = sitk.ImageRegistrationMethod()

    # Similarity metric settings.
    R.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
    R.SetMetricSamplingStrategy(R.RANDOM)
    R.SetMetricSamplingPercentage(0.01)

    R.SetInterpolator(sitk.sitkLinear)

    # Optimizer settings.
    R.SetOptimizerAsGradientDescent(learningRate=0.1,
                                                      numberOfIterations=1000,
                                                      convergenceMinimumValue=1e-8,
                                                      convergenceWindowSize=10)
    R.SetOptimizerScalesFromPhysicalShift()

    # Setup for the multi-resolution framework.
    R.SetShrinkFactorsPerLevel(shrinkFactors = [4,2,1])
    R.SetSmoothingSigmasPerLevel(smoothingSigmas=[2,1,0])
    R.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()

    # Don't optimize in-place, we would possibly like to run this cell multiple times.
    R.SetInitialTransform(initial_transform, inPlace=True)
    # Connect all of the observers so that we can perform plotting during registration.
    R.AddCommand(sitk.sitkStartEvent, start_plot)
    R.AddCommand(sitk.sitkEndEvent, end_plot)
    R.AddCommand(sitk.sitkMultiResolutionIterationEvent, update_multires_iterations)
    R.AddCommand(sitk.sitkIterationEvent, lambda: plot_values(R))


    final_transform = R.Execute(sitk.Cast(fixed, sitk.sitkFloat32),
                                                   sitk.Cast(moving, sitk.sitkFloat32))

    return final_transform


def register_test(MASKED, INPUT, fixed_index, moving_index):
    pixelType = sitk.sitkFloat32
    fixed_file = os.path.join(INPUT, f'{fixed_index}.tif')
    moving_file = os.path.join(INPUT, f'{moving_index}.tif')
    fixed_mask_file = os.path.join(MASKED, f'{fixed_index}.tif')
    moving_mask_file = os.path.join(MASKED, f'{moving_index}.tif')

    fixed = sitk.ReadImage(fixed_file, sitk.sitkFloat32);
    moving = sitk.ReadImage(moving_file, sitk.sitkFloat32)
    maskFixed = sitk.ReadImage(fixed_mask_file, sitk.sitkUInt8)
    maskMoving= sitk.ReadImage(moving_mask_file, sitk.sitkUInt8)
    # Handle optimizer
    # Restrict the evaluation of the similarity metric thanks to masks
    #R.SetMetricFixedMask(maskFixed)
    #R.SetMetricMovingMask(maskMoving)
    # Set metric as mutual information using joint histogram
    #R.SetMetricAsMattesMutualInformation(numberOfHistogramBins=150)
    #R.SetMetricAsJointHistogramMutualInformation(100)
    #rotation, xshift, yshift(0.12350498036706653, -17.079042362772007, -47.41141804307104)
    #R.SetMetricAsMeanSquares()
    #rotation, xshift, yshift (0.1611860479695003, -17.06518762920313, -47.4020601708269)
    #R.SetMetricAsANTSNeighborhoodCorrelation(radius=10)
    ##### ants is really slow
    ## 20 iterations looks fine, LR=0.75
    # Gradient descent optimizer
    # metric values of
    # -0.33 is really bad
    # -0.69 looked good with moments, RANDOM, 100 JointHisto same with REGULAR
    # geometry filter not good at -0.51
    # -0.47 with mattesmutual looked good
    #R.SetOptimizerAsRegularStepGradientDescent(learningRate=0.75, minStep=1e-6,
    #                                           numberOfIterations=25, gradientMagnitudeTolerance=1e-8)
    #
    R = sitk.ImageRegistrationMethod()

    # correlation
    #Final  metric value: -0.7039249190388261
    #Optimizer 's stopping condition, RegularStepGradientDescentOptimizerv4: Maximum number of iterations (25) exceeded.
    # rotation, xshift, yshift(1.0063625513680365, 0.12324555947756057, -49.463004329446534, -17.263262368310336)
    # center(959.9599816863847, 491.68844594717933)
    R.SetMetricAsCorrelation()
    R.SetOptimizerAsRegularStepGradientDescent(learningRate=1,
                                               minStep=1e-4,
                                               numberOfIterations=80,
                                               gradientMagnitudeTolerance=1e-8)
    R.SetOptimizerScalesFromIndexShift()

    tx = sitk.CenteredTransformInitializer(fixed, moving,
                                           sitk.Similarity2DTransform())
    R.SetInitialTransform(tx)
    ## OK version
    """
    R.SetMetricAsJointHistogramMutualInformation(100)

    # Gradient descent optimizer
    R.SetOptimizerAsRegularStepGradientDescent(learningRate=0.1, minStep=1e-6,
                                               numberOfIterations=25, gradientMagnitudeTolerance=1e-8)

    # R.SetOptimizerScalesFromPhysicalShift()
    R.SetMetricSamplingStrategy(R.REGULAR)  # R.RANDOM
    # Define the transformation (Rigid body here)
    moments = sitk.CenteredTransformInitializerFilter.MOMENTS
    transformation = sitk.CenteredTransformInitializer(fixed, moving, sitk.Euler2DTransform(), moments)
    R.SetInitialTransform(transformation)
    """

    R.SetInterpolator(sitk.sitkLinear)
    ### done test
    # Define the transformation (Rigid body here)
    moments = sitk.CenteredTransformInitializerFilter.MOMENTS
    geometry = sitk.CenteredTransformInitializerFilter.GEOMETRY
    transformation = sitk.CenteredTransformInitializer(fixed, moving, sitk.Euler2DTransform(), moments)
    #R.SetInitialTransform(transformation)
    # Define interpolation method
    #R.SetInterpolator(sitk.sitkLinear)
    # Add command to the registration process
    R.AddCommand(sitk.sitkStartEvent, start_plot)
    R.AddCommand(sitk.sitkEndEvent, end_plot)
    R.AddCommand(sitk.sitkMultiResolutionIterationEvent, update_multires_iterations)
    R.AddCommand(sitk.sitkIterationEvent, lambda: plot_values(R))

    # Perform registration
    final_transform = R.Execute(fixed, moving)
    return final_transform, fixed, moving, R




def register(MASKED, INPUT, fixed_index, moving_index):
    fixed_file = os.path.join(INPUT, f'{fixed_index}.tif')
    moving_file = os.path.join(INPUT, f'{moving_index}.tif')
    fixed = sitk.ReadImage(fixed_file, sitk.sitkFloat32);
    moving = sitk.ReadImage(moving_file, sitk.sitkFloat32)
    R = sitk.ImageRegistrationMethod()
    #moving_mask_file = os.path.join(MASKED, f'{moving_index}.tif')
    #maskMoving= sitk.ReadImage(moving_mask_file, sitk.sitkUInt8)
    #R.SetMetricMovingMask(maskMoving)

    R.SetMetricAsJointHistogramMutualInformation(100)

    # Gradient descent optimizer
    R.SetOptimizerAsRegularStepGradientDescent(learningRate=0.1, minStep=1e-6,
                                               numberOfIterations=25, gradientMagnitudeTolerance=1e-8)

    # R.SetOptimizerScalesFromPhysicalShift()
    R.SetMetricSamplingStrategy(R.REGULAR)  # R.RANDOM
    # Define the transformation (Rigid body here)
    moments = sitk.CenteredTransformInitializerFilter.MOMENTS
    transformation = sitk.CenteredTransformInitializer(fixed, moving, sitk.Euler2DTransform(), moments)
    R.SetInitialTransform(transformation)
    # Define interpolation method
    R.SetInterpolator(sitk.sitkLinear)
    # Perform registration
    final_transform = R.Execute(fixed, moving)
    return final_transform




def register_correlation(INPUT, fixed_index, moving_index):
    pixelType = sitk.sitkFloat32
    fixed_file = os.path.join(INPUT, f'{fixed_index}.tif')
    moving_file = os.path.join(INPUT, f'{moving_index}.tif')

    fixed = sitk.ReadImage(fixed_file, sitk.sitkFloat32);
    moving = sitk.ReadImage(moving_file, sitk.sitkFloat32)
    R = sitk.ImageRegistrationMethod()
    # correlation
    R.SetMetricAsCorrelation()
    R.SetOptimizerAsRegularStepGradientDescent(learningRate=1,
                                               minStep=1e-4,
                                               numberOfIterations=80,
                                               gradientMagnitudeTolerance=1e-8)
    R.SetOptimizerScalesFromIndexShift()

    tx = sitk.CenteredTransformInitializer(fixed, moving,
                                           sitk.Similarity2DTransform())
    R.SetInitialTransform(tx)
    R.SetInterpolator(sitk.sitkLinear)

    # Perform registration
    final_transform = R.Execute(fixed, moving)
    finalParameters = final_transform.GetParameters()
    fixedParameters = final_transform.GetFixedParameters()
    _, rot_rad, xshift, yshift = finalParameters
    center = np.array(fixedParameters)

    R = np.array([[np.cos(rot_rad), -np.sin(rot_rad)],
                  [np.sin(rot_rad), np.cos(rot_rad)]])
    shift = center + (xshift, yshift) - np.dot(R, center)
    T = np.vstack([np.column_stack([R, shift]), [0, 0, 1]])
    return T
