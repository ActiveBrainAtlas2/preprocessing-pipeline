"""
This script will

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
import urllib

PIPELINE_ROOT = Path('./src').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())

from library.image_manipulation.neuroglancer_manager import NumpyToNeuroglancer
from library.image_manipulation.filelocation_manager import FileLocationManager
from library.utilities.utilities_mask import normalize16
from library.utilities.utilities_process import read_image
from library.controller.annotation_session_controller import AnnotationSessionController
from library.database_model.annotation_points import StructureCOM
try:
    from settings import host, password, schema, user
except ImportError:
    print('Missing settings using defaults')
    data_path = "/net/birdstore/Active_Atlas_Data/data_root"
    host = "db.dk.ucsd.edu"
    schema = "active_atlas_production"

password = urllib.parse.quote_plus(str(password))

class VolumeRegistration:
    """This class takes a downsampled image stack and registers it to the Allen volume    
    """

    def __init__(self, animal, channel, um, atlas, debug):
        self.animal = animal
        self.debug = debug
        self.atlas = atlas
        self.um = um
        self.channel = f'CH{channel}'
        self.output_dir = f'{self.atlas}{um}um'
        self.scaling_factor = 128 # This is the downsampling factor used to create the aligned volume
        self.fileLocationManager = FileLocationManager(animal)
        self.thumbnail_aligned = os.path.join(self.fileLocationManager.prep, self.channel, 'thumbnail_aligned')
        self.moving_volume_path = os.path.join(self.fileLocationManager.prep, self.channel, 'moving_volume.tif')
        self.fixed_volume_path = os.path.join(self.fileLocationManager.registration_info, f'{atlas}_{um}um_sagittal.tif')
        self.elastix_output = os.path.join(self.fileLocationManager.prep, 'elastix_output', self.output_dir)
        self.reverse_elastix_output = os.path.join(self.fileLocationManager.prep, 'reverse_elastix_output', self.output_dir)
        self.registered_output = os.path.join(self.fileLocationManager.prep, self.channel,  'registered', self.output_dir)
        self.registered_point_file = os.path.join(self.registered_output, 'outputpoints.txt')
        self.unregistered_pickle_file = os.path.join(self.fileLocationManager.prep, 'points.pkl')
        self.unregistered_point_file = os.path.join(self.fileLocationManager.prep, 'points.pts')
        self.neuroglancer_data_path = os.path.join(self.fileLocationManager.neuroglancer_data, f'{self.channel}_{self.atlas}{um}um')
        self.number_of_sampling_attempts = "8"
        if self.debug:
            self.rigidIterations = "100"
            self.affineIterations = "100"
            self.bsplineIterations = "100"
        else:
            self.rigidIterations = "1000"
            self.affineIterations = "2500"
            self.bsplineIterations = "15000"

        if not os.path.exists(self.fixed_volume_path):
            print(f'{self.fixed_volume_path} does not exist, exiting.')
            sys.exit()

        
 

    def register_volume(self):
        """This will perform the elastix registration of the volume to the atlas.
        It first does an affine registration, then a bspline registration.
        """
        
        os.makedirs(self.elastix_output, exist_ok=True)
        os.makedirs(self.registered_output, exist_ok=True)

        elastixImageFilter = self.setup_registration(self.fixed_volume_path, self.moving_volume_path, self.elastix_output)
        resultImage = elastixImageFilter.Execute()         
        sitk.WriteImage(resultImage, os.path.join(self.registered_output, 'result.tif'))


    def reverse_register_volume(self):
        """This method also uses an affine and a bspline registration process, but it does 
        it in reverse. The fixed and moving images get switched so we can get the transformation
        for the points to get registered to the atlas. 
        """

        os.makedirs(self.reverse_elastix_output, exist_ok=True)

        # switch moving and fixed
        elastixImageFilter = self.setup_registration(self.moving_volume_path, self.fixed_volume_path, self.reverse_elastix_output)
        elastixImageFilter.Execute()

    def setup_registration(self, imagepath1, imagepath2, outputpath):
        fixedImage = sitk.ReadImage(imagepath1)
        movingImage = sitk.ReadImage(imagepath2)
        elastixImageFilter = sitk.ElastixImageFilter()
        elastixImageFilter.SetFixedImage(fixedImage)
        elastixImageFilter.SetMovingImage(movingImage)

        rigidParameterMap = sitk.GetDefaultParameterMap('rigid')        
        rigidParameterMap["MaximumNumberOfIterations"] = [self.rigidIterations] # 250 works ok
        rigidParameterMap["WriteResultImage"] = ["false"]
        rigidParameterMap["MaximumNumberOfSamplingAttempts"] = [self.number_of_sampling_attempts]
        rigidParameterMap["NumberOfResolutions"]= ["6"]
        
        affineParameterMap = sitk.GetDefaultParameterMap('affine')
        affineParameterMap["MaximumNumberOfIterations"] = [self.affineIterations] # 250 works ok
        affineParameterMap["WriteResultImage"] = ["false"]
        affineParameterMap["MaximumNumberOfSamplingAttempts"] = [self.number_of_sampling_attempts]
        affineParameterMap["NumberOfResolutions"]= ["6"]

        bsplineParameterMap = sitk.GetDefaultParameterMap('bspline')
        bsplineParameterMap["MaximumNumberOfIterations"] = [self.bsplineIterations] # 150 works ok
        bsplineParameterMap["WriteResultImage"] = ["false"]
        bsplineParameterMap["UseDirectionCosines"] = ["false"]
        bsplineParameterMap["FinalGridSpacingInVoxels"] = [f"{self.um}"]
        bsplineParameterMap["MaximumNumberOfSamplingAttempts"] = [self.number_of_sampling_attempts]
        bsplineParameterMap["NumberOfResolutions"]= ["6"]
        bsplineParameterMap["GridSpacingSchedule"] = ["6.219", "4.1", "2.8", "1.9", "1.4", "1.0"]
        del bsplineParameterMap["FinalGridSpacingInPhysicalUnits"]

        elastixImageFilter.SetParameterMap(rigidParameterMap)
        elastixImageFilter.AddParameterMap(affineParameterMap)
        elastixImageFilter.AddParameterMap(bsplineParameterMap)
        elastixImageFilter.LogToConsoleOff();
        elastixImageFilter.LogToFileOn();
        elastixImageFilter.SetOutputDirectory(outputpath)
        elastixImageFilter.SetLogFileName('elastix.log');
        if self.debug:
            elastixImageFilter.PrintParameterMap(rigidParameterMap)    
            elastixImageFilter.PrintParameterMap(affineParameterMap)
            elastixImageFilter.PrintParameterMap(bsplineParameterMap)
        return elastixImageFilter

        

    def setup_transformix(self, outputpath):
        """Method used to transform volumes and points
        """
        
        os.makedirs(self.registered_output, exist_ok=True)

        transformixImageFilter = sitk.TransformixImageFilter()
        parameterMap0 = sitk.ReadParameterFile(os.path.join(outputpath, 'TransformParameters.0.txt'))
        parameterMap1 = sitk.ReadParameterFile(os.path.join(outputpath, 'TransformParameters.1.txt'))
        parameterMap2 = sitk.ReadParameterFile(os.path.join(outputpath, 'TransformParameters.2.txt'))
        transformixImageFilter.SetTransformParameterMap(parameterMap0)
        transformixImageFilter.AddTransformParameterMap(parameterMap1)
        transformixImageFilter.AddTransformParameterMap(parameterMap2)
        transformixImageFilter.LogToFileOn()
        transformixImageFilter.LogToConsoleOff()
        transformixImageFilter.SetOutputDirectory(self.registered_output)
        movingImage = sitk.ReadImage(self.moving_volume_path)
        transformixImageFilter.SetMovingImage(movingImage)
        return transformixImageFilter

    def transformix_volume(self):
        """Helper method when you want to rerun the same transform on another volume
        """
        
        transformixImageFilter = self.setup_transformix(self.elastix_output)
        transformixImageFilter.Execute()
        transformed = transformixImageFilter.GetResultImage()
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
        
        transformixImageFilter = self.setup_transformix(self.reverse_elastix_output)
        transformixImageFilter.SetFixedPointSetFileName(self.unregistered_point_file)
        transformixImageFilter.Execute()



    def insert_points(self):
        """This method will take the pickle file of COMs and insert them.
        For typical COMs, the full scaled xy version gets multiplied by 0.325 then inserted
        Upon retrieval, xy gets: divided by 0.325. Here we scale by our downsampling factor when we created the volume,
        then multiple by the scan run resolution which is hard coded below.
        """

        if not os.path.exists(self.unregistered_pickle_file):
            print(f'{self.unregistered_pickle_file} does not exist, exiting.')
            sys.exit()
        if not os.path.exists(self.registered_point_file):
            print(f'{self.registered_point_file} does not exist, exiting.')
            sys.exit()

        point_or_index = 'OutputPoint'
        source='COMPUTER'
        d = pd.read_pickle(self.unregistered_pickle_file)
        point_dict = dict(sorted(d.items()))
        controller = AnnotationSessionController(host, password, schema, user)

        with open(self.registered_point_file, "r") as f:                
            lines=f.readlines()
            f.close()

        if len(lines) != len(point_dict):
            print(f'Length {os.path.basename(self.registered_point_file)}: {len(lines)} does not match {os.path.basename(self.unregistered_pickle_file)}: {len(point_dict)}')
            sys.exit()
        print("\n\n{} points detected\n\n".format(len(lines)))
        print(host, password, user, schema)
        for structure, i in zip(point_dict.keys(), range(len(lines))):        
            lx=lines[i].split()[lines[i].split().index(point_or_index)+3:lines[i].split().index(point_or_index)+6] #x,y,z
            lf = [float(x) for x in lx]
            x = lf[0] * self.scaling_factor * 0.325
            y = lf[1] * self.scaling_factor * 0.325
            z = lf[2] * 20 
            brain_region = controller.get_brain_region(structure)
            if brain_region is not None:
                annotation_session = controller.get_annotation_session(self.animal, brain_region.id, 1)
                entry = {'source': source, 'FK_session_id': annotation_session.id, 'x': x, 'y':y, 'z': z}
                controller.upsert_structure_com(entry)
            else:
                print(f'No brain region found for {structure}')

            if self.debug and brain_region is not None:
                print(annotation_session.id, self.animal, brain_region.id, source, structure, lf, x,y)

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
        io.imsave(self.moving_volume_path, image_stack.astype(np.uint16))
        print(f'Saved a 3D volume {self.moving_volume_path} with shape={image_stack.shape} and dtype={image_stack.dtype}')

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
        
        if os.path.exists(self.fixed_volume_path):
            status.append(f'\tFixed volume at {self.fixed_volume_path}')

        if os.path.exists(self.moving_volume_path):
            status.append(f'\tMoving volume at {self.moving_volume_path}')

        result_path = os.path.join(self.registered_output, 'result.tif')
        if os.path.exists(result_path):
            status.append(f'\tRegistered volume at {result_path}')

        reverse_transformation_pfile = os.path.join(self.reverse_elastix_output, 'TransformParameters.2.txt')
        if os.path.exists(reverse_transformation_pfile):
            status.append(f'\tTransformParameters file to register points at: {reverse_transformation_pfile}')

        if os.path.exists(self.neuroglancer_data_path):
            status.append(f'\tPrecomputed data at: {self.neuroglancer_data_path}')

        if os.path.exists(self.unregistered_pickle_file):
            status.append(f'\tCOM pickle data at: {self.unregistered_pickle_file}')

        if os.path.exists(self.unregistered_point_file):
            status.append(f'\tUnnregisted points at: {self.unregistered_point_file}')

        if os.path.exists(self.registered_point_file):
            status.append(f'\tRegisted points at: {self.registered_point_file}')


        if len(status) > 0:
            print("These are the processes that have run:")
            print("\n".join(status))
        else:
            print(f'Nothing has been run to register {self.animal} to {self.atlas} with channel {self.channel}.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument("--channel", help="Enter channel", required=False, default=1, type=int)
    parser.add_argument('--um', help="size of atlas in micrometers", required=False, default=20, type=int)
    parser.add_argument('--atlas', help='Enter the atlas: allen|princeton', required=False, default='princeton')
    parser.add_argument("--debug", help="Enter true or false", required=False, default="false")
    parser.add_argument("--task", 
                        help="Enter the task you want to perform: \
                          create_volume|register_volume|reverse_register_volume|transformix_volume|tranformix_points|create_precomputed|insert_points", 
                        required=False, default="check_registration", type=str)
    
    args = parser.parse_args()
    animal = args.animal
    channel = args.channel
    um = args.um
    atlas = args.atlas
    debug = bool({"true": True, "false": False}[str(args.debug).lower()])
    task = str(args.task).strip().lower()
    volumeRegistration = VolumeRegistration(animal, channel, um, atlas, debug)


    function_mapping = {'create_volume': volumeRegistration.create_volume,
                        'register_volume': volumeRegistration.register_volume,
                        'reverse_register_volume': volumeRegistration.reverse_register_volume,
                        'transformix_volume': volumeRegistration.transformix_volume,
                        'transformix_points': volumeRegistration.transformix_points,
                        'create_precomputed': volumeRegistration.create_precomputed,
                        'check_registration': volumeRegistration.check_registration,
                        'insert_points': volumeRegistration.insert_points
    }

    if task in function_mapping:
        function_mapping[task]()
    else:
        print(f'{task} is not a correct task.')

