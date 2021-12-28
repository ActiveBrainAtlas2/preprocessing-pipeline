from lib.TiffSegmentor import TiffSegmentor
from DKLabInformation import DKLabInformation
import subprocess
from lib.utilities_process import workernoshell
from cell_extractor.calculate_mean_cell_image import MeanImageCalculator
from cell_extractor.CellDetector import CellDetector
info = DKLabInformation
# for braini in info.Jun_brains:
#     segmentor = TiffSegmentor(braini)
#     segmentor.generate_tiff_segments(channel = 1,create_csv = False)
#     segmentor.generate_tiff_segments(channel = 3,create_csv = True)
#     workernoshell(['./parallel_calcultate_examples',braini])
#     MeanImageCalculator(animali)
#     workernoshell(['./parallel_calcultate_features',braini])
#     detector = CellDetector(braini)
#     detector.calculate_and_save_detection_results()

braini = 'DK43'
print('starting cell detection for ' + braini)
segmentor = TiffSegmentor(braini)
segmentor.generate_tiff_segments(channel = 1,create_csv = False)
segmentor.generate_tiff_segments(channel = 3,create_csv = True)
workernoshell(['./parallel_calcultate_examples',braini])
MeanImageCalculator(animali)
workernoshell(['./parallel_calcultate_features',braini])
detector = CellDetector(braini)
detector.calculate_and_save_detection_results()
