from cell_extractor.CellDetectorBase import CellDetectorBase 
from lib.TiffSegmentor import TiffSegmentor
import argparse
import os 
if __name__ =='__main__':
    # parser = argparse.ArgumentParser()
    # parser.add_argument('--animal', type=str, help='Animal ID')
    # args = parser.parse_args()
    # animal = args.animal
    animal = 'DK43'
    base = CellDetectorBase(animal)
    unfinished = base.get_sections_without_example()
    for fi in unfinished:
        os.remove(os.path.join(base.CH3,fi))
        os.remove(os.path.join(base.CH1,fi))
    segmentor = TiffSegmentor(animal)
    segmentor.generate_tiff_segments(channel = 1,create_csv = False)
    segmentor.generate_tiff_segments(channel = 3,create_csv = True)