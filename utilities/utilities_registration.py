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



# reg from tutorial rotation, xshift, yshift (-0.0034807742960239595, -36.88411114029529, 0.7795425553435908)
# reg from test rotation, xshift, yshift (0.9989561173433995, -0.048287262488821474, -57.242378687708886, -1.8337162672070968)
def register_test(INPUT, fixed_index, moving_index):
    pixelType = sitk.sitkFloat32
    fixed_file = os.path.join(INPUT, f'{fixed_index}.tif')
    moving_file = os.path.join(INPUT, f'{moving_index}.tif')
    #fixed_mask_file = os.path.join(MASKED, f'{fixed_index}.tif')
    #moving_mask_file = os.path.join(MASKED, f'{moving_index}.tif')

    fixed = sitk.ReadImage(fixed_file, pixelType);
    moving = sitk.ReadImage(moving_file, pixelType)
    #maskFixed = sitk.ReadImage(fixed_mask_file, sitk.sitkUInt8)
    #maskMoving= sitk.ReadImage(moving_mask_file, sitk.sitkUInt8)
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
    #geometry = sitk.CenteredTransformInitializerFilter.GEOMETRY
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
    # Good version with correlation
    R = sitk.ImageRegistrationMethod()
    R.SetMetricAsCorrelation()
    #R.SetOptimizerAsRegularStepGradientDescent(learningRate=1,
    #                                           minStep=1e-4,
    #                                           numberOfIterations=80,
    #                                           gradientMagnitudeTolerance=1e-8)
    R.SetOptimizerAsGradientDescent(learningRate=1.0, numberOfIterations=100)
    R.SetOptimizerScalesFromIndexShift()
    moments = sitk.CenteredTransformInitializerFilter.MOMENTS
    transformation = sitk.CenteredTransformInitializer(fixed, moving,
                                           sitk.Similarity2DTransform(), moments)
    R.SetInitialTransform(transformation)
    R.SetMetricSamplingStrategy(R.REGULAR)  # R.RANDOM
    R.SetMetricSamplingPercentage(0.1)
    R.SetInterpolator(sitk.sitkLinear)

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
    ### done test
    # Define the transformation (Rigid body here)
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


def register_from_tutorial(INPUT, fixed_index, moving_index):
    pixelType = sitk.sitkUInt16

    fixed_file = os.path.join(INPUT, f'{fixed_index}.tif')
    moving_file = os.path.join(INPUT, f'{moving_index}.tif')
    fixed = sitk.ReadImage(fixed_file, pixelType);
    moving = sitk.ReadImage(moving_file, pixelType)

    initial_transform = sitk.CenteredTransformInitializer(
        fixed, moving,
        sitk.Euler2DTransform(),
        sitk.CenteredTransformInitializerFilter.MOMENTS)

    R = sitk.ImageRegistrationMethod()
    R.SetMetricAsCorrelation()
    R.SetMetricSamplingStrategy(R.REGULAR)
    R.SetMetricSamplingPercentage(0.1)
    R.SetInterpolator(sitk.sitkLinear)
    # Optimizer settings.
    R.SetOptimizerAsRegularStepGradientDescent(learningRate=1,
                                               minStep=1e-4,
                                               numberOfIterations=180,
                                               gradientMagnitudeTolerance=1e-8)
    R.SetOptimizerScalesFromPhysicalShift()
    R.SetInitialTransform(initial_transform)

    # Connect all of the observers so that we can perform plotting during registration.
    R.AddCommand(sitk.sitkStartEvent, start_plot)
    R.AddCommand(sitk.sitkEndEvent, end_plot)
    R.AddCommand(sitk.sitkMultiResolutionIterationEvent, update_multires_iterations)
    R.AddCommand(sitk.sitkIterationEvent, lambda: plot_values(R))


    final_transform = R.Execute(sitk.Cast(fixed, sitk.sitkFloat32),
                                                   sitk.Cast(moving, sitk.sitkFloat32))

    return final_transform, fixed, moving, R

def register_correlation(INPUT, fixed_index, moving_index):
    pixelType = sitk.sitkUInt16
    fixed_file = os.path.join(INPUT, f'{fixed_index}.tif')
    moving_file = os.path.join(INPUT, f'{moving_index}.tif')

    fixed = sitk.ReadImage(fixed_file, pixelType);
    moving = sitk.ReadImage(moving_file, pixelType)

    initial_transform = sitk.CenteredTransformInitializer(
        fixed, moving,
        sitk.Euler2DTransform(),
        sitk.CenteredTransformInitializerFilter.MOMENTS)

    R = sitk.ImageRegistrationMethod()
    R.SetMetricAsCorrelation()
    R.SetMetricSamplingStrategy(R.REGULAR)
    R.SetMetricSamplingPercentage(0.1)
    R.SetInterpolator(sitk.sitkLinear)
    # Optimizer settings.
    R.SetOptimizerAsRegularStepGradientDescent(learningRate=1,
                                               minStep=1e-4,
                                               numberOfIterations=180,
                                               gradientMagnitudeTolerance=1e-8)
    R.SetOptimizerScalesFromPhysicalShift()
    R.SetInitialTransform(initial_transform)

    # Perform registration
    final_transform = R.Execute(sitk.Cast(fixed, sitk.sitkFloat32),
                                                   sitk.Cast(moving, sitk.sitkFloat32))

    finalParameters = final_transform.GetParameters()
    fixedParameters = final_transform.GetFixedParameters()
    rot_rad, xshift, yshift = finalParameters
    center = np.array(fixedParameters)

    R = np.array([[np.cos(rot_rad), -np.sin(rot_rad)],
                  [np.sin(rot_rad), np.cos(rot_rad)]])
    t = center + (xshift, yshift) - np.dot(R, center)
    #T = np.vstack([np.column_stack([R, shift]), [0, 0, 1]])
    return R, t
