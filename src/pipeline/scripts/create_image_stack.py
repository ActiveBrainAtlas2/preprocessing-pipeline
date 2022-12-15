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

    def register_volume(self):
        """This basically just runs elastix as the following command
        elastix -f $HOME/.brainglobe/sagittal_atlas_20um_iso.tif \
        -m /net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK37/preps/CH1/image_stack.tif \
        -out /net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK37/preps/CH1/registration \
        -p $HOME/programming/preprocessing-pipeline/pipeline/registration/princeton/parameterfolder/Order2_Par0000bspline.txt \
 -      p $HOME/programming/preprocessing-pipeline/pipeline/registration/princeton/parameterfolder/Order1_Par0000affine.txt

        elastix -f /net/birdstore/Active_Atlas_Data/data_root/brains_info/registration/sagittal_atlas_20um_iso.tif 
        -m /net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK41/preps/CH1/aligned_volume.tif 
        -out /net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK41/preps/CH1/registered_volume.tif 
        -p /net/birdstore/Active_Atlas_Data/data_root/brains_info/registration/Order1_Par0000affine.txt 
        -p /net/birdstore/Active_Atlas_Data/data_root/brains_info/registration/Order2_Par0000bspline.txt


        """
        os.makedirs(self.registration_path, exist_ok=True)
        cmd = ["elastix", "-f", self.sagittal_allen_path, "-m", self.aligned_volume, "-out", 
            self.registration_path, "-p", self.parameter_file_affine, "-p", self.parameter_file_bspline]
        cmd = ' '.join(cmd)
        proc_elastix = Popen(cmd, shell=True, stdout = PIPE, stderr = PIPE)
        stdout, stderr = proc_elastix.communicate()
        print(f'Output {stdout}')
        print(f'Error', {stderr})

    def perform_registration(self):
        if not os.path.exists(self.aligned_volume):
            self.create_volume()
        if not os.path.exists(self.registration_path):
            self.register_volume()
        




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)

    args = parser.parse_args()
    animal = args.animal
    volumeRegistration = VolumeRegistration(animal)
    volumeRegistration.perform_registration()

