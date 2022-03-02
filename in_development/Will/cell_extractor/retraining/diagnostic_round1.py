
print()
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import distance_matrix
import pickle as pk

def load_annotations():
    data2 = os.path.abspath(os.path.dirname(__file__)+'/../../../yoav/'+
        'marked_cell_detector/data2/')
    file={'manual_train':       data2+'/DK55_premotor_manual_2021-12-09.csv',
        'manual_negative':    data2+'/DK55_premotor_manual_negative_round1_2021-12-09.csv',
        'manual_positive':    data2+'/DK55_premotor_manual_positive_round1_2021-12-09.csv',
        'computer_sure':      data2+'/DK55_premotor_sure_detection_2021-12-09.csv',
        'computer_unsure':    data2+'/DK55_premotor_unsure_detection_2021-12-09.csv'}
    dfs={}
    for name,path in file.items():
        dfs[name]= pd.read_csv(path,header=None)
        dfs[name]['name']=name
    All=pd.concat([dfs[key] for key in dfs])
    All.columns=['x','y','section','name']
    All['x']=np.round(All['x'])
    All['y']=np.round(All['y'])
    return All

def get_distance(All):
    All['section']*=1000
    Distances=distance_matrix(np.array(All.iloc[:,:3]),np.array(All.iloc[:,:3]))
    All['section']/=1000
    return Distances

def find_union(A,B):
    for b in B:
        if not b in A:
            A.append(b)
    B=A
    return A,B

def check(L,yes=None,no=None,size_min=None,size_max=None):
    """ Return true if names in yes appear in L, names in no do not appear, 
        and the length of the list is between min_size and max_size"""

    if not yes is None:
        for e in yes:
            if not e in L:
                return False
            
    if not no is None:
        for e in no:
            if e in L:
                return False
    
    if not size_min is None:
            if len(L)<size_min:
                return False
            
    if not size_max is None:
            if len(L)>size_max:
                return False

    return True

def prep(All,Distances):
    very_small=Distances<30
    pairs=np.transpose(np.nonzero(very_small))
    pairs=pairs[pairs[:,0]< pairs[:,1],:]

    sets={} #an indexed set of hashes
    for i in range(All.shape[0]):
        sets[i]=[i]

    for i in range(pairs.shape[0]):
        first,second=pairs[i]
        sets[first],sets[second]=find_union(sets[first],sets[second])

    print('before removing duplicates',len(sets))
    for i in range(len(sets)):
        if not i in sets:
            continue
        for j in sets[i]:
            if j != i and j in sets:
                del sets[j]
    print('after removing duplicates',len(sets))

    names=list(All.iloc[:,-1])
    set_names={}
    for key in sets:
        set_names[key]=[names[i] for i in sets[key]]
    list(set_names.items())[:5]

    sections=[]
    for i in range(All.shape[0]):
        if All.iloc[i,3]=='manual_train':
            sections.append(int(All.iloc[i,2]))
    sections=np.unique(sections)
    return sets,set_names,sections

All = load_annotations()
Distances = get_distance(All)
sets,set_names,sections = prep(All,Distances)

train_sections={}
is_category = []
for i in sets:
    if int(All.iloc[i,2]) in sections:
        if set_names[i]==['computer_sure']:
            is_category.append((i,dict(All.iloc[i,:])))
train_sections['Computer Detected in train sections, Human Missed']=is_category

is_category = []
for i in sets:
        if int(All.iloc[i,2]) in sections:
            if 'manual_train' in set_names[i]:
                is_category.append((i,dict(All.iloc[i,:])))
train_sections['total train']=is_category

contra=[]
is_category = []
for i in sets:
    if int(All.iloc[i,2]) in sections:
        if check(set_names[i],yes=['manual_negative','manual_train']):
            for j in sets[i]:
                contra.append(j)
            is_category.append((i,dict(All.iloc[i,:])))
train_sections['Human mind change']=is_category

contra=[]
is_category = []
for i in sets:
    if int(All.iloc[i,2]) in sections:
        if check(set_names[i],yes=['manual_train'],no=['manual_negative']):
            for j in sets[i]:
                contra.append(j)
            is_category.append((i,dict(All.iloc[i,:])))
train_sections['original training set after mind change']=is_category

test_counts={}
is_category = []
for i in sets:
    if  check(set_names[i],yes=['manual_positive'],no=['computer_sure','computer_unsure'],size_max=1):
        is_category.append((i,dict(All.iloc[i,:])))
test_counts['computer missed, human detected']=is_category

label="detected by computer as sure, marked by human as negative"
is_category = []
for i in sets:
    if  check(set_names[i],yes=['computer_sure','manual_negative'],size_max=2):
            is_category.append((i,dict(All.iloc[i,:])))
test_counts[label]=is_category

label="detected by computer as UNsure, marked by human as negative"
is_category = []
for i in sets:
    if  check(set_names[i],yes=['computer_unsure','manual_negative'],size_max=2):
            is_category.append((i,dict(All.iloc[i,:])))
test_counts[label]=is_category

label="detected by computer as UNsure, marked by human as positive"
is_category = []
for i in sets:
    if  check(set_names[i],yes=['computer_unsure','manual_positive'],size_max=2):
            is_category.append((i,dict(All.iloc[i,:])))
test_counts[label]=is_category

label="Total computer as UNsure"
is_category = []
for i in sets:
    if  check(set_names[i],yes=['computer_unsure'],size_max=2):
            is_category.append((i,dict(All.iloc[i,:])))
test_counts[label]=is_category

label="Total computer as UNsure, unmarked by human"
is_category = []
for i in sets:
    if  check(set_names[i],yes=['computer_unsure'],size_max=1):
            is_category.append((i,dict(All.iloc[i,:])))
test_counts[label]=is_category

label="detected by computer as sure, unmarked by human"
is_category = []
for i in sets:
    if  check(set_names[i],yes=['computer_sure'],size_max=1):
            is_category.append((i,dict(All.iloc[i,:])))
test_counts[label]=is_category

label="More than 2 labels (excluding train)"
is_category = []
for i in sets:
    if  check(set_names[i],no=['manual_train'],size_min=3):
        is_category.append((i,dict(All.iloc[i,:])))
test_counts[label]=is_category


for keyi in train_sections:
    print(keyi)
    print(len(train_sections[keyi]))

for keyi in test_counts:
    print(keyi)
    print(len(test_counts[keyi]))

pk.dump((test_counts,train_sections),open('categories.pkl','wb'))