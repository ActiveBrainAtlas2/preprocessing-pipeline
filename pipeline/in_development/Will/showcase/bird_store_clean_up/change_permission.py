import os
import subprocess
dir = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/'
animals = os.listdir(dir)
for animali in animals:
    path = dir+animali
    folders = os.listdir(path)
    for folderi in folders:
        if folderi in ['histogram','www','neuroglancer_data']:
            os.chmod(os.path.join(path,folderi),0o775)
            # subprocess.Popen(["sudo", "chmod", "0775", os.path.join(path,folderi)], stdout=subprocess.PIPE, shell=True)
        else:
            os.chmod(os.path.join(path,folderi),0o770)
            # subprocess.Popen(["sudo", "chmod", "0770", os.path.join(path,folderi)], stdout=subprocess.PIPE, shell=True)