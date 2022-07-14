# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
import sys
sys.path.append('/home/zhw272/programming/pipeline_utility')
sys.path.append('/home/zhw272/programming/pipeline_utility/src')
from pipeline.lib.sql_setup import session
from model.center_of_mass import CenterOfMass
from toolbox.IOs.LoadComPickle import LoadComPickle
from toolbox.IOs.LoadComDatabase import LoadComDatabase
from toolbox.IOs.TransformCom import TransformCom
from toolbox.plotting import com_scatter_plot
import numpy as np
from pipeline.lib.comparison_tools import compare_lists
getcomp = LoadComPickle()
gettc = TransformCom(getcomp)
getcomd = LoadComDatabase()


# %%
import notebooks.Will.experimental.old.get_coms_from_pickle as getcomp
import notebooks.Will.experimental.old.get_transformed_coms as gettc


# %%
def query_brain_coms(brain, person_id=28, input_type_id=4,factor = np.array([0.325,0.325,20])):
    # default: person is bili, input_type is aligned
    rows = session.query(CenterOfMass)        .filter(CenterOfMass.active.is_(True))        .filter(CenterOfMass.prep_id == brain)        .filter(CenterOfMass.person_id == person_id)        .filter(CenterOfMass.input_type_id == input_type_id)        .all()
    row_dict = {}
    for row in rows:
        structure = row.structure.abbreviation
        row_dict[structure] = np.array([row.x, row.y, row.section])*factor
    return row_dict


# %%

def check_dict(d1:dict,d2:dict,verbose = True):
    if (d1.keys()==d2.keys()):
        bools = []
        for keyi in d1.keys():
            equal = np.all(np.isclose(d1[keyi],d2[keyi],atol = 1))
            if not equal and verbose:
                # print('nonequal entry:')
                print(keyi,d1[keyi],d2[keyi])
            bools.append(equal)
            
    else:
        print('unequal keys')
        compare_lists(list(d1.keys()),list(d2.keys()))
        bools = None
    return np.all(bools)


# %%
#compare atlas
a1 = getcomp.get_atlas_com()
a2 = getcomd.get_atlas_com()
check_dict(a1,a2) 


# %%
#compare com save vs database corrected beth
prep_list = getcomp.get_prep_list()
for prepi in prep_list:
    d1 = getcomp.get_corrected_prepi_com(prepi)
    d2 = getcomd.get_corrected_prepi_com(prepi)
    print(prepi,check_dict(d1,d2) )


# %%
#compare com save vs database beth
prep_list = getcomp.get_prep_list()
for prepi in prep_list:
    d1 = getcomp.get_prepi_com(prepi)
    d2 = getcomd.get_prepi_com(prepi)
    print(prepi,check_dict(d1,d2) )


# %%
#compare com Com table(old) vs save beth
prep_list = getcomp.get_prep_list()
for prepi in prep_list:
    d1 = getcomp.get_prepi_com(prepi)
    d2 = query_brain_coms(prepi, person_id=2, input_type_id=1)
    print(prepi,check_dict(d1,d2) )


# %%
#compare com Com table(old) vs save corrected beth
prep_list = getcomp.get_prep_list()
prep_list.remove('DK55')
for prepi in prep_list:
    d1 = getcomp.get_corrected_prepi_com(prepi)
    d2 = query_brain_coms(prepi, person_id=2, input_type_id=2)
    print(prepi,check_dict(d1,d2) )


# %%
beth_aligned = gettc.get_beth_coms_aligned_to_atlas()
#%%
com_scatter_plot.compare_two_com_dict(beth_aligned[0],query_brain_coms('DK39', person_id=28, input_type_id=2,factor = np.array([10,10,20])),names = ['will','bili'])

# %%
#compare com Com table(old) vs save corrected beth
prep_list = getcomp.get_prep_list()
prep_list.remove('DK52')
id = 0
for prepi in prep_list:
    d1 = beth_aligned[id]
    d2 = query_brain_coms(prepi, person_id=28, input_type_id=2,factor = np.array([10,10,20]))
    print(prepi,check_dict(d1,d2,verbose = True) )
    id+=1


# %%



