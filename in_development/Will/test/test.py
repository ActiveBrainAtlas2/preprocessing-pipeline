import sys
sys.path.append('/home/zhw272/programming/pipeline_utility/in_development/Will')
sys.path.append('/home/zhw272/programming/pipeline_utility/src')
from cell_extractor.CellDetectorTrainer import CellDetectorTrainer
trainer = CellDetectorTrainer('DK55',round=2,segmentation_threshold=2700)
features = trainer.load_new_features()