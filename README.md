### Table of contents for the pipeline process
1. [Active Brain Atlas home page](https://github.com/ActiveBrainAtlas2)
1. [Installing the pipeline software](docs/SETUP.md)
1. [A description of the pipeline process with detailed instructions](docs/PROCESS.md)
1. [HOWTO run the entire pipeline process with step by step instructions](docs/RUNNING.md)
1. [The entire MySQL database schema for the pipeline and the Django portal](schema.sql)
1. [Software design and organization](docs/Design.md)

## A high level description of the Active Brain Atlas pipeline process

The ability to view and share high resolution microsopy data among different laboratories across the continents 
is an impending challenge of today's neuroscience research.  Our recent capacity to measure and store data on a 
large scale has given rise to the need for a set of tools that enables seemless sharing of large data sets. 
Going from biological samples to data that can be viewed, edited and shared is a nontrivial task. The challenges 
presented by handling big data is clear as a set of complete section images with resonable resoltion could take
around 5TB per mouse. On top of that, many copies of the data need to be created in order to visualize the image set
at variable resolution through the internet. The processed data set also needs to be stored in an efficient and secure format 
that is accessible by web servers. 

The image data is stored on our filesystem and served by a web server while the image metadata is stored 
in a database. A human user can then access information in the database and monitor each step of the 
processing pipeline via a grapical interface. Throughout the pipeline, data is inserted, updated and retrieved to 
and from the database to report the status of the processing steps. The database provides a convenient and 
efficent way for multiple users to create, retrieve, update, and manage the shared data sets anywhere in the world.  

The goal of this project is to allow labs to run this process on a cloud based or
in house server setup with low human intervention. Users will be able to start, monitor 
and log systems progress entirely through a web page.

The following steps describes the pipeline process, from slide scanning all the 
way to the web accessible data.

### Raw data processing

Each mouse brain has around 130-160 slides with 4 tissue samples on each slide.
The slides are scanned and digitized into files that contain both the images and the
metadata. The images are extracted onto the filesystem and the metadata
inserted into the relational database. The user(s) then use the web portal to perform 
quality control on the data to make sure the sections are in the correct order and 
to replace any bad sections if necessary. Once the quality control is finished,
the pipeline continues to create the quality controlled images in full resolution. 
Downsampled versions of the image are also created to make preliminary image manipulations
easier and quicker to perform.


### Masking and cleaning
After creating the quality controlled images, we then create masks that covers the 
important biological tissue to remove signals from background and debres from the full resolution
and downsampled images. This process remove excess glue, dirt, hairs and other unwanted signals.
Cleaned images not only create better visualization, but also improves the accuracy of the subsequent
section to section alignment.  Masks are created on downsamples images, quality controlled through a 
manual step and scaled for the full resolution image.

### Section to section alignment
Brain tissue on the image have different rotations, horizontal and vertical shifts from section to section. 
Therefore the sections must be aligned with each other for proper viewing in Neuroglancer. In the case 
where a brain is sectioned sagittally, neuroglancer creates virutal images in the coronal and horizontal 
view.  If the images are not aligned correctly, these virtual images will not be accurate. The section to 
section alignment is created on the downsample files using Elastix: an opensource program that is integrated
into the pipeline process. Performing the alignment process on the full resolution 
images is untenable for the sheer size of these images. Elastix performs a correlation between the greyscale values
of the adjoining images to assess alignment result. It then stores the rotation, x-shift, and y-shift
in the database. Elastix then uses rigid transformation to align adjoining images through the entire image stack. 
The transformations are calculated from downsampled images and then used to align the full resolution images 
with the the appropriate scaling.


### Preparation of aligned data for use in Neuroglancer
The aligned images are now ready to be processed into the [precomputed]
(https://github.com/google/neuroglancer/tree/master/src/neuroglancer/datasource/precomputed) 
format of neuroglancer.  To make the data available to a web browser over the internet, the data must
be broken up into 'chunks'. These chunks are created from the aligned images,
then compressed and placed in a directory that is accessible by the web
server. This data provides the different resolutions (pyramids) that allow
the user to zoom in and out. Once the data is viewable in a web browser,
more metadata and annotations can be created by users and stored in the database. 
The images and the corresponding annotaions are then available to any personnel with the appropriate access.
