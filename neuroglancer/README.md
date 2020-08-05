### Adding outside boundaries
1. Get the outside boundaries (masking) defined for each original uncropped foundation brain
using corrected dilation. (MD589 is done, finish the other two for Kui)
1. Check feasibility for using full resolution images in CVAT. (Kui)
1. Mark on CVAT for each foundation brain the external mask and the internal structures for that brain. (Kui)
1. Combine outside masks with internal structures (Kui).
1. Beth/Litao/Kui will verify correct placement of internal structures and correct outside boundaries (for the 3 foundation brains)
1. Ability to insert beads around the boundary of the brain. (Kui)
1. Create two images for CVAT, one with boundary on masked images and one with boundary on unmasked images. (Kui)
### Generating an average brain
1. Start with structures for a foundation brain:
    1. Get pandas dataframe of hand annotations for each foundation brain.
    1. Dataframes are in hd5 format are located on birdstore under the brain name:
    /net/birdstore/Active_Atlas_Data/data_root/CSHL_labelings_v3
    1. Create an atlas for that specific brain with those annotations with:
        1. `cd neuroglancer`
        1. `python build_vollume_colored.py --animal MDXXX`
        1. This will create numpy array and place it at:/net/birdstore/Active_Atlas_Data/data_root/CSHL_volumes/MDXXX/full_brain_volume_annotated.npy
        1. `python convert_vols.py --animal MDXXX`
        1. This will create an annotations directory at:/net/birdstore/Active_Atlas_Data/data_root/CSHL_volumes/MD589/annotations
        1. Copy that directory onto a path available to the web server. That will be the root
        of your precomputed url
1. Create average brain with atlases from the process above.
1. For average brain, there is an numpy array for each structure.
1. Take each of these structures into one numpy array for neuroglancer.
1. Get individual structures into CVAT
1. Find number of persons who annotated each structure from the HDF files
### Neuroglancer fixes
1. Fix the color code with the structure and structure name.
1. Colors in neuroglancer structures are wrong. 7N has two colors in the right side list, but just one color in the actual structure. Have a tight link
between the legend and the actual structure. (Litao)
