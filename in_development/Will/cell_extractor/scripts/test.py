import sys
sys.path.append('/data/programming/preprocessing-pipeline/src')
sys.path.append('/data/programming/preprocessing-pipeline/in_development/Will/cell_extractor')
from lib.TiffSegmentor import TiffSegmentor
segmentor = TiffSegmentor('DK40',disk = 'scratch')
segmentor.generate_tiff_segments(channel = 1,create_csv = False)
segmentor.generate_tiff_segments(channel = 3,create_csv = True)
