import numpy as np
from skimage import io
from os.path import expanduser
from tqdm import tqdm
HOME = expanduser("~")
import os, sys
import SimpleITK as sitk


animal = 'DK39'
DIR = f'/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{animal}/preps'
INPUT = os.path.join(DIR, 'CH1', 'thumbnail_cleaned')
ELASTIX = os.path.join(DIR, 'elastix')

def register(fixed_image, moving_image):
    initial_transform = sitk.CenteredTransformInitializer(
    fixed_image,
    moving_image,
    sitk.Euler2DTransform(),
    sitk.CenteredTransformInitializerFilter.GEOMETRY)

    registration_method = sitk.ImageRegistrationMethod()

    # Similarity metric settings.
    registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
    registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
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
    registration_method.SetInitialTransform(initial_transform, inPlace=True)


    final_transform = registration_method.Execute(sitk.Cast(fixed_image, sitk.sitkFloat32),
                                                   sitk.Cast(moving_image, sitk.sitkFloat32))
    return final_transform


image_name_list = sorted(os.listdir(INPUT))
for i in tqdm(range(1, len(image_name_list))):
    final_transform = None
    prev_img_name = os.path.splitext(image_name_list[i - 1])[0]
    curr_img_name = os.path.splitext(image_name_list[i])[0]
    moving_file = os.path.join(INPUT, image_name_list[i - 1])
    fixed_file = os.path.join(INPUT, image_name_list[i])
    outfile = f'{curr_img_name}-{prev_img_name}.tfm'
    outpath = os.path.join(ELASTIX, outfile)
    if os.path.exists(outpath):
        continue

    moving_image = sitk.ReadImage(moving_file, sitk.sitkUInt16)
    fixed_image = sitk.ReadImage(fixed_file, sitk.sitkUInt16)

    try:
        final_transform = register(fixed_image, moving_image)
    except:
        print('Could not create transform for ', outfile)
    if final_transform is not None:
        sitk.WriteTransform(final_transform, outpath)
