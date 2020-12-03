from skimage import io
from os.path import expanduser
from timeit import default_timer as timer
from shutil import copyfile
HOME = expanduser("~")
import os, sys
import SimpleITK as sitk
from tqdm import tqdm

start = timer()


animal = 'MD589'
DIR = f'/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{animal}/preps/CH1'
INPUT = os.path.join(DIR, 'full')
OUTPUT = os.path.join(DIR, 'thumbnail_aligned')


def align_image(fixed_image, moving_image):
    initial_transform = sitk.CenteredTransformInitializer(
        fixed_image,
        moving_image,
        sitk.Euler2DTransform(),
        sitk.CenteredTransformInitializerFilter.MOMENTS)
    registration_method = sitk.ImageRegistrationMethod()
    # Similarity metric settings.
    registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
    registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
    # changing this from 0.01 to 0.1 increased time from 32 to 81 seconds
    registration_method.SetMetricSamplingPercentage(0.01)
    registration_method.SetInterpolator(sitk.sitkLinear)
    # Optimizer settings.
    registration_method.SetOptimizerAsGradientDescent(learningRate=1.0,
                                                      numberOfIterations=100,
                                                      convergenceMinimumValue=1e-6,
                                                      convergenceWindowSize=10)
    registration_method.SetOptimizerScalesFromPhysicalShift()
    # Setup for the multi-resolution framework.
    registration_method.SetShrinkFactorsPerLevel(shrinkFactors = [4,2,1])
    registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=[2,1,0])
    registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()
    # Don't optimize in-place, we would possibly like to run this cell multiple times.
    registration_method.SetInitialTransform(initial_transform, inPlace=False)
    final_transform = registration_method.Execute(sitk.Cast(fixed_image, sitk.sitkFloat32),
                                                   sitk.Cast(moving_image, sitk.sitkFloat32))

    moving_resampled = sitk.Resample(
        moving_image, fixed_image, final_transform, sitk.sitkLinear, 0.0, moving_image.GetPixelID())
    return moving_resampled



files = sorted(os.listdir(INPUT))
lfiles = len(files)
midpoint  = lfiles // 2
#copyfile(os.path.join(INPUT, files[midpoint]), os.path.join(OUTPUT, files[midpoint]))
#copyfile(os.path.join(INPUT, files[midpoint+1]), os.path.join(OUTPUT, files[midpoint+1]))
#copyfile(os.path.join(INPUT, files[midpoint]), os.path.join(OUTPUT, files[midpoint]))
moving_resampled = None
for index in range(0, lfiles, 1):
    moving_file = os.path.join(INPUT, files[index])
    moving_image = sitk.ReadImage(moving_file, sitk.sitkUInt8)
    fixed_file = os.path.join(INPUT, files[index+1])
    fixed_image =  sitk.ReadImage(fixed_file, sitk.sitkUInt8)

    moving_resampled = align_image(fixed_image, moving_resampled)

    print(moving_file)
    print(fixed_file)
    print()


    sitk.WriteImage(moving_resampled, os.path.join(OUTPUT, files[index]))
    #sitk.WriteTransform(final_transform, os.path.join(OUTPUT, f"{index}.tfm" ))

end = timer()
print(f'Program took {end - start} seconds')
print(f'Program took {(end - start)//lfiles} seconds per file')
