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