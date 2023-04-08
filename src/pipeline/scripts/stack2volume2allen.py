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
import SimpleITK as sitk
from taskqueue import LocalTaskQueue
import igneous.task_creation as tc
import pandas as pd

PIPELINE_ROOT = Path('./src').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())

from library.image_manipulation.neuroglancer_manager import NumpyToNeuroglancer
from library.image_manipulation.filelocation_manager import FileLocationManager
from library.utilities.utilities_mask import normalize16
from library.utilities.utilities_process import read_image
from library.controller.annotation_session_controller import AnnotationSessionController
from library.database_model.annotation_points import AnnotationType
try:
    from settings import host, password, schema, user
except ImportError:
    print('Missing settings using defaults')
    data_path = "/net/birdstore/Active_Atlas_Data/data_root"
    host = "db.dk.ucsd.edu"
    schema = "active_atlas_production"


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
        self.thumbnail_aligned = os.path.join(self.fileLocationManager.prep, self.channel, 'thumbnail_aligned')
        self.moving_volume = os.path.join(self.fileLocationManager.prep, self.channel, 'moving_volume.tif')
        self.fixed_volume = os.path.join(self.fileLocationManager.registration_info, 'fixed_volume.tif')
        self.allen_stack_path = os.path.join(self.fileLocationManager.prep, 'allen_sagittal.tif')
        self.elastix_output = os.path.join(self.fileLocationManager.prep, 'elastix_output')
        self.reverse_elastix_output = os.path.join(self.fileLocationManager.prep, 'reverse_elastix_output')
        self.registered_output = os.path.join(self.fileLocationManager.prep, self.channel,  'registered')
        self.registered_point_file = os.path.join(self.registered_output, 'outputpoints.txt')
        self.unregistered_pickle_file = os.path.join(self.fileLocationManager.prep, 'points.pkl')
        self.unregistered_point_file = os.path.join(self.fileLocationManager.prep, 'points.pts')
        self.neuroglancer_data_path = os.path.join(self.fileLocationManager.neuroglancer_data, f'{self.channel}_{self.atlas}')
        if self.debug:
            self.affineIterations = "250"
            self.bsplineIterations = "150"
        else:
            self.affineIterations = "2500"
            self.bsplineIterations = "15000"
 

    def register_volume(self):
        """This will perform the elastix registration of the volume to the atlas.
        It first does an affine registration, then a bspline registration.
        """

        fixedImage = sitk.ReadImage(self.fixed_volume)
        movingImage = sitk.ReadImage(self.moving_volume)
        elastixImageFilter = sitk.ElastixImageFilter()
        elastixImageFilter.SetFixedImage(fixedImage)
        elastixImageFilter.SetMovingImage(movingImage)

        affineParameterMap = sitk.GetDefaultParameterMap('affine')
        affineParameterMap["MaximumNumberOfIterations"] = [self.affineIterations] # 250 works ok
        affineParameterMap["WriteResultImage"] = ["true"]
        affineParameterMap["ResultImageFormat"] = ["tif"]
        affineParameterMap["ResultImagePixelType"] = ["float"]
        affineParameterMap["NumberOfResolutions"]= ["8"]

        bsplineParameterMap = sitk.GetDefaultParameterMap('bspline')
        bsplineParameterMap["MaximumNumberOfIterations"] = [self.bsplineIterations] # 150 works ok
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
        sitk.WriteImage(resultImage, os.path.join(self.registered_output, 'result.tif'))


    def reverse_register_volume(self):
        """This method also uses an affine and a bspline registration process, but it does 
        it in reverse. The fixed and moving images get switched so we can get the transformation
        for the points to get registered to the atlas. 
        """

        if not os.path.exists(self.unregistered_point_file):
            print(f'No points file at {self.unregistered_point_file}, exiting.')
            sys.exit()

        print('Running registration on points.')
        os.makedirs(self.reverse_elastix_output, exist_ok=True)
        # reverse the volumes for getting the points, doesn't make sense to me.
        fixedImage = sitk.ReadImage(self.moving_volume)
        movingImage = sitk.ReadImage(self.fixed_volume)

        elastixImageFilter = sitk.ElastixImageFilter()
        elastixImageFilter.SetFixedImage(fixedImage)
        elastixImageFilter.SetMovingImage(movingImage)

        affineParameterMap = sitk.GetDefaultParameterMap('affine')
        affineParameterMap["MaximumNumberOfIterations"] = [self.affineIterations] # 250 works ok
        affineParameterMap["WriteResultImage"] = ["false"]
        affineParameterMap["NumberOfResolutions"]= ["8"]

        bsplineParameterMap = sitk.GetDefaultParameterMap('bspline')
        bsplineParameterMap["MaximumNumberOfIterations"] = [self.bsplineIterations] # 150 works ok
        bsplineParameterMap["WriteResultImage"] = ["false"]
        bsplineParameterMap["UseDirectionCosines"] = ["false"]
        bsplineParameterMap["FinalGridSpacingInVoxels"] = [f"{self.um}"]
        del bsplineParameterMap["FinalGridSpacingInPhysicalUnits"]

        elastixImageFilter.SetParameterMap(affineParameterMap)
        elastixImageFilter.AddParameterMap(bsplineParameterMap)
        elastixImageFilter.LogToConsoleOff();
        elastixImageFilter.LogToFileOn();
        elastixImageFilter.SetOutputDirectory(self.reverse_elastix_output)
        elastixImageFilter.SetLogFileName('elastix.log');
        if self.debug:
            elastixImageFilter.PrintParameterMap(bsplineParameterMap)    
        elastixImageFilter.Execute()

    def transformix_volume(self):
        """Helper method when you want to rerun the same transform on another volume
        """

        transformixImageFilter = sitk.TransformixImageFilter()
        parameterMap0 = sitk.ReadParameterFile(os.path.join(self.elastix_output, 'TransformParameters.0.txt'))
        parameterMap1 = sitk.ReadParameterFile(os.path.join(self.elastix_output, 'TransformParameters.1.txt'))
        transformixImageFilter.SetTransformParameterMap(parameterMap0)
        transformixImageFilter.AddTransformParameterMap(parameterMap1)
        movingImage = sitk.ReadImage(self.moving_volume)
        transformixImageFilter.SetMovingImage(movingImage)
        transformixImageFilter.Execute()
        transformed = transformixImageFilter.GetResultImage()
        print(f'new image type {type(transformed)}')
        sitk.WriteImage(transformed, os.path.join(self.registered_output, 'result.tif'))

    def transformix_points(self):
        """Helper method when you want to rerun the same transform on another set of points
        Points are stored in the DB in micrometers from the full resolution images
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
        
        transformixImageFilter = sitk.TransformixImageFilter()
        parameterMap0 = sitk.ReadParameterFile(os.path.join(self.reverse_elastix_output, 'TransformParameters.0.txt'))
        parameterMap1 = sitk.ReadParameterFile(os.path.join(self.reverse_elastix_output, 'TransformParameters.1.txt'))
        transformixImageFilter.SetTransformParameterMap(parameterMap0)
        transformixImageFilter.AddTransformParameterMap(parameterMap1)
        transformixImageFilter.SetFixedPointSetFileName(self.unregistered_point_file)
        transformixImageFilter.LogToFileOn()
        transformixImageFilter.LogToConsoleOff()
        transformixImageFilter.SetOutputDirectory(self.registered_output)
        movingImage = sitk.ReadImage(self.fixed_volume)
        transformixImageFilter.SetMovingImage(movingImage)
        transformixImageFilter.Execute()

        point_or_index = 'OutputPoint'
        d = pd.read_pickle(self.unregistered_pickle_file)
        point_dict = dict(sorted(d.items()))
        controller = AnnotationSessionController(host, password, schema, user)

        with open(self.registered_point_file, "r") as f:                
            lines=f.readlines()
            f.close()
        assert len(lines) == len(point_dict)
        print("\n\n{} points detected\n\n".format(len(lines)))
        source='COMPUTER'
        for structure, i in zip(point_dict.keys(), range(len(lines))):        
            lx=lines[i].split()[lines[i].split().index(point_or_index)+3:lines[i].split().index(point_or_index)+6] #x,y,z
            lf = [float(x) for x in lx]
            x = lf[0]
            y = lf[1]
            z = lf[2]
            brain_region = controller.get_brain_region(structure)
            if brain_region is not None:
                FK_session_id = self.get_annotation_session(brain_region_id=brain_region.id)
                print(source, brain_region.id, x,y,z, FK_session_id)
            else:
                print(f'No brain region found for {structure}')



    def get_annotation_session(self, brain_region_id):
        controller = AnnotationSessionController(host, password, schema, user)
        annotation_session = controller.get_annotation_session(self.animal, brain_region_id, 1)
        return annotation_session.id
        


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

    def create_precomputed(self):
        chunk = 64
        chunks = (chunk, chunk, chunk)
        volumepath = os.path.join(self.registered_output, 'result.tif')
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


    def check_registration(self):
        """Starter method to check for existing directories and files
        """
        status = []
        
        if not os.path.exists(self.fixed_volume):
            status.append(f'\tThere is no fixed volume at {self.fixed_volume}')

        if not os.path.exists(self.moving_volume):
            status.append(f'\tThere is no moving volume at {self.moving_volume}')

        result_path = os.path.join(self.registered_output, 'result.tif')
        if not os.path.exists(result_path):
            status.append(f'\tThere is no registered volume at {result_path}')

        reverse_transformation_pfile = os.path.join(self.reverse_elastix_output, 'TransformParameters.1.txt')
        if not os.path.exists(reverse_transformation_pfile):
            status.append(f'\tThere is no TransformParameters file to register points at: {reverse_transformation_pfile}')

        if not os.path.exists(self.neuroglancer_data_path):
            status.append(f'\tThere is no precomputed data at: {self.neuroglancer_data_path}')

        if os.path.exists(self.unregistered_point_file) and not os.path.exists(self.registered_point_file):
            status.append(f'\tThere are unregisted points at: {self.unregistered_point_file}')
            status.append(f'\tThere are no registed points at: {self.registered_point_file}')


        if len(status) > 0:
            print("These are the processes that have not run:")
            print("\n".join(status))
        else:
            print(f'Everything has been run to register {self.animal} to {self.atlas} with channel {self.channel}.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument("--channel", help="Enter channel", required=False, default=1, type=int)
    parser.add_argument('--um', help="size of Allen atlas in micrometers", required=False, default=20, type=int)
    parser.add_argument('--atlas', help='Enter the atlas', required=False, default='princeton')
    parser.add_argument("--debug", help="Enter true or false", required=False, default="false")
    parser.add_argument("--task", 
                        help="Enter the task you want to perform: \
                          create_volume|register_volume|reverse_register_volume|transformix_volume|tranformix_points|create_precomputed", 
                        required=False, default="check_registration", type=str)
    
    args = parser.parse_args()
    animal = args.animal
    channel = args.channel
    um = args.um
    atlas = args.atlas
    debug = bool({"true": True, "false": False}[str(args.debug).lower()])
    task = args.task
    volumeRegistration = VolumeRegistration(animal, channel, um, atlas, debug)


    function_mapping = {'create_volume': volumeRegistration.create_volume,
                        'register_volume': volumeRegistration.register_volume,
                        'reverse_register_volume': volumeRegistration.reverse_register_volume,
                        'transformix_volume': volumeRegistration.transformix_volume,
                        'transformix_points': volumeRegistration.transformix_points,
                        'create_precomputed': volumeRegistration.create_precomputed,
                        'check_registration': volumeRegistration.check_registration
    }

    function_mapping[task]()
    #volumeRegistration.get_brain_region()

