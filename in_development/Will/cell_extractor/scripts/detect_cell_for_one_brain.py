from cell_extractor.CellDetector import CellDetector
import argparse

def run_from_terminal():
    parser = argparse.ArgumentParser()
    parser.add_argument('--animal', type=str, help='Animal ID')
    parser.add_argument('--disk', type=str, help='storage disk')
    parser.add_argument('--round', type=int, help='model version',default=2)
    args = parser.parse_args()
    braini = args.animal
    disk = args.disk
    round = args.round
    detector = CellDetector(braini,disk = disk,round=round)
    detector.calculate_and_save_detection_results()

def run_as_script():
    for threshold in [2000,3000,4000]:
        detector = CellDetector('DK55',disk = '/net/birdstore/Active_Atlas_Data',round=2,segmentation_threshold=threshold)
        detector.calculate_and_save_detection_results()

if __name__ =='__main__':
    # run_from_terminal()
    run_as_script()
   