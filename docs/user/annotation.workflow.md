## This is the flow of how annotation layers are added to the database
### New set of annotations
1. The user opens up an annotation layer in Neuroglancer and adds data. 
When the user hits 'Save', the program will enter all data under that layer,
convert it to micrometers and insert into the database table: layer_data.
The only exception is if the user does not change the layer name from the default:
'annotation'. If the user wants the data saved, the user `must` change the name
from 'annotation' to something more meaningful.
### Existing annotations
1. When the user hits the 'Save' button again in the same Neuroglancer view,
the program will:
    1. Take the existing annotation data in that layer and mark it as
inactive.
    1. Mark each row with the current timestamp
    1. Mark each row with the person doing the updating 
    1. Insert all data and mark it with the current timestamp and the person
    who entered the data. 
    1. This will occur for all layers.
1. For the large annotation layer like 'DK39 premotor' where there are 2,200
annotations, this will take a few seconds to save. Take note, for this instance,
whenever the user hits 'Save', there will be an additional 2,200 inactive DK39 premotor
annotations. This is not a problem as the database can easily handle millions
of rows, but the user needs to be aware of this fact when searching.
1. All annotation data that is marked as inactive, gets marked with the current
update time and by the user that updated the data.

