## Converting polygons to segmentation layers
1. The process is broken into two steps:
    1. The first part involves fetching the data from the database, transforming it to atlas space, and creating the Numpy arrays, and finally storing the data in the DB as pickled data. The script to perform [this step is at:](https://github.com/ActiveBrainAtlas2/preprocessing-pipeline/blob/master/src/atlas/polygon2numpy2database.py)

    1. The 2nd part of the process fetches the pickled data from the DB (the Numpy arrays) and creates the Neuroglancer segmentation layer. Each numpy array is simple a 3D mask of zeros and ones. Each different structure is then multiplied by a 'color' number taken from the database to give it a different color in Nueroglancer. Each array then is a mask filled with mostly zeros and some color number. This array is then processed with the (Seung Lab Cloudvolume software)[https://github.com/seung-lab/igneous](https://github.com/ActiveBrainAtlas2/preprocessing-pipeline/blob/master/src/atlas/database2segmentation.py)

They are both well documented so should be readable and reproducible.