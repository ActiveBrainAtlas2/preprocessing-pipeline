from src.lib.TiffSegmentor import TiffSegmentor
segmentor = TiffSegmentor('DK55')
segmentor.generate_tiff_segments(channel = 3,create_csv = True)