from lib.TiffSegmentor import TiffSegmentor
import subprocess
from cell_extractor.calculate_mean_cell_image import MeanImageCalculator
from cell_extractor.CellDetector import CellDetector
import os
import argparse
if __name__ =='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--animal', type=str, help='Animal ID')
    parser.add_argument('--disk', type=str, help='storage disk')
    args = parser.parse_args()
    braini = args.animal
    disk = args.disk
    print('starting cell detection for ' + braini)
    segmentor = TiffSegmentor(braini,disk = disk)
    segmentor.generate_tiff_segments(channel = 1,create_csv = False)
    segmentor.generate_tiff_segments(channel = 3,create_csv = True)

    script_folder = os.path.dirname(os.path.realpath(__file__))
    command = f'source ;cd {script_folder}; ./parallel_create_examples {braini}'
    ret = subprocess.run(command, capture_output=True, shell=True)

    MeanImageCalculator(animali)
    workernoshell(['./parallel_calcultate_features',braini])
    detector = CellDetector(braini)
    detector.calculate_and_save_detection_results()


    from cell_extractor.CellDetectorBase import CellDetectorBase 
    from lib.TiffSegmentor import TiffSegmentor