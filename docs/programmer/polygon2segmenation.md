## Converting polygons to segmentation layers
### Fetching the data
1. Data is stored in the polygon_sequences table.
1. Each row contains an x,y,z vertex and has metadata describing the data point.
1. All data is stored in micrometers.
1. Fetching the data involves importing the abakit module. This module uses the process described below:

    The [PolygonSequenceController](https://github.com/ActiveBrainAtlas2/abakit/blob/dev/src/abakit/lib/Controllers/PolygonSequenceController.py) class querys the polygon sequence table by calling the `get_volume(prep_id,annotator_id,structure_id)` function.  The [PolygonSequenceController](https://github.com/ActiveBrainAtlas2/abakit/blob/dev/src/abakit/lib/Controllers/PolygonSequenceController.py) class initiates a sqalchemy session through the constructor of it's parent class [Controller](https://github.com/ActiveBrainAtlas2/abakit/blob/dev/src/abakit/lib/Controllers/Controller.py).

    The [Controller](https://github.com/ActiveBrainAtlas2/abakit/blob/dev/src/abakit/lib/Controllers/Controller.py) class contains method to start the sql session with the right credentials, and the ability to add delete and insert rows as well as checking if a row exists.

    The `get_volume(prep_id,annotator_id,structure_id)` function queries the annotation sessions table to find any active session matching the prep_id,annotator_id,structure_id.  If a session is found, it queries the PolygonSequence table for the polygon points, and parses them into dictionaries.  Finally the function returns the dictionary of polygon points for a specific structure.

1. Ater the data has been fetched, we can transform the polygon data to atlas space with the following process:
   
    The [TransformationController](https://github.com/ActiveBrainAtlas2/abakit/blob/master/src/abakit/lib/Controllers/TransformationController.py) class pulls the transformation stored in the transforamtion table using the `get_transformation` function.  The TransformationController class inherits from the same parent class Controller.
    
    We transform the points from the stack space to the atlas space using the `forward_transform_points` function. `forward_transform_points` takes a list of point coordinates and outputs the result of the points after the transformation. The function will be run on all of the points in all the polygons and apply the affine or rigid transformation calculated from the structure coms to the atlas coms.

1. Creating the 3D masks from polygon data
 
     The [VolumeMaker](https://github.com/ActiveBrainAtlas2/abakit/blob/master/src/abakit/atlas/VolumeMaker.py) class is then used to create a 3D mask from the 2D contours.  The aligned contours are given to the class by the function `set_aligned_contours`.  The volume is calculated by running the function `compute_COMs_origins_and_volumes`.  After the calculation, the volume can be found in the `self.volumes` attribute.

     The [VolumeMaker](https://github.com/ActiveBrainAtlas2/abakit/blob/master/src/abakit/atlas/VolumeMaker.py) class has the parent class [BrainStructureManager](https://github.com/ActiveBrainAtlas2/abakit/blob/master/src/abakit/atlas/BrainStructureManager.py) which inherits from the [Brain](https://github.com/ActiveBrainAtlas2/abakit/blob/master/src/abakit/lib/Brain.py) class and [VolumeUtilities](https://github.com/ActiveBrainAtlas2/abakit/blob/master/src/abakit/atlas/VolumeUtilities.py) class.  The Brain class has a multitude of functions that handle the file path and database access. VolumeUtilities has functions to threshold volumes and for smoothing the 3D mask with a gaussian filter.  Most of the function of the Brain class is not that useful to the VolumeMaker in this context.  We should add the ability to toggle these part of the functions so that a connection to the database would not be required to run this step.


    1. The 2nd part of the process fetches the pickled data from the DB (the numpy arrays) and creates the Neuroglancer segmentation layer. Each numpy array is simply a 3D mask of zeros and ones. Each different structure is then multiplied by a 'color' number taken from the database to give it a different color in Nueroglancer. Each array then is a mask filled with mostly zeros and some color number. This array is then processed with the [Seung Lab Cloudvolume software](https://github.com/seung-lab/igneous). To process the numpy arrays into the segmentation layer, the following steps are taken:
        1. Fetches metadata from the DB to determine what shape the entire 3D volume will be. The width and height are taken from the width and height of the full scale images. These values are then downsampled by 32 (this is our universal downsampling factor). The numpy array would be too large with the full scale resolution. The z shape is taken from the number of sections.
        1. All structures (numpy arrays and x,y,z offsets) for that particular brain for that brain are fetched from the DB. The offsets are the distance in um taken from the top left origin of the Neuroglancer view.
        1. Each structure is then placed in the entire 3D volume we created with the width, height, section number data fetched earlier. Now we have a 3D volume with all the structures and this numpy array is then passed onto the Cloudvolume library to process into the segmentation layer.
        1. The Cloudvolume process creates the precomputed data directory which can then be placed on Birdstore and can be accessed by the web server.
        
        1. The script to perform this step is: [database2segmentation.py](https://github.com/ActiveBrainAtlas2/preprocessing-pipeline/blob/master/src/atlas/database2segmentation.py)

Both scripts are well documented and should be readable and reproducible. They can be run on either ratto, basalis, or muralis. Activate the virtualenv with: `source /usr/local/share/pipeline/bin/activate` and then run the programs with python.