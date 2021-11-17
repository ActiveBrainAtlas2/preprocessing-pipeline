import pandas as pd
import numpy as np
from get_new_manual import ManualVSAffineAtlasCOM

def get_offset_table_from_two_com_sets(com1,com2):
    '''

    :param com1: a dictionary of COMs of atlas
    :param com2: a dictionary of COMs of beth
    :return:
    '''
    offset_table = pd.DataFrame()
    column_types = ['dx','dy','dz']
    for stack in com2.keys():
        for landmark in com2[stack].keys():
            dx, dy ,dz = np.array(com1[stack][landmark]) - np.array(com2[stack][landmark])
            # highscore = landmark in list(df_highscore[df_highscore['Mouse ID']==stack]['Structure'])
            for data_type in column_types:
                data = {}
                data['landmark'] = landmark
                data['structure'] = landmark+':'+data_type
                data['value'] = eval(data_type)
                data['direction'] = data_type
                data['brain'] = stack
                # data['HighScore'] = highscore
                offset_table = offset_table.append(data, ignore_index=True)
    return offset_table

def create_error_table(tables):
    '''

    :param tables: a pandas table created by get_offset_table_from_two_com_sets
    :return:
    '''
    collection = pd.DataFrame()
    for structure in sorted(set(tables['landmark'])):
        data = {}
        data['Structure'] = structure
        # data['Number of low confidence'] = format(10-len(df_highscore[df_highscore['Structure']==structure]), 'd')
        table = tables[(tables['landmark']==structure) ]
        for data_type in ['dx','dy','dz']:
            values = np.array(table[table['structure']==structure+':'+data_type]['value'])
            data['Mean of errors: '+data_type] = format(values.mean(),'.2f')
            data['Std of errors: '+data_type] = format(values.std(),'.2f')
            # data['Size of structure: '+data_type] = format(extent[structure+':'+data_type],'.2f')
            data[data_type+': fraction of errors <50'] = '{:.1%}'.format(sum(abs(values)<50)/len(values))
            data[data_type+': fraction of errors [50,100]'] = '{:.1%}'.format(sum((abs(values)<=100) & (abs(values)>=50))/len(values))
            data[data_type+': fraction of errors >100'] = '{:.1%}'.format(sum(abs(values)>100)/len(values))
        collection = collection.append(data,ignore_index=True)[data.keys()]
    return collection

ana = ManualVSAffineAtlasCOM()
ana.load_data()
ana.load_detected_com()
a1 = ana.aligned_atlas_coms
a2 = ana.new_coms
a2 = ana.all_coms
a1['DK63'] = {}
a2['DK63'] = {}
offset = get_offset_table_from_two_com_sets(a1,a2)
error = create_error_table(offset)
inreg = list(ana.detected['DK39'].keys())
[print(sti) for sti in error.Structure ]
error_inreg = error[[sti in inreg for sti in error.Structure ]]
error_not_inreg = error[[sti not in inreg for sti in error.Structure ]]
error = pd.concat([error_inreg,error_not_inreg])
error.to_csv('~/Desktop/Aligned_vs_all_manual_kuis_method.csv')
print('done')