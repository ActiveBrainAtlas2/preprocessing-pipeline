import sys
import os
sys.path.append(os.path.abspath('./../../'))
<<<<<<< HEAD
sys.path.append(os.path.abspath('./../../../../'))
=======
sys.path.append(os.path.abspath('./../../../..'))
>>>>>>> 2d52f2b60e8bf5ce3733212d185a43876c71056f
from cell_extractor.ExampleFinder import create_examples_for_one_section 
from cell_extractor.FeatureFinder import create_features_for_one_section
from cell_extractor.CellDetector import detect_cell
from cell_extractor.CellDetectorBase import parallel_process_all_sections,CellDetectorBase


if __name__ =='__main__':
    # animal = 'DK54'
    for animal in ['DK60']:
        for threshold in [2100,2200,2300,2700]:
            base = CellDetectorBase(animal)
            sections = base.get_sections_without_example(threshold)
<<<<<<< HEAD
            parallel_process_all_sections(animal,create_examples_for_one_section,disk = '/net/birdstore/Active_Atlas_Data',segmentation_threshold=threshold,sections=sections,njobs=20)
            sections = base.get_sections_without_features(threshold)
            parallel_process_all_sections(animal,create_features_for_one_section,disk = '/net/birdstore/Active_Atlas_Data',segmentation_threshold=threshold,sections=sections,njobs=20)
=======
            parallel_process_all_sections(animal,create_examples_for_one_section,disk = '/net/birdstore/Active_Atlas_Data',segmentation_threshold=threshold,sections=sections,njobs=70)
            sections = base.get_sections_without_features(threshold)
            parallel_process_all_sections(animal,create_features_for_one_section,disk = '/net/birdstore/Active_Atlas_Data',segmentation_threshold=threshold,sections=sections,njobs=100)
>>>>>>> 2d52f2b60e8bf5ce3733212d185a43876c71056f
            detect_cell(animal,round=2,segmentation_threshold=threshold)
