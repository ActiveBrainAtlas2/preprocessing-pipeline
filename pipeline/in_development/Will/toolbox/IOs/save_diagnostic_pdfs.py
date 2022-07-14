
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

def save_diagnostic_pdf(save_path,mov_brain,fix_brain,moving_arr,fixed_arr,transformed_arr,title = 'Affine transformed'):
    """save_diagnostic_pdf [creates diagnostic pdfs for image to image transformation]

    :param save_path: [pdf save path]
    :type save_path: [type]
    :param mov_brain: [name of moving brain]
    :type mov_brain: [type]
    :param fix_brain: [name of fixed brain]
    :type fix_brain: [type]
    :param moving_arr: [moving brain image stack array]
    :type moving_arr: [type]
    :param fixed_arr: [fixed brain image stack array]
    :type fixed_arr: [type]
    :param transformed_arr: [transformed image stack array]
    :type transformed_arr: [type]
    :param title: [image title], defaults to 'Affine transformed'
    :type title: str, optional
    """
    if not os.path.exists(save_path):
        os.mkdir(save_path)
    def add_figure_to_pdf(prep_id,stack_array,title_text,z,pdf):
        fig = plt.figure(**figure_kwargs)
        plt.imshow(stack_array[z,:,:], **imshow_kwargs)
        plt.title(f'z = {z}\n{prep_id} ' + title_text)
        plt.axis('off')
        pdf.savefig(fig)
        plt.close()
    save_file_path = save_path+fix_brain+'Affine-alt.pdf'
    figure_kwargs = {
        'dpi': 200,
        'figsize': (8, 6),}
    imshow_kwargs = {
        'aspect':'equal',
        'cmap': 'gray',}
    z_step = 10
    with PdfPages(save_file_path) as pdf:
        sz = fixed_arr.shape[0]
        for z in range(0, sz, z_step):
            print(f'{z}/{sz}', end='\r')
            add_figure_to_pdf(mov_brain,moving_arr,'moving',z,pdf)
            add_figure_to_pdf(fix_brain,fixed_arr,'fixed',z,pdf)
            add_figure_to_pdf(mov_brain,transformed_arr,title,z,pdf)
            add_figure_to_pdf(fix_brain,fixed_arr,'fixed',z,pdf)
    print('Finished!')
