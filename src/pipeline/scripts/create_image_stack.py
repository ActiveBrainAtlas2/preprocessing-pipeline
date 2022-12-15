"""
This takes the a stack of tifs and creates a numpy array
3D (volume)
"""
import argparse
import os
import sys
import numpy as np
from pathlib import Path
from skimage import io
from tqdm import tqdm
from subprocess import Popen, PIPE

PIPELINE_ROOT = Path('./src/pipeline').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())

from image_manipulation.filelocation_manager import FileLocationManager
from utilities.utilities_mask import equalized 

def scaled(img, epsilon=0.01):
    """This scales the image to the limit specified. You can get this value
    by looking at the combined histogram of the image stack. It is quite
    often less than 30000 for channel 1.
    One of the reasons this takes so much RAM is a large float64 array is being
    multiplied by another large array. That is WHERE all the RAM is going!!!!!
    The scale is hardcoded to 45000 which was a good value from Yoav

    :param img: image we are working on.
    :param mask: binary mask file
    :param epsilon:
    :param limit: max value we wish to scale to
    :return: scaled image in 16bit format
    """

    scale = 45000
    _max = np.quantile(img, 1 - epsilon) # gets almost the max value of img
    if img.dtype == np.uint8:
        _range = 2 ** 8 - 1 # 8bit
        data_type = np.uint8        
    else:
        _range = 2 ** 16 - 1 # 16bit
        data_type = np.uint16

    if _max > 0:
        scaled = (img * (scale // _max)).astype(data_type) # scale the image from original values to e.g., 30000/10000
    else:
        scaled = img
    del img
    scaled[scaled > _range] = _range # if values are > 16bit, set to 16bit
    return scaled



class VolumeRegistration:
    """This class takes a downsampled image stack and registers it to the Allen volume    
    """

    def __init__(self, animal):
        self.animal = animal
        self.fileLocationManager = FileLocationManager(animal)
        self.thumbnail_aligned = os.path.join(self.fileLocationManager.prep, 'CH1', 'thumbnail_aligned')
        self.aligned_volume = os.path.join(self.fileLocationManager.prep, 'CH1', 'aligned_volume.tif')
        self.registration_path = os.path.join(self.fileLocationManager.prep, 'CH1', 'registration')
        self.parameter_file_affine = os.path.join(self.fileLocationManager.registration_info, 'Order1_Par0000affine.txt')
        self.parameter_file_bspline = os.path.join(self.fileLocationManager.registration_info, 'Order2_Par0000bspline.txt')
        self.sagittal_allen_path = os.path.join(self.fileLocationManager.registration_info, 'sagittal_atlas_20um_iso.tif')
        self.allen_stack_path = os.path.join(self.fileLocationManager.prep, 'CH1', 'allen_sagittal.tif')
 

    def get_file_information(self):
        files = sorted(os.listdir(self.thumbnail_aligned))
        midpoint = len(files) // 2
        midfilepath = os.path.join(self.thumbnail_aligned, files[midpoint])
        midfile = io.imread(midfilepath, img_num=0)
        rows = midfile.shape[0]
        columns = midfile.shape[1]
        volume_size = (rows, columns, len(files))
        return files, volume_size



    def create_volume(self):
        files, volume_size = self.get_file_information()
        print(volume_size)
        image_stack = np.zeros(volume_size)
        file_list = []
        for i in tqdm(range(len(files))):
            ffile = str(i).zfill(3) + '.tif'
            fpath = os.path.join(self.thumbnail_aligned, ffile)
            farr = io.imread(fpath)
            file_list.append(farr)
        image_stack = np.stack(file_list, axis = 0)
        io.imsave(self.aligned_volume, image_stack.astype(np.uint16))
        print(image_stack.shape)

    def create_allen_stack(self):
        allen = io.imread(self.sagittal_allen_path)
        image_stack = np.zeros(allen.shape)
        print(allen.shape)
        
        file_list = []
        for i in tqdm(range(allen.shape[0])):
            farr = allen[i,:,:]
            farr = scaled(farr)
            farr = np.rot90(farr, 1, axes=(1,0))
            farr = np.flip(farr, axis=1)
            file_list.append(farr)

        image_stack = np.stack(file_list, axis = 0)
        io.imsave(self.allen_stack_path, image_stack.astype(np.uint16))
        print(image_stack.shape)

    def register_volume(self):
        """This is the command that gets run for DK41:
        elastix -f /net/birdstore/Active_Atlas_Data/data_root/brains_info/registration/sagittal_atlas_20um_iso.tif 
        -m /net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK41/preps/CH1/aligned_volume.tif 
        -out /net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK41/preps/CH1/registered_volume.tif 
        -p /net/birdstore/Active_Atlas_Data/data_root/brains_info/registration/Order1_Par0000affine.txt 
        -p /net/birdstore/Active_Atlas_Data/data_root/brains_info/registration/Order2_Par0000bspline.txt
        """

        os.makedirs(self.registration_path, exist_ok=True)
        cmd = ["elastix", "-f", self.allen_stack_path, "-m", self.aligned_volume, "-out", 
            self.registration_path, "-p", self.parameter_file_affine, "-p", self.parameter_file_bspline]
        cmd = ' '.join(cmd)
        proc_elastix = Popen(cmd, shell=True, stdout = PIPE, stderr = PIPE)
        stdout, stderr = proc_elastix.communicate()
        print(f'Output {stdout}')
        if stderr:
            print(f'Error', {stderr})

    def perform_registration(self):
        
        if not os.path.exists(self.aligned_volume):
            self.create_volume()
        if not os.path.exists(self.sagittal_allen_path):
            self.create_allen_stack()
        if not os.path.exists( os.path.join(self.registration_path, 'TransformParameters.1.txt') ):
            self.register_volume()
        




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)

    args = parser.parse_args()
    animal = args.animal
    volumeRegistration = VolumeRegistration(animal)
    volumeRegistration.perform_registration()

