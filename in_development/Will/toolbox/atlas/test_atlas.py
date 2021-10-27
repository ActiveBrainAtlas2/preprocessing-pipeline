from . import Atlas
path1 = '/home/zhw272/Desktop/atlasV8'
path2 = '/net/birdstore/Active_Atlas_Data/data_root/atlas_data/atlasV8'
atlas1 = Atlas(path1)
atlas2 = Atlas(path2)
atlas1.compare_atlas(atlas2)