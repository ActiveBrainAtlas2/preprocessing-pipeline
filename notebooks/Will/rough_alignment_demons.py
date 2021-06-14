from notebooks.Will.toolbox.sitk.get_registeration_method_demons import get_demons_transform
from notebooks.Will.toolbox.sitk.utility import *

def get_rough_alignment_demons_transform(moving_brain = 'DK52',fixed_brain = 'DK43'):
    print(f'aligning brain {moving_brain} to brain {fixed_brain}')
    print('loading image')
    moving_image,fixed_image = get_fixed_and_moving_image(fixed_brain,moving_brain)
    print('aligning image center')
    transform = get_initial_transform_to_align_image_centers(fixed_image, moving_image)
    print('finding affine tranformation')
    transform = get_demons_transform(fixed_image, moving_image, transform)
    print(transform)
    return transform