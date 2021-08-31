import os
from multiprocessing.pool import Pool
import sys
sys.path.append('/home/zhw272/programming/pipeline')
from src.lib.utilities_process import workernoshell
tif_directory = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK55/preps/CH1/full_cleaned/'
save_directory = '/data/cell_segmentation/DK55/'
files = os.listdir(tif_directory)
cmd_list = []
for filei in files:
    file_name = filei[:-4]
    save_folder = save_directory+file_name
    if not os.path.exists(save_folder):
        os.mkdir(save_folder)
    else:
        if len(os.listdir(save_folder)) == 10:
            continue
    file_path = tif_directory + filei
    cmd = [f'convert', tif_directory + filei, '-compress', 'None', '-crop', '2x5-0-0@', '+repage', '+adjoin', f'{save_directory}{file_name}/{file_name}tile-%d.tif']
    workernoshell(cmd)
    # cmd_list.append(cmd)

# print('')
# with Pool(2) as p:
#         p.map(workernoshell, cmd_list)