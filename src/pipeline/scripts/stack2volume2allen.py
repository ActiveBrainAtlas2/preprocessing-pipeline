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
from taskqueue import LocalTaskQueue
import igneous.task_creation as tc


PIPELINE_ROOT = Path('./src').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())

from library.image_manipulation.neuroglancer_manager import NumpyToNeuroglancer
from library.image_manipulation.filelocation_manager import FileLocationManager
from library.utilities.utilities_mask import normalize16
from library.utilities.utilities_process import read_image


class VolumeRegistration:
    """This class takes a downsampled image stack and registers it to the Allen volume    
    """

    def __init__(self, animal, channel, um, atlas, debug):
        self.animal = animal
        self.debug = debug
        self.um = um
        self.channel = f'CH{channel}'
        self.atlas = atlas
        self.fileLocationManager = FileLocationManager(animal)
        # check if exists
        self.thumbnail_aligned = os.path.join(self.fileLocationManager.prep, self.channel, 'thumbnail_aligned')
        self.moving_volume = os.path.join(self.fileLocationManager.prep, self.channel, 'moving_volume.tif')
        self.fixed_volume = os.path.join(self.fileLocationManager.registration_info, 'fixed_volume.tif')
        self.allen_stack_path = os.path.join(self.fileLocationManager.prep, 'allen_sagittal.tif')
        self.elastix_output = os.path.join(self.fileLocationManager.prep, 'elastix_output')
        self.transformix_output = os.path.join(self.fileLocationManager.prep, self.channel,  'registered')
        self.aligned_point_file = os.path.join(self.fileLocationManager.prep, 'com.points.pts')
        self.neuroglancer_data_path = os.path.join(self.fileLocationManager.neuroglancer_data, f'{self.channel}_{self.atlas}')
 

    def register_volume(self):
        if self.debug:
            affineIterations = "250"
            bsplineIterations = "150"
        else:
            affineIterations = "2500"
            bsplineIterations = "15000"

        fixedImage = sitk.ReadImage(self.fixed_volume)
        movingImage = sitk.ReadImage(self.moving_volume)
        elastixImageFilter = sitk.ElastixImageFilter()
        elastixImageFilter.SetFixedImage(fixedImage)
        elastixImageFilter.SetMovingImage(movingImage)

        affineParameterMap = sitk.GetDefaultParameterMap('affine')
        affineParameterMap["MaximumNumberOfIterations"] = [affineIterations] # 250 works ok
        affineParameterMap["WriteResultImage"] = ["true"]
        affineParameterMap["ResultImageFormat"] = ["tif"]
        affineParameterMap["ResultImagePixelType"] = ["float"]
        affineParameterMap["NumberOfResolutions"]= ["8"]

        bsplineParameterMap = sitk.GetDefaultParameterMap('bspline')
        bsplineParameterMap["MaximumNumberOfIterations"] = [bsplineIterations] # 150 works ok
        bsplineParameterMap["WriteResultImage"] = ["true"]
        bsplineParameterMap["ResultImageFormat"] = ["tif"]
        bsplineParameterMap["ResultImagePixelType"] = ["float"]
        bsplineParameterMap["UseDirectionCosines"] = ["false"]
        bsplineParameterMap["FinalGridSpacingInVoxels"] = [f"{self.um}"]
        del bsplineParameterMap["FinalGridSpacingInPhysicalUnits"]

        elastixImageFilter.SetParameterMap(affineParameterMap)
        elastixImageFilter.AddParameterMap(bsplineParameterMap)
        elastixImageFilter.LogToConsoleOff();
        elastixImageFilter.LogToFileOn();
        elastixImageFilter.SetOutputDirectory(self.elastix_output)
        elastixImageFilter.SetLogFileName('elastix.log');
        if self.debug:
            elastixImageFilter.PrintParameterMap(bsplineParameterMap)    
        resultImage = elastixImageFilter.Execute()  
        #transformed = sitk.Cast(resultImage, sitk.sitkUInt16)
        #print(f'new image type {type(transformed)}')
        sitk.WriteImage(resultImage, os.path.join(self.transformix_output, 'result.tif'))

    def transformix_volume(self):

        transformixImageFilter = sitk.TransformixImageFilter()
        parameterMap0 = sitk.ReadParameterFile(os.path.join(self.elastix_output, 'TransformParameters.0.txt'))
        parameterMap1 = sitk.ReadParameterFile(os.path.join(self.elastix_output, 'TransformParameters.1.txt'))
        transformixImageFilter.SetParameterMap(parameterMap0)
        transformixImageFilter.AddParameterMap(parameterMap1)
        movingImage = sitk.ReadImage(self.moving_volume)
        transformixImageFilter.SetMovingImage(movingImage)
        transformixImageFilter.Execute()
        transformed = transformixImageFilter.GetResultImage()
        transformed = sitk.Cast(transformed, sitk.sitkUInt16)
        print(f'new image type {type(transformed)}')
        sitk.WriteImage(transformed, os.path.join(self.transformix_output, 'result.tif'))


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


    def create_precomputed(self):
        chunk = 64
        chunks = (chunk, chunk, chunk)
        volumepath = os.path.join(self.transformix_output, 'result.tif')
        if not os.path.exists(volumepath):
            print(f'{volumepath} does not exist, exiting.')
            sys.exit()
            
        PRECOMPUTED = self.neuroglancer_data_path
        scale = self.um * 1000
        scales = (scale, scale, scale)
        os.makedirs(PRECOMPUTED, exist_ok=True)
        volume = read_image(volumepath)
        volume = np.swapaxes(volume, 0, 2)
        num_channels = 1
        volume_size = volume.shape
        print(f'volume shape={volume.shape} dtype={volume.dtype}')
        volume = normalize16(volume)
        print(f'volume shape={volume.shape} dtype={volume.dtype}')

        ng = NumpyToNeuroglancer(
            animal,
            None,
            scales,
            "image",
            volume.dtype,
            num_channels=num_channels,
            chunk_size=chunks,
        )

        ng.init_precomputed(PRECOMPUTED, volume_size)
        ng.precomputed_vol[:, :, :] = volume
        ng.precomputed_vol.cache.flush()
        tq = LocalTaskQueue(parallel=4)
        cloudpath = f"file://{PRECOMPUTED}"
        tasks = tc.create_downsampling_tasks(cloudpath, num_mips=2)
        tq.insert(tasks)
        tq.execute()


    def perform_registration(self):
        """Starter method to check for existing directories and files
        """
        
        if not os.path.exists(self.moving_volume):
            print('There is no moving volume, exiting.')
            sys.exit()
        if not os.path.exists(self.fixed_volume):
            print('There is no fixed volume, exiting.')
            sys.exit()

        result_path = os.path.join(self.transformix_output, 'result.tif')
        result = os.path.exists(result_path)
        if result:
            print(f'Process done, {self.atlas} aligned volume is at={result_path}')
        else:
            print('Running transformix to create registered volume')
            self.register_volume()

        if os.path.exists(os.path.join(self.aligned_point_file)) and os.path.exists(os.path.join(self.elastix_output, 'TransformParameters.1.txt')):
            print('Running transformix on points')
            #self.transformix_points()

        if not os.path.exists(self.neuroglancer_data_path):
            print('Running the precomputed process on the registered volume')
            self.create_precomputed()



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
    parser.add_argument("--channel", help="Enter channel", required=False, default=1, type=int)
    parser.add_argument('--um', help="size of Allen atlas in micrometers", required=False, default=20, type=int)
    parser.add_argument('--atlas', help='Enter the atlas', required=False, default='princeton')
    parser.add_argument("--debug", help="Enter true or false", required=False, default="false")
    
    args = parser.parse_args()
    animal = args.animal
    channel = args.channel
    um = args.um
    atlas = args.atlas
    debug = bool({"true": True, "false": False}[str(args.debug).lower()])
    volumeRegistration = VolumeRegistration(animal, channel, um, atlas, debug)
    volumeRegistration.perform_registration()
