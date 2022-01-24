from lib.TiffSegmentor import TiffSegmentor
if __name__ =='__main__':
    segmentor = TiffSegmentor('DK40',disk = 'data',n_workers = 10)
    segmentor.move_full_aligned()
    segmentor.generate_tiff_segments(channel = 1,create_csv = False)
    segmentor.generate_tiff_segments(channel = 3,create_csv = True)
