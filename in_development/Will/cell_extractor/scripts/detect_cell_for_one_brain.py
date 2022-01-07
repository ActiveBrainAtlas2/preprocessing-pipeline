from cell_extractor.CellDetector import CellDetector
import argparse
if __name__ =='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--animal', type=str, help='Animal ID')
    parser.add_argument('--disk', type=str, help='storage disk')
    args = parser.parse_args()
    braini = args.animal
    disk = args.disk
    detector = CellDetector(braini,disk = disk)
    detector.calculate_and_save_detection_results()
