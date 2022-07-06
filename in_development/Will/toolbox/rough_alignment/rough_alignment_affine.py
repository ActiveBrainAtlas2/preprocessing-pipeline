from toolbox.rough_alignment.sitk.get_registeration_method_affine import get_affine_transform
from toolbox.rough_alignment.sitk.utility import get_fixed_and_moving_image
import SimpleITK as sitk

def get_rough_alignment_affine_transform(moving_brain = 'DK52',fixed_brain = 'DK43'):
    """get_rough_alignment_affine_transform [finds the image to image affine transformation from points in the fixed brain to moving brain]

    :param moving_brain: [ID of moving brain], defaults to 'DK52'
    :type moving_brain: str, optional
    :param fixed_brain: [ID of fixed brain], defaults to 'DK43'
    :type fixed_brain: str, optional
    :return transform: [Simple ITK affine transformation object]
    :rtype: [SimpleITK:AffineTransform]
    """        
    print(f'aligning brain {moving_brain} to brain {fixed_brain}')
    print('loading image')
    moving_image,fixed_image = get_fixed_and_moving_image(fixed_brain,moving_brain)
    print('aligning image center')
    transform = get_initial_transform_to_align_image_centers(fixed_image, moving_image)
    print('finding affine tranformation')
    transform = get_affine_transform(fixed_image, moving_image, transform)
    print(transform)
    return transform

def get_initial_transform_to_align_image_centers(fixed_image, moving_image):
    """get_initial_transform_to_align_image_centers [finds an initial translation that alignes the mean of two stacks]

    :param fixed_image: [fixed image stack]
    :type fixed_image: [sitk image]
    :param moving_image: [moving image stack]
    :type moving_image: [sitk image]
    :return: [translation for centering]
    :rtype: [sitk transformation]
    """
    centering_transform = sitk.CenteredTransformInitializer(
        fixed_image, moving_image,
        sitk.AffineTransform(3),
        sitk.CenteredTransformInitializerFilter.GEOMETRY)
    return centering_transform