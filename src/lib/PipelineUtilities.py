from skimage import io
import os 
import numpy as np
from subprocess import check_output

class PipelineUtilities:
    def read_image(self,file_path):
        try:
            img = io.imread(file_path)
        except IOError as e:
            errno, strerror = e.args
            print(f'Could not open {file_path} {errno} {strerror}')
        return img

    def get_image_size(self,filepath):
        result_parts = str(check_output(["identify", filepath]))
        results = result_parts.split()
        width, height = results[2].split('x')
        return width, height

    def get_max_imagze_size(self,folder_path):
        size = []
        for file in os.listdir(folder_path):
            filepath = folder_path+'/'+file
            width,height = self.get_image_size(filepath)
            size.append([int(width),int(height)])
        return np.array(size).max(axis = 0)