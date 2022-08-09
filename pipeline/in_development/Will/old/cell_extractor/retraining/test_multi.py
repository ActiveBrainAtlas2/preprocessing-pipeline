import sys
sys.path.append('/home/zhw272/programming/pipeline_utility/in_development/Will')
from cell_extractor.CellDetector import detect_cell,detect_cell_multithreshold
detect_cell_multithreshold(animal = 'DK55',round = 2)