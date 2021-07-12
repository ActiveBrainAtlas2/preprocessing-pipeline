from matplotlib.backends.backend_pdf import PdfPages
import os 
from .get_path import get_plot_save_path_root

def get_plot_save_path(file_name = '',folder=''):
    save_folder = get_plot_save_path_root()
    if not os.path.exists(save_folder+ folder):
        os.mkdir(save_folder+ folder)
    file_path = save_folder + folder+'/'+file_name+'.html'
    return file_path

def get_plot_save_path_pdf(file_name = '',folder=''):
    save_folder = get_plot_save_path_root()
    if not os.path.exists(save_folder+ folder):
        os.mkdir(save_folder+ folder)
    file_path = save_folder + folder+'/'+file_name+'.pdf'
    return file_path

def save_figures_to_pdf(figures,file_name,folder):
    """save_figures_to_pdf [generate a pdf from a list of plt figures in ~/plots/foldername/filename.pdf
    save folder are defined in get_plot_save_path_root sub folders are created as specified and are created if do not exist]
    :param figures: [list of plt figures]
    :type figures: [list]
    :param file_name: [name of save file]
    :type file_name: [str]
    :param folder: [save folder,save in root save folder if equals '']
    :type folder: [str]
    """
    save_path = get_plot_save_path_pdf(folder = folder,file_name = file_name)
    with PdfPages(save_path) as pdf:
        for fig in figures:
            pdf.savefig(fig)