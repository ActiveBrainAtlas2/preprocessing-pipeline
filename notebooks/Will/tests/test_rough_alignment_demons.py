from notebooks.Will.toolbox.sitk.utility import get_test_fixed_and_moving_image
from notebooks.Will.toolbox.sitk.get_registeration_method_demons import get_demons_transform
fixed_image,moving_image = get_test_fixed_and_moving_image()
transform = get_demons_transform(fixed_image,moving_image)
