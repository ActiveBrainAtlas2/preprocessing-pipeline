"""
This gets the CSV data of the 3 foundation brains' annotations.
These annotations were done by Lauren, Beth, Yuncong and Harvey
(i'm not positive about this)
The annotations are full scale vertices.
MD585 section 161,182,223,231,253 annotations are too far south
MD585 off by 100,60,60,80,60
MD589 section 297 too far north
MD594 all good

The contours were done on unaligned sections
this code does the following:
1. gets the transformation needed to align the contours
2. applies them
3. save the result
"""
import argparse
from collections import defaultdict
import os
import sys
import numpy as np
import pandas as pd
import ast
import json
from tqdm import tqdm
from abakit.utilities.shell_tools import get_image_size
from scipy.interpolate import splprep, splev
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility/src')
sys.path.append(PATH)
from lib.utilities_contour_lite import get_contours_from_annotations
from lib.sqlcontroller import SqlController
from lib.file_location import DATA_PATH, FileLocationManager
from lib.utilities_alignment import parse_elastix, \
    transform_points, create_downsampled_transforms
from lib.utilities_atlas import ATLAS
import plotly.graph_objects as go
DOWNSAMPLE_FACTOR = 32

class ContourAligner:
    def __init__(self,animal):
        self.animal = animal
        self.contour_path = os.path.join(DATA_PATH, 'atlas_data','foundation_brain_annotations',f'{self.animal}_annotation.csv')
    
    def create_clean_transform(self):
        sqlController = SqlController(self.animal)
        fileLocationManager = FileLocationManager(self.animal)
        section_size = np.array((sqlController.scan_run.width, sqlController.scan_run.height))
        downsampled_section_size = np.round(section_size / DOWNSAMPLE_FACTOR).astype(int)
        INPUT = os.path.join(fileLocationManager.prep, 'CH1', 'thumbnail')
        files = sorted(os.listdir(INPUT))
        section_offsets = {}
        for file in tqdm(files):
            filepath = os.path.join(INPUT, file)
            width, height = get_image_size(filepath)
            width,height = int(width),int(height)
            downsampled_shape = np.array((width, height))
            section = int(file.split('.')[0])
            section_offsets[section] = (downsampled_section_size - downsampled_shape) / 2
        self.section_offsets = section_offsets

    def interpolate(self,points, new_len):
        points = np.array(points)
        pu = points.astype(int)
        indexes = np.unique(pu, axis=0, return_index=True)[1]
        points = np.array([points[index] for index in sorted(indexes)])
        addme = points[0].reshape(1, 2)
        points = np.concatenate((points, addme), axis=0)
        tck, u = splprep(points.T, u=None, s=3, per=1)
        u_new = np.linspace(u.min(), u.max(), new_len)
        x_array, y_array = splev(u_new, tck, der=0)
        arr_2d = np.concatenate([x_array[:, None], y_array[:, None]], axis=1)
        return list(map(tuple, arr_2d))

    def load_transformation_to_align_contours(self):
        self.create_clean_transform()
        transforms = parse_elastix(self.animal)
        downsampled_transforms = create_downsampled_transforms(self.animal, transforms, downsample=True)
        downsampled_transforms = sorted(downsampled_transforms.items())
        self.transform_per_section = {}
        for section, transform in downsampled_transforms:
            section_num = int(section.split('.')[0])
            transform = np.linalg.inv(transform)
            self.transform_per_section[section_num] = transform

    def load_contours_for_fundation_brains(self):
        sqlController = SqlController(self.animal)
        hand_annotations = pd.read_csv(self.contour_path)
        hand_annotations['vertices'] = hand_annotations['vertices'] \
            .apply(lambda x: x.replace(' ', ',')) \
            .apply(lambda x: x.replace('\n', ',')) \
            .apply(lambda x: x.replace(',]', ']')) \
            .apply(lambda x: x.replace(',,', ',')) \
            .apply(lambda x: x.replace(',,', ',')) \
            .apply(lambda x: x.replace(',,', ',')).apply(lambda x: x.replace(',,', ','))
        hand_annotations['vertices'] = hand_annotations['vertices'].apply(lambda x: ast.literal_eval(x))
        self.contour_per_section_per_structure = defaultdict(dict)
        structures = sqlController.get_structures_dict()
        for structurei, _ in structures.items():
            contour_for_structurei, _, _ = get_contours_from_annotations(self.animal, structurei, hand_annotations, densify=4)
            for section in contour_for_structurei:
                self.contour_per_section_per_structure[structurei][section] = contour_for_structurei[section]

    def aligned_contours(self):
        md585_fixes = {161: 100, 182: 60, 223: 60, 231: 80, 253: 60}
        self.original_structures = defaultdict(dict)
        self.unaligned_centered_structures = defaultdict(dict)
        self.aligned_centered_structures = defaultdict(dict)
        for structure in self.contour_per_section_per_structure:
            for section in self.contour_per_section_per_structure[structure]:
                section = int(section)
                points = np.array(self.contour_per_section_per_structure[structure][section]) / DOWNSAMPLE_FACTOR
                points = self.interpolate(points, max(3000, len(points)))
                self.original_structures[structure][section] = points
                offset = self.section_offsets[section]
                if animal == 'MD585' and section in md585_fixes.keys():
                    offset = offset - np.array([0, md585_fixes[section]])
                if animal == 'MD589' and section == 297:
                    offset = offset + np.array([0, 35])
                points = np.array(points) +  offset
                self.unaligned_centered_structures[structure][section] = points.tolist()
                points = transform_points(points, self.transform_per_section[section]) 
                self.aligned_centered_structures[structure][section] = points.tolist()

    def save_contours(self):
        OUTPUT_DIR = os.path.join(DATA_PATH, 'atlas_data', ATLAS, animal)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        jsonpath1 = os.path.join(OUTPUT_DIR,  'original_structures.json')
        with open(jsonpath1, 'w') as f:
            json.dump(self.original_structures, f, sort_keys=True)
        jsonpath2 = os.path.join(OUTPUT_DIR,  'unaligned_padded_structures.json')
        with open(jsonpath2, 'w') as f:
            json.dump(self.unaligned_centered_structures, f, sort_keys=True)
        jsonpath3 = os.path.join(OUTPUT_DIR,  'aligned_padded_structures.json')
        with open(jsonpath3, 'w') as f:
            json.dump(self.aligned_centered_structures, f, sort_keys=True)

    def plot_contour_of_structurei(self,contours):
        data = []
        for sectioni in contours:
            datai = np.array(contours[sectioni])
            npoints = datai.shape[0]
            datai = np.hstack((datai,np.ones(npoints).reshape(npoints,1)*sectioni))
            data.append(datai)
        data = np.vstack(data)
        fig = go.Figure(data=[go.Scatter3d(x=data[:,0], y=data[:,1], z=data[:,2],mode='markers')])
        fig.show()

    def create_aligned_contours(self):
        self.load_contours_for_fundation_brains()
        self.load_transformation_to_align_contours()
        self.aligned_contours()

    def show_steps(self,structurei='10N_L'):
        self.plot_contour_of_structurei(self.original_structures[structurei])
        self.plot_contour_of_structurei(self.aligned_centered_structures[structurei])

if __name__ == '__main__':
    # parser = argparse.ArgumentParser(description='Work on Animal')
    # parser.add_argument('--animal', help='Enter the animal', required=False)
    # args = parser.parse_args()
    # animal = args.animal
    # if animal is None:
    #     animals = ['MD585', 'MD589', 'MD594']
    # else:
    #     animals = [animal]
    
    animals = ['MD585', 'MD589', 'MD594']
    for animal in animals:
        aligner = ContourAligner(animal)
        aligner.create_aligned_contours()
        # aligner.save_contours()
        aligner.show_steps()