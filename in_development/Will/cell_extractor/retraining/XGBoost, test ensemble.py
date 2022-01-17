
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from lib import XGBHelper as xgbh
import pandas as pd
from lib.logger import logger
import pickle as pk

def solve(x1,x2,y1,y2):
    b=(y1-y2)/(x1-x2)
    a=0.5*(y1+y2-b*(x1+x2))
    return a,b

a,b=solve(-1,5,2,4)
x=arange(-2,6)
plot(x,a+b*x)
grid()

def createDM(df):
    labels=df['label']
    features=df.drop('label',axis=1)
    return xgb.DMatrix(features, label=labels)

def split_data(df,frac=0.5):
    train = df.sample(frac = 0.5)
    test  = df.drop(train.index)

    trainDM=createDM(train)
    testDM=createDM(test)
    AllDM=createDM(df)
    return trainDM,testDM,AllDM

with open('../data/172/BoostedTrees.pkl','br') as pkl_file:
    bst_list=pk.load(pkl_file)

bad=[]
for section in [164,172,248]:
    filename='../data/%d/puntas.csv'%section

    df=pd.read_csv(filename)

    trainDM,testDM,AllDM=split_data(df)
    labels=AllDM.get_label()
    scores=np.zeros([df.shape[0],len(bst_list)])
    for i in range(len(bst_list)):
        bst=bst_list[i]
        scores[:,i] = bst.predict(AllDM, iteration_range=[1,bst.best_ntree_limit], output_margin=True)

    _max=np.max(scores,axis=1)
    _min=np.min(scores,axis=1)

    #figure(figsize=[15,10])
    #scatter((_min+_max)/2,_max-_min,c=labels)
    #title('min and max of scores for section %d, tree depth=1'%section)
    #xlabel('(max+min)/2')
    #ylabel('max-min')
    #grid()

    _mean=np.mean(scores,axis=1)
    _std=np.std(scores,axis=1)
    false_pos=np.nonzero((_mean>0)*(labels==0))[0]
    false_neg=np.nonzero((_mean<0)*(labels==1))[0]
    bad.append({'section':section,
               'false_pos':false_pos,
               'false_neg':false_neg})
    figure(figsize=[15,10])
    scatter(_mean,_std,c=labels)
    plot([0,-2.5],[1,2])
    plot([0,2.5],[1,2])

    title('mean and std for section %d, tree depth=1'%section)
    xlabel('mean')
    ylabel('std')
    grid()

full_df=pd.DataFrame(df)

df=df[Old]

with open('../data/172/BadExamples.pkl','bw') as pkl_file:
    pk.dump(bad,pkl_file)

for b in bad:
    print(b['section'],b['false_pos'].shape,b['false_neg'].shape)

with open('../data/172/BadExamples.pkl','bw') as pkl_file:
    pk.dump(bad,pkl_file)

plot([-1,5],[2,4])
a,b=solve(-1,5,2,4)
x=arange(-2,5)
plot(x,a+b*x)
plot([-1,-5],[2,4])
a,b=solve(-1,-5,2,4)
x=arange(-5,2)
plot(x,a+b*x)
plot([-1,-1],[2,0])




