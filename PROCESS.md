## Table of contents for the pipeline process
1. [Active Brain Atlas home page](https://github.com/ActiveBrainAtlas2)
1. [Installing the pipeline software](SETUP.md)
1. [A description of the pipeline process with detailed instructions](PROCESS.md)
1. [HOWTO run the entire pipeline process with step by step instructions](RUNNING.md)
1. [The entire MySQL database schema for the pipeline and the Django portal](schema.sql)
1. [Software design and organization](Design.md)

## Overview of the pipeline utility process
The pipeline process will take scanned images that are digitized into CZI files
and make them available in Neuroglancer. The process involves the following steps:

#### Extracting scan images from the CZI files and storing in various formats for visualization and computation purposes
1. The user enters the initial information into the database. The entire process depends on this initial step and will not
proceed without this information. Throughout the process, the database is checked
for variables so it is vital for the correct information to be placed in these tables:
    1. [animal](https://activebrainatlas.ucsd.edu/activebrainatlas/admin/brain/slideczitotif/)
    1. [scan_run](https://activebrainatlas.ucsd.edu/activebrainatlas/admin/brain/scanrun/)
    1. [histology](https://activebrainatlas.ucsd.edu/activebrainatlas/admin/brain/histology/)

1. CZI files are placed on a network file system (NFS) which is named birdstore and is 
mounted at /net/birdstore on our 3 workstations:
    1. ratto
    1. basalis
    1. muralis
1. The location of the CZI files is: */net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DKXX/czi*
1. CZI files are large compressed files containing around 20 images and a large amount of metadata that describes
the scanner and the scanned images. The images and metadata contained in each CZI file are extracted with a set of 
tools that are available on each workstation. This bioformat software is also available for download at: 
https://www.openmicroscopy.org/bio-formats/downloads/  
1. The metadata is extracted from the CZI file using the command line tool: */usr/local/share/bftools/showinf*
1. The TIF images are extracted with this tool: */usr/local/share/bftools/bfconvert*
1. The bioformat tools use Java so this must also be installed on the workstation.
1. The extracted tiff files are them stored in */net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DKXX/tif*
1. The *showinf* tool takes the metadata and stores it into the following tables in the database:
    1. [slide](https://activebrainatlas.ucsd.edu/activebrainatlas/admin/brain/slide/) 
    1. [slide_czi_to_tif](https://activebrainatlas.ucsd.edu/activebrainatlas/admin/brain/slideczitotif/)
    1. [scan_run](https://activebrainatlas.ucsd.edu/activebrainatlas/admin/brain/scanrun/)
#### Manual Quality control of sections that allows the replacing of bad sections with neighboring section.
1. Once the TIF files are placed in the tif directory, the user can perform quality control on the 
[slides](https://activebrainatlas.ucsd.edu/activebrainatlas/admin/brain/slide/) in the
database. There are around 150 slides per mouse with each slide usually containing 4 scenes(pictures).
During QA on the slides and scenes, the user will replace bad scenes with adjacent good scenes. 
Entire slides can also be removed by marking the slide appropriately in the portal.
Once QA is finished, the user will continue with the pipeline process.
1. The user then creates the sections and web images. The correct order of slides/scenes is fetched
from the database and the files are copied to:
    1. */net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DKXX/preps/CHX/full*
    1. */net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DKXX/preps/CHX/thumbnail*
1. We then normalize the TIF images intensities to a visiable range and store them 
in */net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DKXX/preps/CHX/normalized*
#### Automatic Creation and manual editing of masks around sections to exclude debres around the tissue.
1. Masks are then created from the thumbnail images and are placed in:
*/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DKXX/preps/masks/thumbnail_colored/*
1. The masks are created with Pytorch and torchvision and the process is very similar to:
https://pytorch.org/tutorials/intermediate/torchvision_tutorial.html
1. The users can then add to the mask with a *white* paintbrush or remove mask sections with a *black* paintbrush.
1. When the user is done, the pipeline is run again and the edited masks are extracted.
1. masks in  
*/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DKXX/preps/masks/thumbnail_masked/* 
are then used to create clean images in 
*/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DKXX/preps/CHX/thumbnail_cleaned/*
#### Aligning the section images within the brain
1. The cleaned images are then aligned to each other using *Elastix* which is built into the SimpleITK library.
Each image is aligned to the image before it in section order. This data is stored in the elastix_transformation table
in the database. For each image, the rotation, xshift, and yshift data is stored. This is then used
in the alignment process to create a stack of section to section aligned images. These images are then stored in:
*/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DKXX/preps/CHX/thumbnail_aligned/*
#### Create files for viewing the 3D image in Neuroglancer.
1. The aligned images are now ready to be processed into Neuroglancer's default image type: 
[precomputed](https://github.com/google/neuroglancer/tree/master/src/neuroglancer/datasource/precomputed)
1. There are two steps to creating the precomputed format:
    1. Create the intial chunk size of (64,64,1). Neuroglancer serves data from the webserver in chunks. The initial chunk
    only has a z length of 1. This is necessary for the initial creation. 
    However, this chunk size results in too many files and needs to be *transfered* by the next step in the process which creates
    a better chunk size and results in they *pyramid* scheme that is best for viewing in a web browser. This
    data is stored in */net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DKXX/neuroglancer_data/CX_rechunkme*
    1. The 2nd phase in the precomputed creates a set of optimum chunks from the  directory created in the previous
    step and places the new pyramid files in 
    */net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DKXX/neuroglancer_data/CX*
    This data is now ready to be served by the Apache web server.
1. All data in */net/birdstore/Active_Atlas_Data/data_root/pipeline_data/* is available to Neuroglancer. When
the user opens up Neuroglancer and enters a URL path in the precomputed field, the URL will actually be
pointing to the data on birdstore. For example, typing this URL in Neuroglancer: 
https://activebrainatlas.ucsd.edu/data/DK39/neuroglancer_data/C1 will be pointing to
*/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK39/neuroglancer_data/C1 on birdstore. 

