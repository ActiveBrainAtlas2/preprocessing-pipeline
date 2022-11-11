#%%
import sys
sys.path.append('/home/zhw272/programming/pipeline_utility')
from toolbox.IOs.get_specimen_lists import get_list_of_all_dk_brains
from utilities.brain_specimens.get_com import *
from toolbox.IOs.pickle_io import *
from utilities.model.center_of_mass import CenterOfMass
#%%
atlas_com = get_atlas_com_dict()

prep_list = get_list_of_all_dk_brains()
beth_coms = {}
for prepi in prep_list:
    comi = get_com_dict(prepi,person_id=2,input_type_id=1)
    beth_coms[prepi] = comi

beth_corrected_coms = {}
for prepi in prep_list:
    comi = get_com_dict(prepi,person_id=2,input_type_id=2)
    beth_corrected_coms[prepi] = comi

bili_aligned_coms = {}
for prepi in prep_list:
    comi = get_com_dict(prepi,person_id=28,input_type_id=4)
    bili_aligned_coms[prepi] = comi

bili_aligned_corrected_coms = {}
for prepi in prep_list:
    comi = get_com_dict(prepi,person_id=28,input_type_id=2)
    bili_aligned_corrected_coms[prepi] = comi

def get_com_dict_from_center_of_mass(prep_id,person_id,input_type_id):
    query_results = session.query(CenterOfMass)\
        .filter(CenterOfMass.active.is_(True))\
        .filter(CenterOfMass.prep_id == prep_id)\
        .filter(CenterOfMass.person_id == person_id)\
        .filter(CenterOfMass.input_type_id == input_type_id)\
        .all()
    center_of_mass = {}
    for row in query_results:
        structure = row.structure.abbreviation
        com = np.array([row.x, row.y, row.section])
        center_of_mass[structure] = com
    return center_of_mass

kui_airlab_coms = {}
for prepi in prep_list:
    comi = get_com_dict_from_center_of_mass(prepi,person_id=1,input_type_id=4)
    kui_airlab_coms[prepi] = comi

save_dict = {}
data = [atlas_com,beth_coms,beth_corrected_coms,bili_aligned_coms,bili_aligned_corrected_coms,kui_airlab_coms]
names = ['atlas_com','beth_coms','beth_corrected_coms','bili_aligned_coms','bili_aligned_corrected_coms','kui_airlab_coms']
for i in range(len(data)):
    save_dict[names[i]] = data[i]

save_pickle(save_dict,file_name='com_save_7-1-2021',folder='com_saves')
# %%
