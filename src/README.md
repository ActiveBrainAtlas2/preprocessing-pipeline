### Raw images processing
The raw images that come of the scanning microscope are in a proprietary format called CZI.
the script `create_tifs.py` transforms them to the standard format tiff for further processing.

The next step is to align the sections to each other. This is done in two steps, first `create_elastix.py` generates the transformations that bring the sections into alignment. Second, `create_alignment` uses these transformations to bring the tiff images into alignment.

The last step is to update the database with the meta information on the images. This is done by the scripts `create_meta` ...
that inserts information in the tables ...,...,...

1. create_alignment.py - Performs section to sectio alignment
5. create_elastix.py - Creates the transformations for the section to section alignment. Uses the elastix software package.
6. create_tifs.py - Creates the tif files from the CZI files. Uses the XXXX software package.
18. create_update_tifs.py - Updates size info from the tifs into the DB.
19. create_meta.py - Yanks the meta info from the CZI files and inserts it into the DB.
20. create_web.py - creates web viewable PNG files.

### Masking
Masking is used to remove the shmuts that is in the clear areas outside the sections.   

1. create_masks.py - Creates the masks which are used to clean the images.
4. create_clean.py - Takes the masks and performs pixel-wise and to clean image.

### Neuroglancer 
1. create_different_mesh.py - Creates a mesh segmentation layer for neuroglancer
7. create_downsampling.py - 2nd phase in the neuroglancer process. Creates the neuroglancer downsampled precomuted files
8. create_histogram.py - Creates a set of histograms for a particular channel
10. create_neuroglancer_image.py - First part of the neuroglancer process. Creates the initial chunks of the precomputed files
11. create_neuroglancer_mesh.py - Creates a mesh segmentation layer for Neuroglancer. This was used for Xiang's work.
12. create_normalized.py - Creates downsampled, 8 bit normalized images.
13. create_pointvolume.py - Creates a binary precomputer layer of annotations.
14. create_preps.py - Takes the TIF files, orders, renames and downsamples the tiffs into the correct directory with the correct names and in the correct corder. Gets the info from the DB.
15. create_shell.py - Creates a shell from the masks for Neuroglancer layer.
16. create_single_histogram.py - Creates a one off of a single histogram into a PNG file.

### To be added

#### Cell Extraction
#### Diffusion Map
#### Training Detectors
#### Brain to atlas alignment
##### Rough Alignment
##### Structure detection
##### fine alignment.
