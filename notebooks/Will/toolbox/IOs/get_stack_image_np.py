import matplotlib.pyplot as plt
from notebooks.Will.toolbox.IOs.get_path import get_subpath_to_tif_files
import os

def get_list_of_tiff(prepi):
    tiff_path = get_subpath_to_tif_files(prepi)
    list_of_tiffs = os.listdir(tiff_path)
    list_of_tiffs = sorted(list_of_tiffs)
    return list_of_tiffs

def get_nsections(prepi):
    list_of_tiffs = get_list_of_tiff(prepi)
    return len(list_of_tiffs)

def load_image(prepi,z=0):
    tiff_path = get_subpath_to_tif_files(prepi)
    list_of_tiffs = get_list_of_tiff(prepi)
    return plt.imread(tiff_path/list_of_tiffs[z])