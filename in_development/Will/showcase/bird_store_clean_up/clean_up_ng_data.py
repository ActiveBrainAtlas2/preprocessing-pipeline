from abakit.lib.Controllers.SqlController import SqlController
from lib.UrlGenerator import UrlGenerator
from collections import Counter
import numpy as np
import os
from lib.utilities_process import workernoshell

controller = SqlController("DK55")
id_list = controller.get_url_id_list()


def extract_active_ng_folders(image_layers):
    active_folders = []
    print_id = False
    for layer in image_layers:
        source = layer["source"]
        if type(source) == dict:
            source = source["url"]
        assert source[:53] == "precomputed://https://activebrainatlas.ucsd.edu/data/"
        folders = source[53:].split("/")
        active_folders.append(folders)
    return active_folders, print_id


def sort_folders(active_folders):
    prep_ids = [folderi[0] for folderi in active_folders]
    sorted = []
    for prep_id in prep_ids:
        sorted += [folders for folders in active_folders if prep_id == folders[0]]
    return sorted


def get_all_ng_folders():
    root_dir = "/net/birdstore/Active_Atlas_Data/data_root/pipeline_data"
    animals = os.listdir(root_dir)
    ng_folders = []
    for animali in animals:
        if animali == "MD661":
            continue
        folders = os.listdir(root_dir + "/" + animali)
        if "neuroglancer_data" in folders:
            cloud_volumes = os.listdir(
                root_dir + "/" + animali + "/" + "neuroglancer_data"
            )
            cloud_volumes = [
                volumei
                for volumei in cloud_volumes
                if os.path.isdir(
                    os.path.join(root_dir, animali, "neuroglancer_data", volumei)
                )
            ]
            ng_folders += [
                [animali, "neuroglancer_data", volumei] for volumei in cloud_volumes
            ]
    return ng_folders


def get_active_folders():
    active_folders = []
    for id in id_list:
        generator = UrlGenerator()
        url = controller.get_urlModel(id)
        generator.parse_url(url.url)
        image_layers = generator.get_image_layers()
        active_folder, print_id = extract_active_ng_folders(image_layers)
        active_folders += active_folder
        if print_id:
            print(id)
    active_folders = np.unique(active_folders)
    active_folders = sort_folders(active_folders)
    return active_folders


root_dir = "/net/birdstore/Active_Atlas_Data/data_root/pipeline_data"
ng_folders = get_all_ng_folders()
active_folders = get_active_folders()
inactive_folders = [folder for folder in ng_folders if folder not in active_folders]
for folderi in inactive_folders:
    # cmd = ['rm','-rf',folderi]
    # workernoshell(cmd)
    print(folderi)
Sprint("done")
