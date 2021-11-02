
import sys
sys.path.append('/home/zhw272/programming/pipeline_utility')
from notebooks.Will.toolbox.IOs.save_diagnostic_pdfs import save_diagnostic_pdf
import SimpleITK as sitk
from notebooks.Will.toolbox.IOs.get_stack_image_sitk import load_stack_from_prepi
from notebooks.Will.toolbox.IOs.get_calculated_transforms import get_affine_transform
mov_brain = 'DK52'
fix_brain = 'DK43'
thumb_spacing = (10.4, 10.4, 20.0)
moving_image = load_stack_from_prepi(mov_brain)
fixed_image = load_stack_from_prepi(fix_brain)
affine_transform = get_affine_transform(fix_brain)
affine_transformed_image = sitk.Resample(
    moving_image, fixed_image, affine_transform,
    sitk.sitkLinear, 0.0, moving_image.GetPixelID())
fixed_arr = sitk.GetArrayViewFromImage(fixed_image)
moving_arr = sitk.GetArrayViewFromImage(moving_image)
affine_transformed_arr = sitk.GetArrayViewFromImage(affine_transformed_image)
save_path = '/home/zhw272/plots/affine_rough_alignment_diag/'
save_diagnostic_pdf(save_path,mov_brain,fix_brain,moving_arr,fixed_arr,affine_transformed_arr,title = 'Affine transformed')

