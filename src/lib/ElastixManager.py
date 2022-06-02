import os 
import numpy as np
import pandas as pd
from collections import OrderedDict
from sqlalchemy.orm.exc import NoResultFound
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from abakit.lib.FileLocationManager import FileLocationManager
from abakit.lib.utilities_alignment import (create_downsampled_transforms, clean_image)
from abakit.lib.utilities_registration import register_simple,parameters_to_rigid_transform
from abakit.model.elastix_transformation import ElastixTransformation
from lib.pipeline_utilities import get_image_size
class ElastixManager:
    """Class for generating, storing and applying the within stack alignment with the Elastix package
    """    
    def create_within_stack_transformations(self):
        """Calculate and store the rigid transformation using elastix.  The transformations are calculated from the next image to the previous
        """        
        INPUT = os.path.join(self.fileLocationManager.prep, 'CH1', 'thumbnail_cleaned')
        files = sorted(os.listdir(INPUT))
        for i in range(1, len(files)):
            fixed_index = os.path.splitext(files[i-1])[0]
            moving_index = os.path.splitext(files[i])[0]        
            if not self.sqlController.check_elastix_row(self.animal,moving_index):
                second_transform_parameters,initial_transform_parameters = \
                    register_simple(INPUT, fixed_index, moving_index,self.debug)
                T1 = self.parameters_to_rigid_transform(*initial_transform_parameters)
                T2 = self.parameters_to_rigid_transform(*second_transform_parameters, self.get_rotation_center())
                T = T1@T2     
                xshift,yshift,rotation,_ = self.rigid_transform_to_parmeters(T)           
                self.sqlController.add_elastix_row(self.animal, moving_index, rotation, xshift, yshift)
    
    def rigid_transform_to_parmeters(self,transform):
        """convert a 2d transformation matrix (3*3) to the rotation angles, rotation center and translation

        Args:
            transform (array like): 3*3 array that stores the 2*2 transformation matrix and the 1*2 translation vector for a 
            2D image.  the third row of the array is a place holder of values [0,0,1].

        Returns:
            float: x translation
            float: y translation
            float: rotation angle in arc
            list:  lisf of x and y for rotation center
        """        
        R = transform[:2,:2]
        shift = transform[:2,2]
        tan= R[1,0]/R[0,0]
        center = self.get_rotation_center()
        rotation = np.arctan(tan)
        xshift,yshift = shift-center +np.dot(R, center)
        return xshift,yshift,rotation,center

    def parameters_to_rigid_transform(self,rotation, xshift, yshift, center):
        """convert a set of rotation parameters to the transformation matrix

        Args:
            rotation (float): rotation angle in arc
            xshift (float): translation in x
            yshift (float): translation in y
            center (list): list of x and y for the rotation center

        Returns:
            array: 3*3 transformation matrix for 2D image, contain the 2*2 array and 1*2 translation vector
        """        
        return parameters_to_rigid_transform(rotation, xshift, yshift, center)

    def load_elastix_transformation(self,animal, moving_index):
        """loading the elastix transformation from the database

        Args:
            animal (str): Animal ID
            moving_index (int): index of moving section

        Returns:
            array: 2*2 roatation matrix
            float: x translation
            float: y translation
        """        
        try:
            elastixTransformation = self.sqlController.session.query(ElastixTransformation).filter(ElastixTransformation.prep_id == animal)\
                .filter(ElastixTransformation.section == moving_index).one()
        except NoResultFound as nrf:
            print('No value for {} {} error: {}'.format(animal, moving_index, nrf))
            return 0,0,0

        R = elastixTransformation.rotation
        xshift = elastixTransformation.xshift
        yshift = elastixTransformation.yshift
        return R, xshift, yshift

    def get_rotation_center(self):
        """return a rotation center for finding the parameters of a transformation from the transformation matrix

        Returns:
            list: list of x and y for rotation center that set as the midpoint of the section that is in the middle of the stack
        """        
        INPUT = self.fileLocationManager.get_thumbnail_cleaned(self.channel)
        files = sorted(os.listdir(INPUT))
        midpoint = len(files) // 2
        midfilepath = os.path.join(INPUT, files[midpoint])
        width,height = get_image_size(midfilepath)
        center = np.array([width, height]) / 2
        return center

    def get_transformations(self):
        """
        After the elastix job is done, this goes into each subdirectory and parses the Transformation.0.txt file
        Args:
            animal: the animal
        Returns: a dictionary of key=filename, value = coordinates
        """
        INPUT = self.fileLocationManager.get_thumbnail_cleaned(self.channel)
        files = sorted(os.listdir(INPUT))
        midpoint = len(files) // 2
        transformation_to_previous_sec = {}
        center = self.get_rotation_center()
        for i in range(1, len(files)):
            moving_index = os.path.splitext(files[i])[0]
            rotation, xshift, yshift = self.load_elastix_transformation(self.animal, moving_index)
            T = self.parameters_to_rigid_transform(rotation, xshift, yshift, center)
            transformation_to_previous_sec[i] = T
        transformations = {}
        for moving_index in range(len(files)):
            if moving_index == midpoint:
                transformations[files[moving_index]] = np.eye(3)
            elif moving_index < midpoint:
                T_composed = np.eye(3)
                for i in range(midpoint, moving_index, -1):
                    T_composed = np.dot(np.linalg.inv(transformation_to_previous_sec[i]), T_composed)
                transformations[files[moving_index]] = T_composed
            else:
                T_composed = np.eye(3)
                for i in range(midpoint + 1, moving_index + 1):
                    T_composed = np.dot(transformation_to_previous_sec[i], T_composed)
                transformations[files[moving_index]] = T_composed
        return transformations

    def align_full_size_image(self,transforms):
        """align the full resolution tif images with the transformations provided.
           All the sections are aligned to the middle sections, the transformation 
           of a given section to the middle section is the composite of the transformation 
           from the given section through all the intermediate sections to the middle sections.

        Args:
            transforms (dict): dictionary of transformations that are index by the id of moving sections
        """        
        transforms = create_downsampled_transforms(self.animal, transforms, downsample = False)
        INPUT = self.fileLocationManager.get_full_cleaned(self.channel)
        OUTPUT = self.fileLocationManager.get_full_aligned(self.channel)
        self.align_images(INPUT,OUTPUT,transforms)
        progress_id = self.sqlController.get_progress_id(downsample = False, channel = self.channel, action = 'ALIGN')
        self.sqlController.set_task(self.animal, progress_id)

    def align_downsampled_images(self, transforms):
        """align the downsample tiff images

        Args:
            transforms (dict): dictionary of transformations indexed by id of moving sections
        """        
        transforms = create_downsampled_transforms(self.animal, transforms, downsample = True)
        INPUT = self.fileLocationManager.get_thumbnail_cleaned(self.channel)
        OUTPUT = self.fileLocationManager.get_thumbnail_aligned(self.channel)
        self.align_images(INPUT,OUTPUT,transforms)
        progress_id = self.sqlController.get_progress_id(downsample = True, channel = self.channel, action = 'ALIGN')
        self.sqlController.set_task(self.animal, progress_id)

    def align_section_masks(self,animal, transforms):
        """function that can be used to align the masks used for cleaning the image.  This not run as part of 
        the pipeline, but is used to create the 3d shell around a certain brain

        Args:
            animal (str): Animal ID
            transforms (array): 3*3 transformation array
        """        
        fileLocationManager = FileLocationManager(animal)
        INPUT = fileLocationManager.rotated_and_padded_thumbnail_mask
        OUTPUT = fileLocationManager.aligned_rotated_and_padded_thumbnail_mask
        self.align_images(INPUT,OUTPUT,transforms)

    def align_images(self,INPUT,OUTPUT,transforms):
        """function to align a set of images with a with the transformations between them given

        Args:
            INPUT (str): directory of images to be aligned
            OUTPUT (str): directory output the aligned images
            transforms (dict): dictionary of transformations indexed by id of moving sections
        """        
        os.makedirs(OUTPUT, exist_ok=True)
        transforms = OrderedDict(sorted(transforms.items()))
        file_keys = []
        for i, (file, T) in enumerate(transforms.items()):
            infile = os.path.join(INPUT, file)
            outfile = os.path.join(OUTPUT, file)
            if os.path.exists(outfile):
                continue
            file_keys.append([i,infile, outfile, T])
        workers = self.get_nworkers()
        self.run_commands_in_parallel_with_executor([file_keys],workers,clean_image)

    def create_csv_data(self,animal, file_keys):
        """legacy code, I don't think this is used in the pipeline and should be depricated

        Args:
            animal (str): Animal Id
            file_keys (list): list of file input
        """        
        data = []
        for index, infile, outfile, T in file_keys:
            T = np.linalg.inv(T)
            file = os.path.basename(infile)

            data.append({
                'i': index,
                'infile': file,
                'sx': T[0, 0],
                'sy': T[1, 1],
                'rx': T[1, 0],
                'ry': T[0, 1],
                'tx': T[0, 2],
                'ty': T[1, 2],
            })
        df = pd.DataFrame(data)
        df.to_csv(f'/tmp/{animal}.section2sectionalignments.csv', index=False)