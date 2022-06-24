import sys
sys.path.append('/data/preprocessing-pipeline/in_development/Will/')
from cell_extractor.ExampleFinder import create_examples_for_one_section 
from cell_extractor.FeatureFinder import create_features_for_one_section
from cell_extractor.CellDetector import detect_cell
from cell_extractor.CellDetectorBase import parallel_process_all_sections


if __name__ =='__main__':
    animal = 'DK40'
    for threshold in [2100,2200,2300,2700]:
        parallel_process_all_sections(animal,create_examples_for_one_section,disk = '/scratch/',segmentation_threshold=threshold,njobs=20)
        parallel_process_all_sections(animal,create_features_for_one_section,disk = '/scratch/',segmentation_threshold=threshold,njobs=40)
        detect_cell(animal,round=2,segmentation_threshold=threshold)