from skimage import io
import os 
import numpy as np
from subprocess import check_output

def read_image(file_path):
    try:
        img = io.imread(file_path)
    except IOError as e:
        errno, strerror = e.args
        print(f'Could not open {file_path} {errno} {strerror}')
    return img

def get_image_size(filepath):
    result_parts = str(check_output(["identify", filepath]))
    results = result_parts.split()
    width, height = results[2].split('x')
    return int(width), int(height)

def get_max_image_size(folder_path):
    size = []
    for file in os.listdir(folder_path):
        filepath = folder_path+'/'+file
        width,height = get_image_size(filepath)
        size.append([int(width),int(height)])
    return np.array(size).max(axis = 0)