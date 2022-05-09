## Converting polygons to segmentation layers
### Fetching the data
1. Data is stored in the polygon_sequences table.
1. Each row contains an x,y,z vertex and has metadata describing the data point.
1. All data is stored in micrometers.
1. Fetching the involves using the following process:

    The [PolygonSequenceController](https://github.com/ActiveBrainAtlas2/abakit/blob/dev/src/abakit/lib/Controllers/PolygonSequenceController.py) class querys the polygon sequence table by calling the `get_volume(prep_id,annotator_id,structure_id)` function.  The [PolygonSequenceController](https://github.com/ActiveBrainAtlas2/abakit/blob/dev/src/abakit/lib/Controllers/PolygonSequenceController.py) class initiates a sqalchemy session through the constructor of it's parent class [Controller](https://github.com/ActiveBrainAtlas2/abakit/blob/dev/src/abakit/lib/Controllers/Controller.py).

    The [Controller](https://github.com/ActiveBrainAtlas2/abakit/blob/dev/src/abakit/lib/Controllers/Controller.py) class contains method to start the sql session with the right credential, and the ability to add delete and insert rows as well as checking if a row exists.

    The `get_volume(prep_id,annotator_id,structure_id)` function queries the annotation sessions table to find any active session matching the prep_id,annotator_id,structure_id.  If a session is found, it queries the PolygonSequence table for the polygon points, and parses them into dictionaries.  Finally the function returns the dictionary of polygon points for a specific structure.


    1. The 2nd part of the process fetches the pickled data from the DB (the numpy arrays) and creates the Neuroglancer segmentation layer. Each numpy array is simply a 3D mask of zeros and ones. Each different structure is then multiplied by a 'color' number taken from the database to give it a different color in Nueroglancer. Each array then is a mask filled with mostly zeros and some color number. This array is then processed with the [Seung Lab Cloudvolume software](https://github.com/seung-lab/igneous). To process the numpy arrays into the segmentation layer, the following steps are taken:
        1. Fetches metadata from the DB to determine what shape the entire 3D volume will be. The width and height are taken from the width and height of the full scale images. These values are then downsampled by 32 (this is our universal downsampling factor). The numpy array would be too large with the full scale resolution. The z shape is taken from the number of sections.
        1. All structures (numpy arrays and x,y,z offsets) for that particular brain for that brain are fetched from the DB. The offsets are the distance in um taken from the top left origin of the Neuroglancer view.
        1. Each structure is then placed in the entire 3D volume we created with the width, height, section number data fetched earlier. Now we have a 3D volume with all the structures and this numpy array is then passed onto the Cloudvolume library to process into the segmentation layer.
        1. The Cloudvolume process creates the precomputed data directory which can then be placed on Birdstore and can be accessed by the web server.
        
        1. The script to perform this step is: [database2segmentation.py](https://github.com/ActiveBrainAtlas2/preprocessing-pipeline/blob/master/src/atlas/database2segmentation.py)

Both scripts are well documented and should be readable and reproducible. They can be run on either ratto, basalis, or muralis. Activate the virtualenv with: `source /usr/local/share/pipeline/bin/activate` and then run the programs with python.