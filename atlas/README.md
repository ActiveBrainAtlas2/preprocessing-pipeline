### Building an atlas aligned to a specifc brain
* An average atlas has been built from 3 foundation brains
    1. MD589
    1. MD585
    1. MD594
* This average atlas can then be superimposed on another brain but it will need alignment.
* The alignment can occur in two ways. 
    1. Via the manual alignment tool in neuroglancer.
    1. By code using a rotation/translation/scaling matrix.
* Using the matrix above requires getting the center of mass from at least
3 structures of the target brain. This example will use DK52 and these structures with centers of mass:
<pre>
# DK52 structure centers
    '12N': [46488, 18778, 242],
    '5N_L': [38990, 20019, 172],
    '5N_R': [39184, 19027, 315],
    '7N_L': [42425, 23190, 166],
    '7N_R': [42286, 22901, 291]

</pre>
* Vertices were taken from the CVAT tool and the center of mass was then calculated from them.
* Centers of mass are already made by Yuncong's code. The big difference is the centers of mass from 
the above structures were taken from an aligned and padded stack of images. In this example the images are:
65000 pixels wide and 36000 pixels in height. There are 485 sections in this stack. The centers of mass
of the Yuncong data were taken in a  virtual 3D hexahedron space with units of 10um. The actual x,y,z
coordinates of the structures above in this virtual 3D space are as follows:
<pre>
# Atlas origins
12N [141.80026858  31.12536632 -44.        ]
5N_L [ -81.96858606  -40.41990191 -166.24480242]
5N_R [-81.96858606 -40.41990191 108.24480242]
7N_L [ -18.47971976   82.01534472 -162.64548434]
7N_R [-18.47971976  82.01534472  69.64548434]

</pre>
* These coordinates refer to the very top left part of the rectangular space surrounding the individual structure.
The origin of this entire virtual space is in the center of the virtual hexahedron.
* To build the atlas, a shape that will house all the structures needs to be built. This container will then be a
scaled down version of the full resolution image stack. Building an array as the same size as the full resolution
stack is untenable as it would require about 4TB of RAM.
* New centers of mass are then calculated from the transformation matrix. These centers of mass then
need to be again transformed to get a starting and ending point of where to place the individual structure
in the holding container. These starting and ending points are calculated from the center of mass of
the actual structure and its actual dimensions.
* Basically here are the steps:
    1. An empty holding container is created which is a scaled down version of the full image stack.
    1. A rotation/scaling/translation matrix is created using the two sets of data described above.
    1. Centers of mass of all the structures in the average atlas are retrieved from Yuncong's code.
    1. Foreach structure, the original center of mass is transformed.
    1. That center of mass needs to be scaled to the appropriate size for it to fit correctly into
    the holding container.
    1. The transformed center of mass is again transformed to get the starting and ending points according
    to the structures dimensions.
    1. The structure is placed in the large holding container at the correct position
    1. The entire holding container is then converted into a format neuroglancer can display.
