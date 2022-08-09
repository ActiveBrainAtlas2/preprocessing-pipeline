import sys
sys.path.append('/data/preprocessing-pipeline/in_development/Will')
from cell_extractor.CellDetectorBase import CellDetectorBase
from cell_extractor.CellDetector import CellDetector
from cell_extractor.ExampleFinder import create_examples_for_one_section 

create_examples_for_one_section(animal='DK4',section=180,round=2,disk = '/scratch/',segmentation_threshold=2100)