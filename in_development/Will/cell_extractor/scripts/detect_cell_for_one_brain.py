from cell_extractor.CellDetector import CellDetector
import argparse

def run_from_terminal():
    parser = argparse.ArgumentParser()
    parser.add_argument('--animal', type=str, help='Animal ID')
    parser.add_argument('--disk', type=str, help='storage disk')
    args = parser.parse_args()
    braini = args.animal
    disk = args.disk
    detector = CellDetector(braini,disk = disk)
    detector.calculate_and_save_detection_results()

def run_as_script():
    detector = CellDetector('DK43',disk = 'data')
    detector.calculate_and_save_detection_results()

if __name__ =='__main__':
    run_from_terminal()
    # run_as_script()
   