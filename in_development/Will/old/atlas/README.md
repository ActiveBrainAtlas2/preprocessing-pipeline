### Creating a new atlas from hand annotations
1. Create aligned vertices from the CSV files. The hand annotation files done 
by the anatomists are located at: 
/net/birdstore/Active_Atlas_Data/data_root/atlas_data/foundation_brain_annotations
and are named MDXXX_annotations.csv These files were found from Yuncongs data and
are the best ones I could find after scouring the entires filesystem.


1. Running: `python build_foundationbrain_aligned_data.py` will take the data from
those CSV files and create the aligned data that is then stored in JSON format
in /net/birdstore/Active_Atlas_Data/data_root/atlas_data/atlasV8/MDXXX/aligned_padded_structures.json
There is also data files for the unaligned and unpadded data in the same directory.


1. Next run: `python build_foundationbrain_volumes.py script --debug false`. This will create
the actual numpy volumes and the COM (origin) files. The numpy volumes get stored in:
/net/birdstore/Active_Atlas_Data/data_root/atlas_data/atlasV8/MDXXX/structure 
and the origin files get stored in 
/net/birdstore/Active_Atlas_Data/data_root/atlas_data/atlasV8/MDXXX/origin


1. Next run: `python create_average_atlas.py` file. This will take the data from
the 3 brains above and create an average atlas. It will also create mesh files
that can easily be seen in 3D slicer