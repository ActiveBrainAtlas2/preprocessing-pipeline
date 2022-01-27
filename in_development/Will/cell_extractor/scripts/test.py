from lib.TiffSegmentor import TiffSegmentor
if __name__ =='__main__':
    segmentor = TiffSegmentor('DK60',disk = 'data',n_workers = 10)
    segmentor.move_full_aligned()
    print('ch1')
    segmentor.generate_tiff_segments(channel = 1,create_csv = False)
    print('ch3')
    segmentor.generate_tiff_segments(channel = 3,create_csv = True)
    segmentor.delete_full_aligned()
