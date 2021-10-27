from AffineRegistration import AffineRegistration
from SitkIOs import SitkIOs
affine_registration = AffineRegistration()
fixed_image_path = ''
moving_image_path = ''
affine_registration.load_fixed_image_from_directory(fixed_image_path)
affine_registration.load_moving_image_from_driectory(moving_image_path)
affine_registration.align_image_centers()
affine_registration.calculate_affine_transform()
transform = affine_registration.get_transform()