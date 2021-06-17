from notebooks.Will.toolbox.IOs.get_center_of_mass import get_atlas_centers_in_physical_coord
from notebooks.Will.toolbox.IOs.get_calculated_transforms import get_demons_transform
from notebooks.Will.toolbox.IOs.get_specimen_lists import get_list_of_brains_to_align
brains_to_align = get_list_of_brains_to_align()
atlas_coord_phys = get_atlas_centers_in_physical_coord()
for braini in brains_to_align:
    demons_transform = get_demons_transform(braini)
