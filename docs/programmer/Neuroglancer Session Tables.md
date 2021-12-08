I am proposing the creation of four tables that will replace the current way of storing the json neuroglancer sessons in the database:

###Table1 Neuroglancer Layers
id                  int             primary key
session_name        string          name of the session
layer_name          string          name of the layer
layer_type          string          'image','segmentation' or 'Annotation'
post_fixing_json    json            all the flexible json fields

###Table2 Image Layers
id                  int             primary key
source              string          address where the public layer is hosted
(optional)
lab                 string          laboratory hosting the data

###Table3 Segmentation Layers
id                  int             primary key
source              string          address where the public layer is hosted
(optional)
lab                 string          laboratory hosting the data

###Table4 Annotation Layers
id                  int             primary key
x                   int             x coordinate
y                   int             y coordinate
z                   int             z coordinate
