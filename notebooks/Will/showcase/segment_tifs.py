from lib.TiffSegmentor import TiffSegmentor
segmentor = TiffSegmentor('DK55')
#segmentor.generate_tiff_segments(channel = 1,create_csv = False)
segmentor.generate_tiff_segments(channel = 3,create_csv = True)
