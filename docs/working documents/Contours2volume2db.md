### Process to turn contours to volumes and store them in the database.

1. Fetching the polygon data from the database:

    The [PolygonSequenceController](https://github.com/ActiveBrainAtlas2/abakit/blob/dev/src/abakit/lib/Controllers/PolygonSequenceController.py) class querys the polygon sequence table by calling the `get_volume(prep_id,annotator_id,structure_id)` function.  The [PolygonSequenceController](https://github.com/ActiveBrainAtlas2/abakit/blob/dev/src/abakit/lib/Controllers/PolygonSequenceController.py) class initiates a sqalchemy session through the constructor of it's parent class [Controller](https://github.com/ActiveBrainAtlas2/abakit/blob/dev/src/abakit/lib/Controllers/Controller.py).

    The [Controller](https://github.com/ActiveBrainAtlas2/abakit/blob/dev/src/abakit/lib/Controllers/Controller.py) class contains method to start the sql session with the right credential, and the ability to add delete and insert rows as well as checking if a row exists.

    The `get_volume(prep_id,annotator_id,structure_id)` function queries the annotation sessions table to find any active session matching the prep_id,annotator_id,structure_id.  If a session is found, it queries the PolygonSequence table for the polygon points, and parses them into dictionaries.  Finally the function returns the dictionary of polygon points for a specific structure.

2. Transforming polygon data to atlas space
   
    The [TransformationController](https://github.com/ActiveBrainAtlas2/abakit/blob/master/src/abakit/lib/Controllers/TransformationController.py) class then pulls the transformation stored in the transforamtion table using the `get_transformation` function.  The TransformationController class inherit from the same parent class Controller.
    
     then we transforms the points from the stack space to the atlas space using the `forward_transform_points` function. `forward_transform_points` takes a list of point coordinate,and output the result of the points after the transformation.  The function will be run on all of the points in polygons and apply the affine or rigid transformation calculated from the structure coms to the atlas coms.

3. Creating the 3D mask and origins from polygon data
 
     The [VolumeMaker](https://github.com/ActiveBrainAtlas2/abakit/blob/master/src/abakit/atlas/VolumeMaker.py) class is then used to create a 3d mask from the 2d contours.  The aligned contours are given to the class by the function `set_aligned_contours`.  and the volume is calculated by running the function `compute_COMs_origins_and_volumes`.  After the calculation, the volume can be found in the `self.volumes` attribute.

     The [VolumeMaker](https://github.com/ActiveBrainAtlas2/abakit/blob/master/src/abakit/atlas/VolumeMaker.py) class has the parent class [BrainStructureManager](https://github.com/ActiveBrainAtlas2/abakit/blob/master/src/abakit/atlas/BrainStructureManager.py) which inherits from the [Brain](https://github.com/ActiveBrainAtlas2/abakit/blob/master/src/abakit/lib/Brain.py) class and [VolumeUtilities](https://github.com/ActiveBrainAtlas2/abakit/blob/master/src/abakit/atlas/VolumeUtilities.py) class.  The Brain class has a bunch of functions that handles the file path and database access and VolumeUtilities has functions to threshold volumes and smoothing the 3d mask with a gaussian filter.  Most of the function of the Brain class is not that useful to the VolumeMaker in this context.  We should add the ability to toggle these part of the functions so that a connection to the database would not be required to run this step.

4. Compressing the 3D mask with encoding methods
 - code: pending, testing: pending

5. Storing the 3D mask and origins in the DB as pickled data. 
 - code: currently exist in scripts and will be organized, testing: pending