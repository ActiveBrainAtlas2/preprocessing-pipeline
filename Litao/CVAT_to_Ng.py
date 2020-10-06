import json
import argparse

import numpy as np
import cv2

from utils import get_structure_number, get_segment_properties, NumpyToNeuroglancer


def read_from_cvat(cvat_data_fp):
    '''
    Read labels and vertices of each polygon in every section from cvat structure data.
    :param cvat_data_fp: file path to cvat exported data, a json file
    :return: a dictionary containing vertex coordinates organized by section numbers and structure names
    '''
    cvat_json = json.load(open(cvat_data_fp,'r'))
    
    # Read annotation contours coordinates
    category_dict = {category['id']: category['name'] for category in cvat_json['categories']}
    contours = {}
    for annotation in cvat_json['annotations']:
        section = annotation['image_id']
        if not section in contours.keys():
            contours[section] = {}
            
        landmarks = contours[section]
        structure = category_dict[annotation['category_id']]
        if not structure in landmarks.keys():
            landmarks[structure] = []
            
        polygon = np.array(annotation['segmentation'])
        polygon = np.c_[polygon[0,::2], polygon[0,1::2]]
        landmarks[structure].append(polygon)
        
    return contours

def draw_numpy(section_structure_polygons, section_start, section_end, draw_lines=True):
    volume = np.zeros((downsampled_aligned_shape[1], downsampled_aligned_shape[0], section_end - section_start), dtype=np.uint8)
    for section in tqdm(range(section_start, section_end)):
        if section in section_structure_polygons:
            template = np.zeros((downsampled_aligned_shape[1], downsampled_aligned_shape[0]), dtype=np.uint8)
            for structure in section_structure_polygons[section]:
                polygons = section_structure_polygons[section][structure]
                for polygon in polygons:
                    color = get_structure_number(structure)
                    
                    if draw_lines:
                        cv2.polylines(template, [polygon.astype(np.int32)], True, color, 1)
                    else:
                        for point in polygon:
                            cv2.circle(template, tuple(point.astype(np.int32)), 0, color, -1)

            volume[:, :, section - section_start - 1] = template
        
    volume = np.swapaxes(volume, 0, 1)
    return volume

if __name__=='__main__':
    parser.add_argument("cvat_file", type=str, help="Path to cvat exported file")
    parser.add_argument("precomputed_path", type=str, help="Path to Neuroglancer Precomputed dir")
    parser.add_argument("resolution", type=int, help="How much each pixel represents in nm")
    parser.add_argument("draw_lines", type=bool, help="Whether to draw lines or dots for Neuroglancer", default=True)
    
    args = parser.parse_args()
    cvat_data_fp = configuration(args.cvat_file)
    contours = read_from_cvat(cvat_data_fp)
    volume = draw_numpy(section_structure_polygons, 0, num_section, draw_lines=args.draw_lines)
    
    scales = [args.resolution, args.resolution, 20000]
    
    ng = NumpyToNeuroglancer(volume, scales)
    ng.init_precomputed(args.precompute_path)
    ng.add_segment_properties(get_segment_properties())
    ng.add_downsampled_volumes()
    ng.add_segmentation_mesh()