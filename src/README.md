1. create_alignment.py - Performs section to sectio alignment
1. create_clean.py - Takes the maks and does a bit wise ann to clean image.
2. 1. create_masks.py - Creates the masks which are used to clean the images.
3. create_different_mesh.py - Creates a mesh segmentation layer for neuroglancer
4. create_downsampling.py - 2nd phase in the neuroglancer process. Creates the neuroglancer downsampled precomuted files
5. create_elastix.py - Creates the transformations for the section to section alignment
6. create_histogram.py - Creates a set of histograms for a particular channel
7. create_meta.py - Yanks the meta info from the CZI files and inserts it into the DB.
8. create_neuroglancer_image.py - First part of the neuroglancer process. Creates the initial chunks of the precomputed files
9. create_neuroglancer_mesh.py - Creates a mesh segmentation layer for Neuroglancer. This was used for Xiang's work.
10. create_normalized.py - Creates downsampled, 8 bit normalized images.
11. create_pointvolume.py - Creates a binary precomputer layer of annotations.
12. create_preps.py - Takes the TIF files, orders, renames and downsamples the tiffs into the correct directory with the correct names and in the correct corder. Gets the info from the DB.
13. create_shell.py - Creates a shell from the masks for Neuroglancer layer.
14. create_single_histogram.py - Creates a one off of a single histogram into a PNG file.
15. create_tifs.py - Creates the tif files from the CZI files.
16. create_update_tifs.py - Updates size info from the tifs into the DB.
17. create_web.py - creates web viewable PNG files.
