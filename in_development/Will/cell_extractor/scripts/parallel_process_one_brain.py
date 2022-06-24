import sys
sys.path.append('/home/zhw272/programming/preprocessing-pipeline/in_development/Will')
from cell_extractor.ExampleFinder import create_examples_for_one_section 
from cell_extractor.FeatureFinder import create_features_for_one_section
from cell_extractor.CellDetector import detect_cell
from cell_extractor.CellDetectorBase import parallel_process_all_sections,CellDetectorBase


if __name__ =='__main__':
    animal = 'DK61'
    for threshold in [2100,2200,2300,2700]:
        base = CellDetectorBase(animal)
        sections = base.get_sections_without_example(threshold)
        parallel_process_all_sections(animal,create_examples_for_one_section,disk = '/net/birdstore/Active_Atlas_Data/',segmentation_threshold=threshold,sections=sections,njobs=5)
        sections = base.get_sections_without_features(threshold)
        parallel_process_all_sections(animal,create_features_for_one_section,disk = '/net/birdstore/Active_Atlas_Data/',segmentation_threshold=threshold,sections=sections,njobs=16)
        detect_cell(animal,round=2,segmentation_threshold=threshold)