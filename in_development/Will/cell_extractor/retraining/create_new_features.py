from glob import glob
import pandas as pd
import pickle as pk
import numpy as np
import os

def create_combined_features():
    dir = '/net/birdstore/Active_Atlas_Data/cell_segmentation'
    dirs=glob(dir + '/DK55/CH3/*/puntas*.csv')  
    dirs=['/'.join(d.split('/')[:-1]) for d in dirs]
    df_list=[]
    for dir in dirs:
        filename=glob(dir + '/puntas*.csv')[0]
        if os.path.getsize(filename) == 1:
            continue
        df=pd.read_csv(filename)
        print(filename,df.shape)
        df_list.append(df)
    len(df_list)
    full_df=pd.concat(df_list)
    full_df.index=list(range(full_df.shape[0]))
    df=pd.DataFrame(full_df)
    dir = '/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55/all_features.csv'
    df.to_csv(dir)
    return df

def find_corresponding_row_index(all_segment,search_array,index_array):
    i = 0
    print(len(search_array))
    for celli in search_array:
        diff = all_segment - celli
        cell_index = np.where(np.logical_not((diff).any(axis=1)))[0]
        if len(cell_index)==1:
            index_array.append(cell_index[0])
        else:
            diff[:,2] = diff[:,2]*100
            dist = np.sum(np.abs(diff),axis=1)
            minid = np.argmin(dist)
            if dist[minid]<50:
                index_array.append(minid)
                print(f'cannot find equal,subbing point with distance: {dist[minid]}')
            else:
                print('skipping')
                continue
        if i%100 == 0:
            print(i)
        i+=1
    return index_array

# create_combined_features()
dir = '/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55/all_features.csv'
df = pd.read_csv(dir)
test_counts,train_sections = pk.load(open('categories.pkl','rb'))
print()

all_segment = np.array([df.col,df.row,df.section]).T

cells = test_counts['detected by computer as sure, unmarked by human']
cells = np.array([[ci[1]['x'],ci[1]['y'],ci[1]['section']] for ci in cells])

original = train_sections['original training set after mind change']
original = np.array([[ci[1]['x'],ci[1]['y'],ci[1]['section']] for ci in original])

positive = test_counts['detected by computer as UNsure, marked by human as positive']
positive = np.array([[ci[1]['x'],ci[1]['y'],ci[1]['section']] for ci in positive])

positive_index = []
positive_index = find_corresponding_row_index(all_segment,cells,positive_index)
positive_index = find_corresponding_row_index(all_segment,positive,positive_index)
positive_index = find_corresponding_row_index(all_segment,original,positive_index)

npoints = len(df)
for i in range(npoints):
    if i%1000 == 0:
        print(f'{i}/{npoints}')
    i+=1
    if i in positive_index:
        df.at[i,'label'] = 1
    else:
        df.at[i,'label'] = 0
        
dir = '/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55/all_features_modified.csv'
df.to_csv(dir)
print('')

# negative = test_counts['detected by computer as sure, marked by human as negative']+test_counts['detected by computer as UNsure, marked by human as negative']
# negative = np.array([[ci[1]['x'],ci[1]['y'],ci[1]['section']] for ci in negative])
# negative_index = []
# negative_index = find_corresponding_row_index(all_segment,negative,negative_index)