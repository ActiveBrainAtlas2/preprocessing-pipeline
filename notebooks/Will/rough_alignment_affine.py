from pathlib import Path
import SimpleITK as sitk
import toolbox.sitk
from toolbox.sitk_optimization_reporter_functions import *

def get_fixed_and_moving_image(fixed_brain,moving_brain):
    thumb_spacing = (10.4, 10.4, 20.0)
    data_dir = Path('/net/birdstore/Active_Atlas_Data/data_root/pipeline_data')
    moving_image_thumbnail_dir = data_dir / moving_brain / 'preps/CH1/thumbnail_aligned'
    fixed_image_thumbnail_dir = data_dir / fixed_brain / 'preps/CH1/thumbnail_aligned'
    moving_image_16_bit = toolbox.sitk.load_image_dir(moving_image_thumbnail_dir, spacing=thumb_spacing)
    fixed_image_16_bit = toolbox.sitk.load_image_dir(fixed_image_thumbnail_dir, spacing=thumb_spacing)
    moving_image = sitk.Cast(moving_image_16_bit, sitk.sitkFloat32)
    fixed_image = sitk.Cast(fixed_image_16_bit, sitk.sitkFloat32)
    return moving_image,fixed_image

def get_initial_transform_to_align_image_centers(fixed_image, moving_image):
    centering_transform = sitk.CenteredTransformInitializer(
        fixed_image, moving_image,
        sitk.AffineTransform(3),
        sitk.CenteredTransformInitializerFilter.GEOMETRY)
    return centering_transform

def set_mutual_information_as_similarity_metic(registration_method):
    registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
    registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
    registration_method.SetMetricSamplingPercentage(0.01)

def set_optimizer(registration_method):
    registration_method.SetOptimizerAsGradientDescent(
        learningRate=1.0,
        numberOfIterations=100,
        convergenceMinimumValue=1e-6,
        convergenceWindowSize=10
    )
    registration_method.SetOptimizerScalesFromPhysicalShift()

def set_centering_transform_as_initial_starting_point(registration_method,centering_transform):
    affine_transform = sitk.AffineTransform(centering_transform)
    registration_method.SetInitialTransform(affine_transform)
    return affine_transform

def init_regerstration_method():
    registration_method = sitk.ImageRegistrationMethod()
    registration_method.SetInterpolator(sitk.sitkLinear)
    return registration_method

def set_multi_resolution_parameters(registration_method):
    registration_method.SetShrinkFactorsPerLevel(shrinkFactors=[4, 2, 1])
    registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=[2, 1, 0])
    registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()
    
def set_report_events(registration_method):
    registration_method.AddCommand(sitk.sitkStartEvent, start_optimization)
    registration_method.AddCommand(sitk.sitkIterationEvent, lambda: print_values(registration_method))
    registration_method.AddCommand(sitk.sitkMultiResolutionIterationEvent, report_multi_resolution_events) 

def get_affine_transform_that_aligns_images(fixed_image, moving_image,transform):
    registration_method = init_regerstration_method()
    set_mutual_information_as_similarity_metic(registration_method)
    set_optimizer(registration_method)
    transform = set_centering_transform_as_initial_starting_point(registration_method, transform)
    set_multi_resolution_parameters(registration_method)
    set_report_events(registration_method)
    registration_method.Execute(fixed_image, moving_image)
    return transform

def start_optimization():
    global n_resolution
    n_resolution = 0

def print_values(registration_method):
    global n_iter
    n_iter+=1
    if n_iter%10 == 0 :
        print(f'iteration: {n_iter} {registration_method.GetMetricValue():4f}')                                  

def report_multi_resolution_events():
    global n_iter,n_resolution
    n_iter=0
    if n_resolution !=0:
        print('switching to higher resolution')
    elif n_resolution == 0:
        print('starting optimization')
    n_resolution+=1
    
def get_rough_alignment_affine_transform(moving_brain = 'DK52',fixed_brain = 'DK43'):
    print(f'aligning brain {moving_brain} to brain {fixed_brain}')
    print('loading image')
    moving_image,fixed_image = get_fixed_and_moving_image(fixed_brain,moving_brain)
    print('aligning image center')
    transform = get_initial_transform_to_align_image_centers(fixed_image, moving_image)
    print('finding affine tranformation')
    transform = get_affine_transform_that_aligns_images(fixed_image, moving_image,transform)
    print(transform)
    return transform
