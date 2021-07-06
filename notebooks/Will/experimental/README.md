# This directory contains experimental code that could be a bit hard to use

`compare_rough_transformations.py` is the code I used for comparing the Affine transformation from simple itk and airlab, demons and bili's Alignment Error Visualization plot3 (coms person id 1 type 4).  

`visualize transform in neuroglancer.py` contains code to visualize the result of Affine/ demons transform in neuroglancer

`test_transform_point.ipynb` confirms that TransformPoint Does What it advertises
where T(x)=A(x−c)+t+c

`get_coms_from_pickle.py` contains utility functions to load coms from a pickle save and apply the correct transformations