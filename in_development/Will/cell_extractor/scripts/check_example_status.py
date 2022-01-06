from cell_extractor.CellDetectorBase import CellDetectorBase 
from lib.TiffSegmentor import TiffSegmentor
import argparse

if __name__ =='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--animal', type=str, help='Animal ID')
    args = parser.parse_args()
    base = CellDetectorBase(args.animal)
    unfinished = base.get_sections_without_example()
    for fi in unfinished:
        print(fi)