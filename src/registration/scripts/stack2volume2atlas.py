"""
Important notes,
If your fixed image has a smaller field of view than your moving image, 
your moving image will be cropped. (This is what happens when the brain stem
gets cropped out. However, when the fixed image is bigger than the moving image, we get the following error:
Too many samples map outside moving image buffer. The moving image needs to be properly initialized.

In other words, only the part your moving image 
that overlap with the fixed image is included in your result image.
To warp the whole image, you can edit the size of the domain in the 
transform parameter map to match your moving image, and pass your moving image and 
the transform parameter map to sitk.Transformix().
10um allen is 1320x800
25um allen is 528x320
aligned volume @ 32 is 2047x1109 - unreg size matches allen10um
aligned volume @ 64 is 1024x555 - unreg size matches allen25um
aligned volume @ 128 is 512x278
aligned volume @50 is 1310x710
full aligned is 65500x35500
Need to scale a moving image as close as possible to the fixed image
COM info:
allen SC: (368, 62, 227)
pred  SC: 369, 64, 219
"""

import argparse
import os
import sys
import numpy as np
from pathlib import Path
from skimage import io
from tqdm import tqdm
import SimpleITK as sitk
import itk
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


class VolumeRegistration:
    """This class takes a downsampled image stack and registers it to the Allen volume    
    """

    def __init__(self, animal, channel, um, atlas, orientation, debug):
        self.animal = animal
        self.debug = debug
        self.atlas = atlas
        self.um = um
        self.channel = f'CH{channel}'
        self.output_dir = f'{self.atlas}{um}um'
        self.scaling_factor = 64 # This is the downsampling factor used to create the aligned volume
        self.fileLocationManager = FileLocationManager(animal)
        self.thumbnail_aligned = os.path.join(self.fileLocationManager.prep, self.channel, 'thumbnail_aligned')
        self.moving_volume_path = os.path.join(self.fileLocationManager.prep, self.channel, 'moving_volume.tif')
        self.fixed_volume_path = os.path.join(self.fileLocationManager.registration_info, f'{atlas}_{um}um_{orientation}.tif')
        self.elastix_output = os.path.join(self.fileLocationManager.prep, 'elastix_output', self.output_dir)
        self.reverse_elastix_output = os.path.join(self.fileLocationManager.prep, 'reverse_elastix_output', self.output_dir)
        self.registered_output = os.path.join(self.fileLocationManager.prep, self.channel,  'registered', self.output_dir)
        self.registered_point_file = os.path.join(self.registered_output, 'outputpoints.txt')
        self.unregistered_pickle_file = os.path.join(self.fileLocationManager.prep, 'points.pkl')
        self.unregistered_point_file = os.path.join(self.fileLocationManager.prep, 'points.pts')
        self.neuroglancer_data_path = os.path.join(self.fileLocationManager.neuroglancer_data, f'{self.channel}_{self.atlas}{um}um')
        self.number_of_sampling_attempts = "10"
        if self.debug:
            self.rigidIterations = "100"
            self.affineIterations = "100"
            self.bsplineIterations = "200"
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
        # simg1 = sitk.Cast(sitk.RescaleIntensity(resultImage), sitk.sitkUInt16)
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

        # The translation is very important as it centers the two volumes
        translateParameterMap = sitk.GetDefaultParameterMap('translation')
        
        rigidParameterMap = sitk.GetDefaultParameterMap('rigid')        
        rigidParameterMap["MaximumNumberOfIterations"] = [self.rigidIterations] # 250 works ok
        
        rigidParameterMap["MaximumNumberOfSamplingAttempts"] = [self.number_of_sampling_attempts]
        rigidParameterMap["UseDirectionCosines"] = ["true"]
        rigidParameterMap["NumberOfResolutions"]= ["6"]
        rigidParameterMap["NumberOfSpatialSamples"] = ["4000"]
        rigidParameterMap["WriteResultImage"] = ["false"]

        
        affineParameterMap = sitk.GetDefaultParameterMap('affine')
        affineParameterMap["UseDirectionCosines"] = ["true"]
        affineParameterMap["MaximumNumberOfIterations"] = [self.affineIterations] # 250 works ok
        affineParameterMap["MaximumNumberOfSamplingAttempts"] = [self.number_of_sampling_attempts]
        affineParameterMap["NumberOfResolutions"]= ["6"]
        affineParameterMap["NumberOfSpatialSamples"] = ["4000"]
        affineParameterMap["WriteResultImage"] = ["false"]

        bsplineParameterMap = sitk.GetDefaultParameterMap('bspline')
        bsplineParameterMap["MaximumNumberOfIterations"] = [self.bsplineIterations] # 150 works ok
        bsplineParameterMap["WriteResultImage"] = ["true"]
        bsplineParameterMap["UseDirectionCosines"] = ["true"]
        bsplineParameterMap["FinalGridSpacingInVoxels"] = [f"{self.um}"]
        bsplineParameterMap["MaximumNumberOfSamplingAttempts"] = [self.number_of_sampling_attempts]
        bsplineParameterMap["NumberOfResolutions"]= ["6"]
        bsplineParameterMap["GridSpacingSchedule"] = ["6.219", "4.1", "2.8", "1.9", "1.4", "1.0"]
        bsplineParameterMap["NumberOfSpatialSamples"] = ["4000"]
        del bsplineParameterMap["FinalGridSpacingInPhysicalUnits"]

        elastixImageFilter.SetParameterMap(translateParameterMap)
        elastixImageFilter.AddParameterMap(rigidParameterMap)
        elastixImageFilter.AddParameterMap(affineParameterMap)
        elastixImageFilter.AddParameterMap(bsplineParameterMap)
        elastixImageFilter.SetOutputDirectory(outputpath)
        elastixImageFilter.LogToFileOn();
        elastixImageFilter.LogToConsoleOff()
        elastixImageFilter.SetLogFileName('elastix.log');
        if self.debug:
            elastixImageFilter.PrintParameterMap(translateParameterMap)    
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
        parameterMap3 = sitk.ReadParameterFile(os.path.join(outputpath, 'TransformParameters.3.txt'))
        transformixImageFilter.SetTransformParameterMap(parameterMap0)
        transformixImageFilter.AddTransformParameterMap(parameterMap1)
        transformixImageFilter.AddTransformParameterMap(parameterMap2)
        transformixImageFilter.AddTransformParameterMap(parameterMap3)
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

    def transformix_pointsXXX(self):
        """Helper method when you want to rerun the transform on a set of points.
        Get the pickle file and transform it. It is in full resolution pixel size.
        The points in the pickle file need to be translated from full res pixel to
        the current resolution of the downsampled volume.
        Points are inserted in the DB in micrometers from the full resolution images

        
        The points.pts file takes THIS format:
        point
        3
        102.8 -33.4 57.0
        178.1 -10.9 14.5
        180.4 -18.1 78.9
        """
        d = pd.read_pickle(self.unregistered_pickle_file)
        point_dict = dict(sorted(d.items()))
        with open(self.unregistered_point_file, 'w') as f:
            f.write('point\n')
            f.write(f'{len(point_dict)}\n')
            for _, points in point_dict.items():
                x = points[0]/self.scaling_factor
                y = points[1]/self.scaling_factor
                z = points[2] # the z is not scaled
                #print(structure, points, x,y,z)
                f.write(f'{x} {y} {z}')
                f.write('\n')
        
        transformixImageFilter = self.setup_transformix(self.reverse_elastix_output)
        transformixImageFilter.SetFixedPointSetFileName(self.unregistered_point_file)
        transformixImageFilter.Execute()

    def transformix_points(self):
        """Helper method when you want to rerun the transform on a set of points.
        Get the pickle file and transform it. It is in full resolution pixel size.
        The points in the pickle file need to be translated from full res pixel to
        the current resolution of the downsampled volume.
        Points are inserted in the DB in micrometers from the full resolution images

        
        The points.pts file takes THIS format:
        point
        3
        102.8 -33.4 57.0
        178.1 -10.9 14.5
        180.4 -18.1 78.9
        """
        controller = AnnotationSessionController(animal=self.animal)
        d = pd.read_pickle(self.unregistered_pickle_file)
        point_dict = dict(sorted(d.items()))
        input_points = itk.PointSet[itk.F, 3].New()
        """
        with open(self.unregistered_point_file, 'w') as f:
            f.write('point\n')
            f.write(f'{len(point_dict)}\n')
            for _, points in point_dict.items():
                x = points[0]/self.scaling_factor
                y = points[1]/self.scaling_factor
                z = points[2] # the z is not scaled
                #print(structure, points, x,y,z)
                f.write(f'{x} {y} {z}')
                f.write('\n')
        """
        for structure, points in point_dict.items():
            x = points[0]/self.scaling_factor
            y = points[1]/self.scaling_factor
            z = points[2] # the z is not scaled
            points = [x,y,z]
            print(structure, points)
            brain_region = controller.get_brain_region(structure)
            if brain_region is not None:
                input_points.GetPoints().InsertElement(brain_region.id, points)
                #init_points.GetPoints().InsertElement(idx, init_transform.TransformPoint(point))

        print(input_points)


    def insert_points(self):
        """This method will take the pickle file of COMs and insert them.
        The COMs in the pickle files are in pixel coordinates.
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
        controller = AnnotationSessionController(self.animal)

        with open(self.registered_point_file, "r") as f:                
            lines=f.readlines()
            f.close()

        if len(lines) != len(point_dict):
            print(f'Length {os.path.basename(self.registered_point_file)}: {len(lines)} does not match {os.path.basename(self.unregistered_pickle_file)}: {len(point_dict)}')
            sys.exit()
        print("\n\n{} points detected\n\n".format(len(lines)))
        for structure, i in zip(point_dict.keys(), range(len(lines))):        
            lx=lines[i].split()[lines[i].split().index(point_or_index)+3:lines[i].split().index(point_or_index)+6] #x,y,z
            lf = [float(x) for x in lx]
            x = lf[0] * self.um
            y = lf[1] * self.um
            z = lf[2] * self.um
            brain_region = controller.get_brain_region(structure)
            if brain_region is not None:
                annotation_session = controller.get_annotation_session(self.animal, brain_region.id, 1)
                entry = {'source': source, 'FK_session_id': annotation_session.id, 'x': x, 'y':y, 'z': z}
                controller.upsert_structure_com(entry)
            else:
                print(f'No brain region found for {structure}')

            if self.debug and brain_region is not None:
                #lf = [round(l) for l in lf]
                print(annotation_session.id, self.animal, brain_region.id, source, 
                      structure, lf, x, int(y), int(z), lx)


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

    def create_itk(self):
        os.makedirs(self.registered_output, exist_ok=True)

        fixed_image = itk.imread(self.fixed_volume_path, itk.F)
        moving_image = itk.imread(self.moving_volume_path, itk.F)
        # init transform start
        # Translate to roughly position sample data on top of CCF data

        init_transform = itk.VersorRigid3DTransform[
            itk.D
        ].New()  # Represents 3D rigid transformation with unit quaternion
        init_transform.SetIdentity()

        transform_initializer = itk.CenteredVersorTransformInitializer[
            type(fixed_image), type(moving_image)
        ].New()
        transform_initializer.SetFixedImage(fixed_image)
        transform_initializer.SetMovingImage(moving_image)
        transform_initializer.SetTransform(init_transform)
        transform_initializer.GeometryOn()  # We compute translation between the center of each image
        transform_initializer.ComputeRotationOff()  # We have previously verified that spatial orientation aligns
        transform_initializer.InitializeTransform()
        # initializer maps from the fixed image to the moving image,
        # whereas we want to map from the moving image to the fixed image.
        init_transform = init_transform.GetInverseTransform()
        # init transform end
        # Apply translation without resampling the image by updating the image origin directly
        change_information_filter = itk.ChangeInformationImageFilter[type(moving_image)].New()
        change_information_filter.SetInput(moving_image)
        change_information_filter.SetOutputOrigin(
            init_transform.TransformPoint(itk.origin(moving_image))
        )
        change_information_filter.ChangeOriginOn()
        change_information_filter.UpdateOutputInformation()
        source_image_init = change_information_filter.GetOutput()
        # end apply translation        

        parameter_object = itk.ParameterObject.New()
        rigid_parameter_map = parameter_object.GetDefaultParameterMap('rigid')
        affine_parameter_map = parameter_object.GetDefaultParameterMap('affine')
        bspline_parameter_map = parameter_object.GetDefaultParameterMap("bspline")
        bspline_parameter_map["FinalGridSpacingInVoxels"] = (f"{self.um}",)
        parameter_object.AddParameterMap(rigid_parameter_map)
        parameter_object.AddParameterMap(affine_parameter_map)
        parameter_object.AddParameterMap(bspline_parameter_map)
        parameter_object.RemoveParameter("FinalGridSpacingInPhysicalUnits")
        registration_method = itk.ElastixRegistrationMethod[type(fixed_image), type(moving_image)
        ].New(
            fixed_image=fixed_image,
            moving_image=source_image_init,
            parameter_object=parameter_object,
            log_to_console=False,
        )
        registration_method.Update()
        resultImage = registration_method.GetOutput()


        itk.imwrite(resultImage, os.path.join(self.registered_output, 'result.tif'), compression=True) 
        ## write transformation 
        os.makedirs(self.registered_output, exist_ok=True)
        outputpath = os.path.join(self.registered_output, 'init-transform.hdf5')
        itk.transformwrite([init_transform], outputpath)
        for index in range(parameter_object.GetNumberOfParameterMaps()):
            outputpath = os.path.join(self.registered_output, f'elastix-transform.{index}.txt')
            registration_method.GetTransformParameterObject().WriteParameterFile(
                registration_method.GetTransformParameterObject().GetParameterMap(index), outputpath) 

    def create_volume(self):
        """Create a 3D volume of the image stack
        """
        
        files, volume_size = self.get_file_information()
        image_stack = np.zeros(volume_size)
        file_list = []
        for ffile in tqdm(files):
            fpath = os.path.join(self.thumbnail_aligned, ffile)
            farr = read_image(fpath)
            #farr = farr[200:-200,200:-200]
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

        reverse_transformation_pfile = os.path.join(self.reverse_elastix_output, 'TransformParameters.3.txt')
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
    parser.add_argument('--um', help="size of atlas in micrometers", required=False, default=25, type=int)
    parser.add_argument('--atlas', help='Enter the atlas: allen|princeton', required=False, default='allen')
    parser.add_argument('--orientation', help='Enter the orientation: sagittal|coronal', required=False, default='sagittal')
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
    orientation = args.orientation
    debug = bool({"true": True, "false": False}[str(args.debug).lower()])
    task = str(args.task).strip().lower()
    volumeRegistration = VolumeRegistration(animal, channel, um, atlas, orientation, debug)


    function_mapping = {'create_volume': volumeRegistration.create_volume,
                        'register_volume': volumeRegistration.register_volume,
                        'reverse_register_volume': volumeRegistration.reverse_register_volume,
                        'transformix_volume': volumeRegistration.transformix_volume,
                        'transformix_points': volumeRegistration.transformix_points,
                        'create_precomputed': volumeRegistration.create_precomputed,
                        'check_registration': volumeRegistration.check_registration,
                        'insert_points': volumeRegistration.insert_points,
                        'create_itk': volumeRegistration.create_itk
    }

    if task in function_mapping:
        function_mapping[task]()
    else:
        print(f'{task} is not a correct task. Choose one of these:')
        for key in function_mapping.keys():
            print(f'\t{key}')

