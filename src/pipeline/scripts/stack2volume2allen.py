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
import SimpleITK as sitk


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
        self.debug = debug
        self.fileLocationManager = FileLocationManager(animal)
        # check if exists
        self.thumbnail_aligned = os.path.join(self.fileLocationManager.prep, 'CH1', 'thumbnail_aligned')
        self.moving_volume = os.path.join(self.fileLocationManager.prep, 'CH1', 'moving_volume.tif')
        if self.debug:
            print('Debugging with less iterations')
            self.parameter_file_affine = os.path.join(self.fileLocationManager.registration_info, 'Order1_Par0000affine.debug.txt')
            self.parameter_file_bspline = os.path.join(self.fileLocationManager.registration_info, 'Order2_Par0000bspline.debug.txt')
        else:
            self.parameter_file_affine = os.path.join(self.fileLocationManager.registration_info, 'Order1_Par0000affine.txt')
            self.parameter_file_bspline = os.path.join(self.fileLocationManager.registration_info, 'Order2_Par0000bspline.txt')
        self.fixed_volume = os.path.join(self.fileLocationManager.registration_info, 'fixed_volume.tif')
        self.allen_stack_path = os.path.join(self.fileLocationManager.prep, 'allen_sagittal.tif')
        self.elastix_output = os.path.join(self.fileLocationManager.prep, 'elastix_output')
        self.transformix_output = os.path.join(self.fileLocationManager.prep, 'transformix_output')
        self.aligned_point_file = os.path.join(self.fileLocationManager.prep, 'com.points.csv')
 

    def create_simple(self):
        fixedImage = sitk.ReadImage(self.fixed_volume)
        movingImage = sitk.ReadImage(self.moving_volume)
        elastixImageFilter = sitk.ElastixImageFilter()
        elastixImageFilter.SetFixedImage(fixedImage)
        elastixImageFilter.SetMovingImage(movingImage)

        affineParameterMap = sitk.GetDefaultParameterMap('affine')
        affineParameterMap["MaximumNumberOfIterations"] = ["2500"]
        affineParameterMap["WriteResultImage"] = ["true"]
        affineParameterMap["ResultImageFormat"] = ["tif"]
        affineParameterMap["ResultImagePixelType"] = ["float"]
        affineParameterMap["NumberOfResolutions"]= ["8"]

        bsplineParameterMap = sitk.GetDefaultParameterMap('bspline')
        bsplineParameterMap["MaximumNumberOfIterations"] = ["15000"]
        bsplineParameterMap["WriteResultImage"] = ["true"]
        bsplineParameterMap["ResultImageFormat"] = ["tif"]
        bsplineParameterMap["ResultImagePixelType"] = ["float"]
        bsplineParameterMap["UseDirectionCosines"] = ["false"]
        #bsplineParameterMap["NumberOfResolutions"]= ["4"]
        bsplineParameterMap["FinalGridSpacingInVoxels"] = ["20"]
        #bsplineParameterMap["GridSpacingSchedule"] = ["6.0 6.0 4.0 4.0 2.5 2.5 1.0 1.0"]
        del bsplineParameterMap["FinalGridSpacingInPhysicalUnits"]

        elastixImageFilter.SetParameterMap(affineParameterMap)
        elastixImageFilter.AddParameterMap(bsplineParameterMap)
        elastixImageFilter.LogToConsoleOff();
        elastixImageFilter.LogToFileOn();
        elastixImageFilter.SetOutputDirectory(self.elastix_output)
        elastixImageFilter.SetLogFileName('elastix.log');    
        elastixImageFilter.Execute()        

    def get_file_information(self):
        """Get information about the mid file in the image stack

        :return files: list of files in the directory
        :return volume_size: tuple of numpy shape
        """

        files = sorted(os.listdir(self.thumbnail_aligned))
        midpoint = len(files) // 20
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
        io.imsave(self.moving_volume, image_stack.astype(np.uint16))
        print(f'Saved a 3D volume {self.moving_volume} with shape={image_stack.shape} and dtype={image_stack.dtype}')

    def create_allen_stack(self):
        """Create a 3D volume of the sagittal image stack that is in
        the same orientation as ours. The original sagittal allen stack
        has the cerebellum at the bottom left, whereas our is at the bottom right.
        Rostral is on the left, caudal on the right.
        """
        
        allen = read_image(self.fixed_volume)
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
        """The moving image (our image stack) is warped to the fixed image (the allen reference brain) by the transformation.
        This is the command that gets run for DK52:
        """
        
        print('Running elastix and registering volume.')
        os.makedirs(self.elastix_output, exist_ok=True)
        cmd = ["elastix", 
               "-f", self.fixed_volume, 
               "-m", self.moving_volume, 
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
                "-in", self.moving_volume, 
                "-tp", os.path.join(self.elastix_output,'TransformParameters.1.txt'),  
                "-out", self.transformix_output]
        if self.debug:
            print(" ".join(cmd))
        self.run_proc(cmd)

    def transformix_points(self):
        """ Points are stored in the DB in micrometers from the full resolution images
        For the 10um allen:
            1. The set of images are from the 1/16 downsampled images
            2. That set of images are deformed to 10um iso
        
        This takes  file in THIS format:
        point
        3
        102.8 -33.4 57.0
        178.1 -10.9 14.5
        180.4 -18.1 78.9

        """

        print('Running transformix and registering volume.')
        os.makedirs(self.transformix_output, exist_ok=True)
        cmd = ["transformix", 
                "-def", self.aligned_point_file, 
                "-tp", os.path.join(self.elastix_output,'TransformParameters.1.txt'),  
                "-out", self.transformix_output]
        if self.debug:
            print(" ".join(cmd))
        self.run_proc(cmd)

    def perform_registration(self):
        """Starter method to check for existing directories and files
        """
        
        if not os.path.exists(self.moving_volume):
            self.create_volume()
        if not os.path.exists(self.fixed_volume):
            self.create_allen_stack()
        if not os.path.exists(os.path.join(self.elastix_output, 'TransformParameters.1.txt')):
            self.register_volume()

        result = os.path.exists(os.path.join(self.transformix_output, 'result.tif'))
        if result:
            print(f'Process done, Allen aligned volume is at={result}')
        else:
            self.transformix_volume()

        if os.path.exists(os.path.join(self.aligned_point_file)):
            self.transformix_points()


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
    #volumeRegistration.perform_registration()
    volumeRegistration.create_simple()