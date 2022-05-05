## Converting polygons to segmentation layers
1. After the anatomist has entered the polygon data, the process is broken into two steps:
    1. The first part involves fetching the polygon data from the database, transforming it to atlas space, and creating the numpy arrays, and finally storing the data in the DB as pickled data. The module to perform [this step is named:polygon2numpy2database.py](https://github.com/ActiveBrainAtlas2/preprocessing-pipeline/blob/master/src/atlas/polygon2numpy2database.py)

**Yoav:**
* Terminology and coding standards:     
   * Lets refer to a "numpy array" as a "3D mask", it is more specific.
   * Lets refer to python files that are imported as *modules*, files that are executed from the command line as *scripts*.
   * It is preferable to wrap related functions into a class. Classes can have internal state, and that makes the code more modular.
   * Each function method and class should have a descriptive docstring.
* I am not sure if and how [polygon2numpy2database.py](https://github.com/ActiveBrainAtlas2/preprocessing-pipeline/blob/master/src/atlas/polygon2numpy2database.py) takes into account the transformation. Was this module tested?
* Is the order of operations 1: transform polygons to atlas space 2: transform polygons into 3D mask.  
  or: 1. transform polygon into 3D mask, 2: transform 3D mask into atlas space.
* What is the dtype of the 3D-mesh? should be unsigned int 8.
* What is stored in the database? a pickled 3D mask? That can be pretty large for large structures.

    2. The 2nd part of the process fetches the pickled data from the DB (a 3D mesh for each struccture) 
and creates the Neuroglancer segmentation layer. Each different structure is then multiplied by a 'color' number taken from the database to give it a different color in Nueroglancer. Each array then is a mask filled with mostly zeros and some color number.  

 This array is then processed with the [Seung Lab Cloudvolume software](https://github.com/seung-lab/igneous). To process the numpy arrays into the segmentation layer, the following steps are taken:
        1. Fetches metadata from the DB to determine what shape the entire 3D volume will be. The width and height are taken from the width and height of the full scale images. These values are then downsampled by 32 (this is our universal downsampling factor). The numpy array would be too large with the full scale resolution. The z shape is taken from the number of sections.
        1. All structures (numpy arrays and x,y,z offsets) for that particular brain for that brain are fetched from the DB. The offsets are the distance in um taken from the top left origin of the Neuroglancer view.
        1. Each structure is then placed in the entire 3D volume we created with the width, height, section number data fetched earlier. Now we have a 3D volume with all the structures and this numpy array is then passed onto the Cloudvolume library to process into the segmentation layer.
        1. The Cloudvolume process creates the precomputed data directory which can then be placed on Birdstore and can be accessed by the web server.  
        1. The script to perform this step is: [database2segmentation.py](https://github.com/ActiveBrainAtlas2/preprocessing-pipeline/blob/master/src/atlas/database2segmentation.py)
**Yoav:**  
* Can you define the interface between the code and Cloudvolume? Is it done through calls to a functions or class methods? What are the parameters? Or is CloudVolume executed as a separate unix process?

Both scripts are well documented and should be readable and reproducible. They can be run on either ratto, basalis, or muralis. Activate the virtualenv with: `source /usr/local/share/pipeline/bin/activate` and then run the programs with python.
