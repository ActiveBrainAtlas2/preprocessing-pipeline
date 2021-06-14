"""SimpleITK related utilities"""
from pathlib import Path
import SimpleITK as sitk

def load_image(image_dir, spacing=None):
    """A helper function to load a directory of images as a SimpleITK Image."""
    image_dir = Path(image_dir).resolve()
    image_series = []
    for image_file in sorted(image_dir.iterdir()):
        print(f'Loading image {image_file.name}', end='\r')
        image = sitk.ReadImage(image_file.as_posix())
        image_series.append(image)
    sitk_image = sitk.JoinSeries(image_series)
    if spacing is not None:
        sitk_image.SetSpacing(spacing)
    return sitk_image

def get_initial_transform_to_align_image_centers(fixed_image, moving_image):
    centering_transform = sitk.CenteredTransformInitializer(
        fixed_image, moving_image,
        sitk.AffineTransform(3),
        sitk.CenteredTransformInitializerFilter.GEOMETRY)
    return centering_transform

def get_fixed_and_moving_image(fixed_brain,moving_brain):
    thumb_spacing = (10.4, 10.4, 20.0)
    data_dir = Path('/net/birdstore/Active_Atlas_Data/data_root/pipeline_data')
    moving_image_thumbnail_dir = data_dir / moving_brain / 'preps/CH1/thumbnail_aligned'
    fixed_image_thumbnail_dir = data_dir / fixed_brain / 'preps/CH1/thumbnail_aligned'
    moving_image_16_bit = load_image(moving_image_thumbnail_dir, spacing=thumb_spacing)
    fixed_image_16_bit = load_image(fixed_image_thumbnail_dir, spacing=thumb_spacing)
    moving_image = sitk.Cast(moving_image_16_bit, sitk.sitkFloat32)
    fixed_image = sitk.Cast(fixed_image_16_bit, sitk.sitkFloat32)
    return moving_image,fixed_image

def get_3d_test_grid():
    test_grid = sitk.GridSource(outputPixelType=sitk.sitkUInt32, size=(100,100,100),
                             sigma=(0.1,0.1,0.1), gridSpacing=(20.0,20.0,20.0))
    return test_grid

def get_test_fixed_and_moving_image():
    moving_image = get_3d_test_grid()
    fixed_image = get_3d_test_grid()
    return fixed_image,moving_image