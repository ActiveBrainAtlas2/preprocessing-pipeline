import sys
from cell_extractor.CellDetectorTrainer import CellDetectorTrainer
trainer = CellDetectorTrainer('DK55',round=2,segmentation_threshold=3000)
features = trainer.load_new_features() 

import os
os.path.getsize(extractor.get_example_save_path())