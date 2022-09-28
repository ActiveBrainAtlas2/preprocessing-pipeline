import sys
import os
sys.path.append(os.path.abspath('./preprocessing-pipeline/pipeline'))
from cell_extractor.QcGenerater import QcGenerater
generater = QcGenerater('DK41',3)
generater.get_sure_and_unsure_cells([500,500])