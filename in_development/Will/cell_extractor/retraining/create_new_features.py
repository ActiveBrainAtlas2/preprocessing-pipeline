from glob import glob
import pandas as pd
import pickle as pk
import numpy as np
import os

def create_combined_features():
    dir = '/net/birdstore/Active_Atlas_Data/cell_segmentation'
    dirs=glob(dir + '/DK55/CH3/*/punta*.csv')  
    dirs=['/'.join(d.split('/')[:-1]) for d in dirs]
    df_list=[]
    for dir in dirs:
        filename=glob(dir + '/punta*.csv')[0]
        if os.path.getsize(filename) == 1:
            continue
        df=pd.read_csv(filename)
        print(filename,df.shape)
        df_list.append(df)

    full_df=pd.concat(df_list)
    full_df.index=list(range(full_df.shape[0]))
    df=pd.DataFrame(full_df)

    # df = df.drop('label',axis=1)
    return df

def find_corresponding_row_index(all_segment,search_array):
    index_array = []
    i = 0
    print(len(search_array))
    for celli in search_array:
        diff = all_segment - celli
        diff[:,2] = diff[:,2]*100
        dist = np.sum(np.abs(diff),axis=1)
        cloest_segment = np.argmin(dist)
        if dist[cloest_segment]==0:
            index_array.append(cloest_segment)
        elif dist[cloest_segment]<50:
            index_array.append(cloest_segment)
            print(f'cannot find equal,subbing point with distance: {dist[cloest_segment]}')
        else:
            print('skipping')
            continue
        if i%100 == 0:
            print(i)
        i+=1
    return index_array

def create_positive_index(df):
    test_counts,train_sections = pk.load(open('/scratch/programming/categories.pkl','rb'))
    all_segment = np.array([df.col,df.row,df.section]).T

    cells = test_counts['detected by computer as sure, unmarked by human']
    cells = np.array([[ci[1]['x'],ci[1]['y'],ci[1]['section']] for ci in cells])
    cells_index = find_corresponding_row_index(all_segment,cells)

    original = train_sections['original training set after mind change']
    original = np.array([[ci[1]['x'],ci[1]['y'],ci[1]['section']] for ci in original])
    original_index = find_corresponding_row_index(all_segment,original)

    positive = test_counts['detected by computer as UNsure, marked by human as positive']
    positive = np.array([[ci[1]['x'],ci[1]['y'],ci[1]['section']] for ci in positive])
    positive_index = find_corresponding_row_index(all_segment,positive)

    additional_positive = test_counts['computer missed, human detected']
    additional_positive = np.array([[ci[1]['x'],ci[1]['y'],ci[1]['section']] for ci in additional_positive])
    additional_positive_index = find_corresponding_row_index(all_segment,additional_positive)
    index_dict = {}
    i = 0
    names = ['cells_index','original_index','positive_index','additional_positive_index']
    for indexi in [cells_index,original_index,positive_index,additional_positive_index]:
        index_dict[names[i]] = indexi
        i+=1

    dir = '/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55/'
    pk.dump(index_dict,open(dir+'positive_indicies.pkl','wb'))

if __name__ == '__main__':
    df = create_combined_features()
    dir = '/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55/all_features.csv'
    df.to_csv(dir,index = False)

    dir = '/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55/all_features.csv'
    df = pd.read_csv(dir)
    create_positive_index(df)
