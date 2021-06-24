import pickle
import os

def ger_save_folder():
    return '/home/zhw272/data/'

def get_file_path(file_name,folder):
    save_folder = ger_save_folder()
    if not os.path.exists(save_folder+ folder):
        os.mkdir(save_folder+ folder)
    file_path = save_folder + folder+'/'+file_name+'.p'
    return file_path

def save_pickle(data , file_name , folder = ''):
    save_path = get_file_path(file_name,folder)
    pickle.dump(data,open(save_path,'wb'))
    

def load_pickle(file_name , folder = ''):
    file_path = get_file_path(file_name,folder)
    data = pickle.load(open(file_path,'rb'))
    return data