from pathlib import Path
import numpy as np

def get_origin_and_volumn_dir():
    atlas_dir = Path('/net/birdstore/Active_Atlas_Data/data_root/atlas_data/atlasV8')
    origin_dir = atlas_dir / 'origin'
    volume_dir = atlas_dir / 'structure'
    for origin_file, volume_file in zip(sorted(origin_dir.iterdir()), sorted(volume_dir.iterdir())):
        assert origin_file.stem == volume_file.stem
    return origin_dir,volume_dir

def get_origins():
    origin_dir,volume_dir = get_origin_and_volumn_dir()
    origins = {}
    for origin_file, _ in zip(sorted(origin_dir.iterdir()), sorted(volume_dir.iterdir())):
        name = origin_file.stem
        origins[name] = np.loadtxt(origin_file)
    return origins

def get_volumns():
    origin_dir,volume_dir = get_origin_and_volumn_dir()
    volumns = {}
    for _, volume_file in zip(sorted(origin_dir.iterdir()), sorted(volume_dir.iterdir())):
        name = volume_file.stem
        volume = np.load(volume_file)
        volume = np.rot90(volume, axes=(0, 1))
        volume = np.flip(volume, axis=0)
        volumns[name] = volume
    return volumns

def get_origin_and_volumn():
    origins = get_origins()
    volumns = get_volumns()
    return origins,volumns