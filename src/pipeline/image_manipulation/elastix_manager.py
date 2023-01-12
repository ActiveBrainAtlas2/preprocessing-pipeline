"""This module takes care of the section to section alignment. It imports
libraries that contain the code from the elastix command line tools:
https://elastix.lumc.nl/
The libraries are contained within the SimpleITK-SimpleElastix library
"""

import os
import numpy as np
from collections import OrderedDict
from sqlalchemy.orm.exc import NoResultFound
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from timeit import default_timer as timer
from subprocess import Popen, PIPE
from pathlib import Path

from database_model.elastix_transformation import ElastixTransformation
from image_manipulation.filelocation_manager import FileLocationManager
from image_manipulation.file_logger import FileLogger
from utilities.utilities_process import get_image_size
from utilities.utilities_registration import (
    align_image_to_affine,
    create_downsampled_transforms,
    parameters_to_rigid_transform,
    register_simple,
    rigid_transform_to_parmeters,
    tif_to_png,
)


class ElastixManager(FileLogger):
    """Class for generating, storing and applying transformations within 
    stack alignment [with the Elastix package]
    All methods relate to aligning images in stack
    """

    def __init__(self, iteration=0):
        self.iteration = iteration
        LOGFILE_PATH = self.fileLocationManager.stack
        super().__init__(LOGFILE_PATH)




    def create_within_stack_transformations(self):
        """Calculate and store the rigid transformation using elastix.  
        The transformations are calculated from the next image to the previous
        This is done in a simple loop with no workers. Usually takes
        up to an hour to run for a stack. It only needs to be run once for
        each brain. We are now using 2 iterations to get better alignment.
        The 2nd pass uses the results of the 1st pass to align
        """
        if self.channel == 1 and self.downsample:
            INPUT = os.path.join(self.fileLocationManager.prep, "CH1", "thumbnail_cleaned")
            if self.iteration == 1:
                INPUT = self.fileLocationManager.get_thumbnail_aligned_iteration_0(self.channel)

            files = sorted(os.listdir(INPUT))
            nfiles = len(files)
            self.logevent(f"INPUT FOLDER: {INPUT}")
            self.logevent(f"FILE COUNT: {nfiles}")

            for i in range(1, nfiles):
                fixed_index = os.path.splitext(files[i - 1])[0]
                moving_index = os.path.splitext(files[i])[0]
                if not self.sqlController.check_elastix_row(self.animal, moving_index, self.iteration):
                    self.calculate_elastix_transformation(INPUT, fixed_index, moving_index)

                    

    def call_alignment_metrics(self):
        """For the metrics value that shows how well the alignment went, 
        elastix needs to be called as a separate program.
        """

        if self.channel == 1 and self.downsample and self.iteration == 1:
            INPUT = os.path.join(self.fileLocationManager.prep, "CH1", "thumbnail_aligned")
            files = sorted(os.listdir(INPUT))
            nfiles = len(files)

            PIPELINE_ROOT = Path('./src/pipeline/scripts').absolute().as_posix()
            program = os.path.join(PIPELINE_ROOT, 'create_alignment_metrics.py')

            for i in range(1, nfiles):
                fixed_index = os.path.splitext(files[i - 1])[0]
                moving_index = os.path.splitext(files[i])[0]
                fixed_file = os.path.join(INPUT, f"{fixed_index}.tif")
                moving_file = os.path.join(INPUT, f"{moving_index}.tif")

                if not self.sqlController.check_elastix_metric_row(self.animal, moving_index, self.iteration): 
                    p = Popen(['python', program, self.animal, fixed_file, moving_file], stdin=PIPE, stdout=PIPE, stderr=PIPE)
                    output, error = p.communicate(b"input data that is passed to subprocess' stdin")
                    if len(output) > 0:
                        metric =  float(''.join(c for c in str(output) if (c.isdigit() or c =='.' or c == '-')))
                        updates = {'metric':metric}
                        self.sqlController.update_elastix_row(self.animal, moving_index, updates)

    def calculate_elastix_transformation(self, INPUT, fixed_index, moving_index):
        """Calculates the rigid transformation from the Elastix output
        and adds it to the database.

        :param INPUT: path of the files
        :param fixed_index: index of fixed image
        :param moving_index: index of moving image
        """
        center = self.get_rotation_center()
        second_transform_parameters, initial_transform_parameters = register_simple(
            INPUT, self.animal, fixed_index, moving_index)
        T1 = parameters_to_rigid_transform(*initial_transform_parameters)
        T2 = parameters_to_rigid_transform(*second_transform_parameters, center)
        T = T1 @ T2
        xshift, yshift, rotation, center = rigid_transform_to_parmeters(T, center)
        self.sqlController.add_elastix_row(
            self.animal, moving_index, rotation, xshift, yshift, self.iteration)

    @staticmethod
    def parameter_elastix_parameter_file_to_dict(filename):
        d = {}
        with open(filename, 'r') as f:
            for line in f.readlines():
                if line.startswith('('):
                    tokens = line[1:-2].split(' ')
                    key = tokens[0]
                    if len(tokens) > 2:
                        value = []
                        for v in tokens[1:]:
                            try:
                                value.append(float(v))
                            except ValueError:
                                value.append(v)
                    else:
                        v = tokens[1]
                        try:
                            value = (float(v))
                        except ValueError:
                            value = v
                    d[key] = value

            return d


    def rigid_transform_to_parmeters(self, transform):
        """convert a 2d transformation matrix (3*3) to the rotation angles, 
        rotation center and translation

        :param transform: (array like): 3*3 array that stores the 2*2 transformation matrix and the 1*2 translation vector for a
            2D image.  the third row of the array is a place holder of values [0,0,1].
        :return tuple: floats of x,y translation, float of rotation
        """

        return rigid_transform_to_parmeters(transform, self.get_rotation_center())


    def parameters_to_rigid_transform(self, rotation: float, xshift: float, yshift: float, center):
        """convert a set of rotation parameters to the transformation matrix

        
        :param rotation: rotation angle in arc
        :param xshift: (float) translation in x
        :param yshift: (float) translation in y
        :param center: (list) list of x and y for the rotation center

        :return array: 3*3 transformation matrix for 2D image, contain the 2*2 array and 1*2 translation vector
        """

        return parameters_to_rigid_transform(rotation, xshift, yshift, center)


    def load_elastix_transformation(self, animal, moving_index, iteration=0):
        """loading the elastix transformation from the database

        :param animal: (str) Animal ID
        :param moving_index: (int) index of moving section

        :return array: 2*2 roatation matrix, float: x translation, float: y translation
        """

        try:
            elastixTransformation = (
                self.sqlController.session.query(ElastixTransformation)
                .filter(ElastixTransformation.prep_id == animal)
                .filter(ElastixTransformation.iteration == iteration)
                .filter(ElastixTransformation.section == moving_index)
                .one()
            )
        except NoResultFound as nrf:
            print("No value for {} {} error: {}".format(animal, moving_index, nrf))
            return 0, 0, 0

        R = elastixTransformation.rotation
        xshift = elastixTransformation.xshift
        yshift = elastixTransformation.yshift
        return R, xshift, yshift


    def get_rotation_center(self):
        """return a rotation center for finding the parameters of a transformation from the transformation matrix

        :return list: list of x and y for rotation center that set as the midpoint of the section that is in the middle of the stack
        """

        INPUT = self.fileLocationManager.get_thumbnail_cleaned(1)
        files = sorted(os.listdir(INPUT))
        midpoint = len(files) // 2
        midfilepath = os.path.join(INPUT, files[midpoint])
        width, height = get_image_size(midfilepath)
        center = np.array([width, height]) / 2
        return center


    def get_transformations(self):
        """After the elastix job is done, this goes into each subdirectory and parses the Transformation.0.txt file
        
        :param animal: the animal
        :return: a dictionary of key=filename, value = coordinates
        """

        sections = self.sqlController.get_sections(self.animal, self.channel)

        midpoint = len(sections) // 2

        transformation_to_previous_sec = {}
        center = self.get_rotation_center()

        for i in range(1, len(sections)):
            rotation, xshift, yshift = self.load_elastix_transformation(self.animal, i, self.iteration)
            T = self.parameters_to_rigid_transform(rotation, xshift, yshift, center)
            transformation_to_previous_sec[i] = T

        transformations = {}

        for moving_index in range(len(sections)):
            filename = str(moving_index).zfill(3) + ".tif"
            if moving_index == midpoint:
                transformations[filename] = np.eye(3)
            elif moving_index < midpoint:
                T_composed = np.eye(3)
                for i in range(midpoint, moving_index, -1):
                    T_composed = np.dot(
                        np.linalg.inv(transformation_to_previous_sec[i]), T_composed
                    )
                transformations[filename] = T_composed
            else:
                T_composed = np.eye(3)
                for i in range(midpoint + 1, moving_index + 1):
                    T_composed = np.dot(transformation_to_previous_sec[i], T_composed)
                transformations[filename] = T_composed
        return transformations


    def align_full_size_image(self, transforms):
        """align the full resolution tif images with the transformations provided.
           All the sections are aligned to the middle sections, the transformation
           of a given section to the middle section is the composite of the transformation
           from the given section through all the intermediate sections to the middle sections.

        :param transforms: (dict): dictionary of transformations that are index by the id of moving sections
        """
        if not self.downsample:
            transforms = create_downsampled_transforms(transforms, downsample=False)
            INPUT = self.fileLocationManager.get_full_cleaned(self.channel)
            OUTPUT = self.fileLocationManager.get_full_aligned_iteration_0(self.channel)
            if self.iteration == 1:
                INPUT = self.fileLocationManager.get_full_aligned_iteration_0(self.channel)
                OUTPUT = self.fileLocationManager.get_full_aligned(self.channel)

            self.logevent(f"INPUT FOLDER: {INPUT}")
            starting_files = os.listdir(INPUT)
            self.logevent(f"FILE COUNT: {len(starting_files)}")
            self.logevent(f"OUTPUT FOLDER: {OUTPUT}")
            self.align_images(INPUT, OUTPUT, transforms)
            progress_id = self.sqlController.get_progress_id(
                downsample=False, channel=self.channel, action="ALIGN"
            )
            self.sqlController.set_task(self.animal, progress_id)


    def align_downsampled_images(self, transforms):
        """align the downsample tiff images

        :param transforms: (dict) dictionary of transformations indexed by id of moving sections
        """

        if self.downsample:
            INPUT = self.fileLocationManager.get_thumbnail_cleaned(self.channel)
            OUTPUT = self.fileLocationManager.get_thumbnail_aligned_iteration_0(self.channel)
            if self.iteration == 1:
                INPUT = self.fileLocationManager.get_thumbnail_aligned_iteration_0(self.channel)
                OUTPUT = self.fileLocationManager.get_thumbnail_aligned(self.channel)

            self.align_images(INPUT, OUTPUT, transforms)
            progress_id = self.sqlController.get_progress_id(
                downsample=True, channel=self.channel, action="ALIGN"
            )
            self.sqlController.set_task(self.animal, progress_id)


    def align_section_masks(self, animal, transforms):
        """function that can be used to align the masks used for cleaning the image.  
        This not run as part of the pipeline, but is used to create the 3d shell 
        around a certain brain

        :param animal: (str) Animal ID
        :param transforms: (array): 3*3 transformation array
        """
        fileLocationManager = FileLocationManager(animal)
        INPUT = fileLocationManager.rotated_and_padded_thumbnail_mask
        OUTPUT = fileLocationManager.rotated_and_padded_and_aligned_thumbnail_mask
        self.align_images(INPUT, OUTPUT, transforms)


    def align_images(self, INPUT, OUTPUT, transforms):
        """function to align a set of images with a with the transformations between them given
        Note: image alignment is memory intensive (but all images are same size)
        6 factor of est. RAM per image for clean/transform needs firmed up but safe

        :param INPUT: (str) directory of images to be aligned
        :param OUTPUT (str): directory output the aligned images
        :param transforms (dict): dictionary of transformations indexed by id of moving sections
        """

        os.makedirs(OUTPUT, exist_ok=True)
        transforms = OrderedDict(sorted(transforms.items()))
        first_file_name = list(transforms.keys())[0]
        infile = os.path.join(INPUT, first_file_name)
        file_keys = []
        for file, T in transforms.items():
            infile = os.path.join(INPUT, file)
            outfile = os.path.join(OUTPUT, file)
            if os.path.exists(outfile):
                continue
            file_keys.append([infile, outfile, T])

        workers = self.get_nworkers() // 2
        start_time = timer()
        self.run_commands_concurrently(align_image_to_affine, file_keys, workers)
        end_time = timer()
        total_elapsed_time = round((end_time - start_time),2)
        print(f'Aligning images took {total_elapsed_time} seconds.')


    def create_web_friendly_sections(self):
        """A function to create section PNG files for the database portal.
        """

        fileLocationManager = FileLocationManager(self.animal)
        INPUT = fileLocationManager.get_thumbnail_aligned(channel=1)
        OUTPUT = fileLocationManager.section_web

        os.makedirs(OUTPUT, exist_ok=True)
        files = sorted(os.listdir(INPUT))
        file_keys = []
        for file in files:
            png = str(file).replace(".tif", ".png")
            infile = os.path.join(INPUT, file)
            outfile = os.path.join(OUTPUT, png)
            if os.path.exists(outfile):
                continue
            file_keys.append([infile, outfile])

        workers = self.get_nworkers()
        self.run_commands_concurrently(tif_to_png, file_keys, workers)


