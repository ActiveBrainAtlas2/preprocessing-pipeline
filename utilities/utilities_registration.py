import os
from matplotlib import pyplot as plt
import SimpleITK as sitk
from IPython.display import clear_output


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


def register(INPUT, fixed_index, moving_index, filter):
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


