import os 

def get_plot_save_path_root():
    return '/home/zhw272/plots/'

def get_plot_save_path(file_name = '',folder=''):
    save_folder = get_plot_save_path_root()
    if not os.path.exists(save_folder+ folder):
        os.mkdir(save_folder+ folder)
    file_path = save_folder + folder+'/'+file_name+'.html'
    return file_path