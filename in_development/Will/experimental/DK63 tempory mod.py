import sys
sys.path.append('/home/zhw272/programming/pipeline_utility')
sys.path.append('/home/zhw272/programming/pipeline_utility/src')
from utilities.alignment.align_point_sets import get_rigid_transformation_from_dicts
from toolbox.IOs.LoadComDatabase import LoadComDatabase
if __name__ == '__main__':
    prepi = 'DK63'
    get_com = LoadComDatabase()
    coms = get_com.get_corrected_prepi_com(prepi)
    atlas_com = get_com.get_atlas_com()
    deletion_list = ['7N_L','7N_R','6N_R']
    for item in deletion_list:
        coms.pop(item)
    a,t = get_rigid_transformation_from_dicts(coms,atlas_com)
    print(a)
    print(t)
    print('')
 