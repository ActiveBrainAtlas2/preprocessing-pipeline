import sys
sys.path.append('/home/zhw272/programming/preprocessing-pipeline/in_development/Will')
from cell_extractor.CellDetectorBase import CellDetectorBase
from cell_extractor.CellDetector import CellDetector
detector = CellDetector(animal = 'DK55',round=2)
