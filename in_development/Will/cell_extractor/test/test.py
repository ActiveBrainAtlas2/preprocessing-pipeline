import sys
sys.path.append('/home/zhw272/programming/preprocessing-pipeline/in_development/Will')
from cell_extractor.CellDetectorBase import CellDetectorBase
from cell_extractor.CellDetector import CellDetector
from cell_extractor.ExampleFinder import create_examples_for_one_section 

create_examples_for_one_section(animal='DK52',section=180,round=2,disk = '/net/birdstore/Active_Atlas_Data/',segmentation_threshold=2100)