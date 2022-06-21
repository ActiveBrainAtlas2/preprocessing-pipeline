from abakit.lib.FileLocationManager import FileLocationManager
from glob import glob
from multiprocessing.pool import Pool
from lib.utilities_process import workernoshell
import os

animal = "DK55"
manager = FileLocationManager("DK55")
raw_images_root = manager.get_full_aligned()
image_paths = [fn for fn in glob(raw_images_root + "/*")]
image_files = sorted([fn[fn.rfind("/") + 1 : fn.rfind(".")] for fn in image_paths])

save_path = "/data/cvat/" + animal + "/"
if not os.path.exists(save_path):
    os.makedirs(save_path)
commands = []
for filei in image_files:
    print(filei)
    input_path = os.path.join(raw_images_root, filei + ".tif")
    output_file_name = os.path.join(save_path, filei + ".tif")
    cmd = [
        "convert",
        input_path,
        "-resize",
        "12.5%",
        "-depth",
        "8",
        "-compress",
        "lzw",
        output_file_name,
    ]
    commands.append(cmd)
    workernoshell(cmd)

# with Pool(30) as p:
#     p.map(workernoshell, commands)
