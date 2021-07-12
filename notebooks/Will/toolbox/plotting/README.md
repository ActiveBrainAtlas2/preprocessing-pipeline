# this directory contains plotting libraires to compare coms
## These plotting functions are of two kinds:
1. `ComBoxPlot.py` Contains class for generating boxplots showing the difference between coms in the x, y, z direction and overall distance using matplotlib.
2. `plot_coms.py` Contains libraires for generating interactive scatter plots that plots two sets of coms together in 3D space using plotly.

All of these functions take com dictionaries or list of coms as input.

Com dictionaries should have landmark abbreviation or name as keys and com coordiates as values.  The values for the com coordiates should be the same for all dictionary entries and across dictionaries.


## Com box plots:
the main functionalities are documented in the main directory.  I will provide some implementation detials for `plot_com_offset_.py` below:

`get_fig_offset_box(offsets_table, title = '')` is the main plotting function in Bili's notebooks.  The functionality for zooming in was removed at one point but can be quickly added in.

`offsets_table` is a pandas table with columns: 
* 'structure' containing the landmark abbreviation
* 'value' contains the difference between the coms for that structure
* 'type' contains string indicating whether the difference is in the x,y,z direction or overall distains 
* 'brain' contains information of the specimens being compared.
`title` is the title of the plot.

`get_offset_table` prepares the offset table depending whether to compare pairwise elements of two list of com dictionaries, compare a list of com dictionaries to one set of reference coms or to prepare the table from precalculated differences between coms.  The different procedures are handled by  `offset_function` which creates data for the rows of the offset_table.  `get_offset_table` then put those values into rows in the pandas table.

## Com scatter plots:
To generate 3d scatter plots to compare two set of coms use the function below from `plot_coms.py`:
* To compare two com dictionaries
```python
compare_two_com_dict(com_dict1,com_dict2,names)
```
names is a list contain name of first and second specimen used for figure legends

* To do pairwise comparison for two list of com dictionaries
```python
compare_corresponding_coms_in_two_dicts(com_dict_list1,com_dict_list2,name_list1,name_list2)
```
`name_list1` and `name_list2` contains name of specimens for the dictionaries in `com_dict_list1` and `com_dict_list1`

* To compare a list of com dictionaries to one reference com dictionary:
```python
compare_corresponding_coms_in_dict_to_reference(com_dict_list1,reference,name_list1,name_list2)
```
In this case `name_list2` contain a list of repeating string of the name of the reference brain with the same number of elements as `name_list1` and `com_dict_list1`
