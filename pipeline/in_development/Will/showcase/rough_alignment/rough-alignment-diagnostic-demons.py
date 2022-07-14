
import sys
sys.path.append('/home/zhw272/programming/pipeline_utility')
import SimpleITK as sitk
from toolbox.IOs.get_stack_image_sitk import load_stack_from_prepi
from toolbox.IOs.get_calculated_transforms import get_demons_transform
from toolbox.IOs.save_diagnostic_pdfs import save_diagnostic_pdf
mov_brain = 'DK52'
fix_brain = 'DK43'
thumb_spacing = (10.4, 10.4, 20.0)
moving_image = load_stack_from_prepi(mov_brain)
fixed_image = load_stack_from_prepi(fix_brain)
demons_transform = get_demons_transform(fix_brain)
demons_transformed_image = sitk.Resample(
    moving_image, fixed_image, demons_transform,
    sitk.sitkLinear, 0.0, moving_image.GetPixelID())
fixed_arr = sitk.GetArrayViewFromImage(fixed_image)
moving_arr = sitk.GetArrayViewFromImage(moving_image)
demons_transformed_arr = sitk.GetArrayViewFromImage(demons_transformed_image)

save_path = '/home/zhw272/plots/affine_rough_alignment_diag/'
save_diagnostic_pdf(save_path,mov_brain,fix_brain,moving_arr,fixed_arr,demons_transformed_arr,title = 'Demons transformed')


