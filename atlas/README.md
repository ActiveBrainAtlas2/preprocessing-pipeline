## Building all the foundation structures

There are two methods for building a precomputed volume of all the structures of a foundation brain. 
One is to use CVAT and export the data and the other involves reading the 
pandas dataframe and creating a numpy array from the hand annotations. This is useful
for the data that has already been done by the anatomists. This data is
then used with cloud-volume to create the precomputed volume which can be
used by Neuroglancer. To view instructions for exporting structures from [CVAT to Neuroglancer, look here.](CVAT.md)
This page will deal with the second method, using a script.
Instructions are listed below:

### Prerequisites
1. Access to birdstore. Specifically these directories.
    * /net/birdstore/Active_Atlas_Data/data_root/pipeline_data/MDXXX/preps/CH1/thumbnail
    * /net/birdstore/Active_Atlas_Data/data_root/atlas_data/foundation_brain_annotations
    * /net/birdstore/Active_Atlas_Data/data_root/pipeline_data/MDXXX/preps/CH1/thumbnail_cleaned
    * /net/birdstore/Active_Atlas_Data/data_root/atlas_data/foundation_brain_annotations/MDXXX
1. python 3 with the necessary libraries. Check the requirements.txt in the root folder of this repository
for the list of libraries used.
1. The brain must already be aligned and the data available in the elastix directory:
/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/MDXXX/preps/elastix
### Process
1. Activate your virtualenv and run: `python build_structures_from_annotations.py --animal MDXXXX`
1. This will run the script. It takes only a minute or two to run. The result will be in:
/net/birdstore/Active_Atlas_Data/data_root/atlas_data/foundation_brain_annotations/MDXXX
1. Copy that directory to a location that is accessible by your web server. For instance, you could
copy it to /net/birdstore/Active_Atlas_Data/data_root/pipeline_data/structures/MDXXX
1. In Neuroglancer, you can create a new layer with the precomputed source for this example at:
https://activebrainatlas.ucsd.edu/data/structures/MDXXX
1. You can also type that url into a web browser to test if it is available.
1. Repeat this process for any other foundation brain.




