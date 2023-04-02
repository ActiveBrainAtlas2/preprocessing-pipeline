"""
This script will:

- Create a 3D volume from a directory of aligned images
- Create a 3D volume from the 20um sagittal Allen brain and orient it the same orientation as ours
- Run elastix on the above 2 volumes
- Run transformix with the 3D volume from the 1st step with the results of the elastix transformation
"""

import argparse
import os
import sys
import numpy as np
from pathlib import Path
from skimage import io
from tqdm import tqdm
from subprocess import Popen, PIPE


PIPELINE_ROOT = Path('./src').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())

from library.image_manipulation.filelocation_manager import FileLocationManager
from library.utilities.utilities_mask import equalized 
from library.utilities.utilities_process import read_image

def scaled(img, epsilon=0.01):
    """This scales the image to the limit specified. You can get this value
    by looking at the combined histogram of the image stack. 

    :param img: image we are working on.
    :param epsilon: very small number used in np.quantile
    :return: scaled image in 16bit format
    """

    scale = 45000
    _max = np.quantile(img, 1 - epsilon) # gets almost the max value of img
    if img.dtype == np.uint8:
        _range = 2 ** 8 - 1 # 8bit
    else:
        _range = 2 ** 16 - 1 # 16bit

    if _max > 0:
        scaled = (img * (scale // _max)).astype(img.dtype) # scale the image from original values to e.g., 30000/10000
    else:
        scaled = img
    del img
    scaled[scaled > _range] = _range # if values are > 16bit, set to 16bit
    return scaled



class VolumeRegistration:
    """This class takes a downsampled image stack and registers it to the Allen volume    
    """

    def __init__(self, animal, debug):
        self.animal = animal
        self.fileLocationManager = FileLocationManager(animal)
        # check if exists
        self.thumbnail_aligned = os.path.join(self.fileLocationManager.prep, 'CH1', 'thumbnail_aligned')
        self.aligned_volume = os.path.join(self.fileLocationManager.prep, 'CH1', 'aligned_volume.tif')
        self.parameter_file_affine = os.path.join(self.fileLocationManager.registration_info, 'Order1_Par0000affine.txt')
        self.parameter_file_bspline = os.path.join(self.fileLocationManager.registration_info, 'Order2_Par0000bspline.txt')
        self.sagittal_allen_path = os.path.join(self.fileLocationManager.registration_info, 'allen_25um_sagittal.tiff')
        self.allen_stack_path = os.path.join(self.fileLocationManager.prep, 'allen_sagittal.tif')
        self.elastix_output = os.path.join(self.fileLocationManager.prep, 'elastix_output')
        self.transformix_output = os.path.join(self.fileLocationManager.prep, 'transformix_output')
        self.debug = debug
 

    def get_file_information(self):
        """Get information about the mid file in the image stack

        :return files: list of files in the directory
        :return volume_size: tuple of numpy shape
        """

        files = sorted(os.listdir(self.thumbnail_aligned))
        midpoint = len(files) // 2
        midfilepath = os.path.join(self.thumbnail_aligned, files[midpoint])
        midfile = read_image(midfilepath)
        rows = midfile.shape[0]
        columns = midfile.shape[1]
        volume_size = (rows, columns, len(files))
        return files, volume_size



    def create_volume(self):
        """Create a 3D volume of the image stack
        """
        
        files, volume_size = self.get_file_information()
        image_stack = np.zeros(volume_size)
        file_list = []
        for i in tqdm(range(len(files))):
            ffile = str(i).zfill(3) + '.tif'
            fpath = os.path.join(self.thumbnail_aligned, ffile)
            farr = read_image(fpath)
            file_list.append(farr)
        image_stack = np.stack(file_list, axis = 0)
        io.imsave(self.aligned_volume, image_stack.astype(np.uint16))
        print(f'Saved a 3D volume {self.aligned_volume} with shape={image_stack.shape} and dtype={image_stack.dtype}')

    def create_allen_stack(self):
        """Create a 3D volume of the sagittal image stack that is in
        the same orientation as ours. The original sagittal allen stack
        has the cerebellum at the bottom left, whereas our is at the bottom right.
        Rostral is on the left, caudal on the right.
        """
        
        allen = read_image(self.sagittal_allen_path)
        image_stack = np.zeros(allen.shape)
        
        file_list = []
        for i in tqdm(range(allen.shape[0])):
            farr = allen[i,:,:]
            farr = scaled(farr)
            farr = np.rot90(farr, 1, axes=(1,0))
            farr = np.flip(farr, axis=1)
            file_list.append(farr)

        image_stack = np.stack(file_list, axis = 0)
        io.imsave(self.allen_stack_path, image_stack.astype(np.uint16))
        print(f'Saved a Allen stack {self.allen_stack_path} with shape={image_stack.shape} and dtype={image_stack.dtype}')

    def register_volume(self):
        """This is the command that gets run for DK52:
        """
        
        print('Running elastix and registering volume.')
        os.makedirs(self.elastix_output, exist_ok=True)
        cmd = ["elastix", 
               "-f", self.sagittal_allen_path, 
               "-m", self.aligned_volume, 
               "-out", self.elastix_output, 
               "-p", self.parameter_file_affine, 
               "-p", self.parameter_file_bspline]
        if self.debug:
            print(" ".join(cmd))
        self.run_proc(cmd)

    def transformix_volume(self):
        """This is the command that gets run for DK52:
        """

        print('Running transformix and registering volume.')
        os.makedirs(self.transformix_output, exist_ok=True)
        cmd = ["transformix", 
                "-in", self.aligned_volume, 
                "-tp", os.path.join(self.elastix_output,'TransformParameters.1.txt'),  
                "-out", self.transformix_output]
        if self.debug:
            print(" ".join(cmd))
        self.run_proc(cmd)

    def perform_registration(self):
        """Starter method to check for existing directories and files
        """
        
        if not os.path.exists(self.aligned_volume):
            self.create_volume()
        if not os.path.exists(self.sagittal_allen_path):
            self.create_allen_stack()
        if not os.path.exists( os.path.join(self.elastix_output, 'TransformParameters.1.txt') ):
            self.register_volume()

        result = os.path.exists( os.path.join(self.transformix_output, 'result.tif') )
        if result:
            print(f'Process done, Allen aligned volume is at={result}')
        else:
            self.transformix_volume()


    @staticmethod
    def run_proc(cmd):
        """Static helper method to run a process

        :param cmd: list of command with arguments
        """

        cmd = ' '.join(cmd)
        proc = Popen(cmd, shell=True, stdout = PIPE, stderr = PIPE)
        _, stderr = proc.communicate()
        if stderr:
            print(f'Error', {stderr})

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument("--debug", help="Enter true or false", required=False, default="false")
    
    args = parser.parse_args()
    animal = args.animal
    debug = bool({"true": True, "false": False}[str(args.debug).lower()])
    volumeRegistration = VolumeRegistration(animal, debug)
    volumeRegistration.perform_registration()
