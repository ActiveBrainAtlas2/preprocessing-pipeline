
import os
import sys
sys.path.append('/home/zhw272/programming/pipeline_utility')
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import SimpleITK as sitk
import notebooks.Bili.notebook.utility as utility
from notebooks.Will.toolbox.IOs.get_stack_image_sitk import load_stack_from_prepi
from notebooks.Will.toolbox.IOs.get_calculated_transforms import get_demons_transform
mov_brain = 'DK52'
fix_brain = 'DK43'
thumb_spacing = (10.4, 10.4, 20.0)
moving_image = load_stack_from_prepi(mov_brain)
fixed_image = load_stack_from_prepi(fix_brain)
demons_transform = get_demons_transform(fix_brain)
demons_transformed_image = sitk.Resample(
    moving_image, fixed_image, demons_transform,
    sitk.sitkLinear, 0.0, moving_image.GetPixelID())
z_step = 10
# convert all images to arrays
fixed_arr = sitk.GetArrayViewFromImage(fixed_image)
moving_arr = sitk.GetArrayViewFromImage(moving_image)
demons_transformed_arr = sitk.GetArrayViewFromImage(demons_transformed_image)

save_path = '/home/zhw272/plots/affine_rough_alignment_diag/'
if not os.path.exists(save_path):
    os.mkdir(save_path)

def add_figure_to_pdf(prep_id,stack_array,title_text,z,pdf):
    fig = plt.figure(**figure_kwargs)
    plt.imshow(stack_array[z,:,:], **imshow_kwargs)
    plt.title(f'z = {z}\n{prep_id} ' + title_text)
    plt.axis('off')
    pdf.savefig(fig)
    plt.close()

save_file_path = save_path+fix_brain+'-Demons-alt.pdf'
figure_kwargs = {
    'dpi': 200,
    'figsize': (8, 6),
}
imshow_kwargs = {
    'aspect':'equal',
    'cmap': 'gray',
}
with PdfPages(save_file_path) as pdf:
    sz = fixed_arr.shape[0]
    for z in range(0, sz, z_step):
        print(f'{z}/{sz}', end='\r')
        add_figure_to_pdf(mov_brain,moving_arr,'moving',z,pdf)
        add_figure_to_pdf(fix_brain,fixed_arr,'fixed',z,pdf)
        add_figure_to_pdf(mov_brain,demons_transformed_arr,'Demons transformed',z,pdf)
        add_figure_to_pdf(fix_brain,fixed_arr,'fixed',z,pdf)
print('Finished!')


