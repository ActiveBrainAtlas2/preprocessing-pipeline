import SimpleITK as sitk
from pathlib import Path 


def get_image_stack(brain_id):
    thumb_spacing = (10.4, 10.4, 20.0)
    data_dir = Path('/net/birdstore/Active_Atlas_Data/data_root/pipeline_data')
    image_thumbnail_dir = data_dir / brain_id / 'preps/CH1/thumbnail_aligned'
    image_16_bit = load_image(image_thumbnail_dir, spacing=thumb_spacing)
    image = sitk.Cast(image_16_bit, sitk.sitkFloat32)
    return image

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