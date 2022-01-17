# ## Setting Parameters for XG Boost
# * Maximum Depth of the Tree = 3 _(maximum depth of each decision trees)_
# * Step size shrinkage used in update to prevents overfitting = 0.3 _(how to weigh trees in subsequent iterations)_
# * Maximum Number of Iterations = 1000 _(total number trees for boosting)_
# * Early Stop if score on Validation does not improve for 5 iterations
# 
# [Full description of options](https://xgboost.readthedocs.io/en/latest//parameter.html)

import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from cell_extractor.lib import XGBHelper as xgbh
import pandas as pd
from cell_extractor.lib.logger import logger
from glob import glob
from sklearn.metrics import roc_curve
import pickle as pk
from DefinePredictor import *

print(xgb.__version__)

def createDM(df):
    labels=df['label']
    features=df.drop('label',axis=1)
    return xgb.DMatrix(features, label=labels)

def get_train_and_test(df,frac=0.5):
    train = pd.DataFrame(df.sample(frac = 0.5))
    test = df.drop(train.index,axis=0)
    print(train.shape,test.shape,train.index.shape,df.shape)

    train=createDM(train)
    test=createDM(test)
    all=createDM(df)
    return train,test,all

def create_parameter():
    param = {}
    depth_of_tree = 3
    shrinkage_parameter = 0.3
    eval_metric = ['error','logloss']
    param['max_depth']= depth_of_tree
    param['eta'] =shrinkage_parameter
    param['objective'] = 'binary:logistic'
    param['nthread'] = 7 
    param['eval_metric'] = eval_metric[1]
    print(param)
    return param

def test_xgboost(depth=1,num_round=100,param = {},evallist = []):
    param['max_depth']= depth   # depth of tree
    fig, axes = plt.subplots(1,2,figsize=(12,5))
    i=0
    for _eval in ['error','logloss']:
        Logger=logger()
        logall=Logger.get_logger()  # Set logger to collect results
        param['eval_metric'] = _eval 
        bst = xgb.train(param, train, num_round, evallist, verbose_eval=False, callbacks=[logall])
        df=Logger.parse_log(ax=axes[i])
        i+=1
    return bst,Logger

def plot_margins(_train_size):
    plt.figure(figsize=(8, 6))
    for i in range(10):
        train,test=get_train_and_test(df)
        legends=[]
        for num_round in [100]:
            bst = xgb.train(param, train, num_round, evallist, verbose_eval=False)
            y_pred = bst.predict(test, iteration_range=[0,bst.best_ntree_limit], output_margin=True)
            thresholds = sorted(np.unique(np.round(y_pred, 2)))
            error_cuv, error_ger = xgbh.get_error_values(y_pred, y_test, thresholds)
            legends += ['Cuviers %d'%num_round, 'Gervais %d'%num_round]
            _style=['y','g'] if num_round==100 else ['b', 'r']
            xgbh.get_margin_plot(error_cuv, error_ger, thresholds, legends = legends, style=_style)
        
        plt.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
        plt.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
        thr = thresholds/(np.max(thresholds) - np.min(thresholds))
    plt.title('data_size=%4.3f'%(X_train.shape[0]))
    plt.show()

def get_error_ranges(error_cuv_samp, error_ger_samp, thresholds_samp, num_chunks=20):
    error_cuv_bin = np.array(np.array(error_cuv_samp) * num_chunks, dtype=int)
    error_cuv_bin[error_cuv_bin == num_chunks] = num_chunks - 1
    error_ger_bin = np.array(np.array(error_ger_samp) * num_chunks, dtype=int)
    error_ger_bin[error_ger_bin == num_chunks] = num_chunks - 1
    
    min_cuv = np.zeros(num_chunks, dtype=float)
    max_cuv = np.zeros(num_chunks, dtype=float)
    min_ger = np.zeros(num_chunks, dtype=float)
    max_ger = np.zeros(num_chunks, dtype=float)
    
    normalizing_factor = (max(thresholds_samp) - min(thresholds_samp))
    
    for i in range(num_chunks):
        min_cuv[i] = thresholds_samp[np.min(np.where(error_cuv_bin == i))]/normalizing_factor
        max_cuv[i] = thresholds_samp[np.max(np.where(error_cuv_bin == i))]/normalizing_factor
        min_ger[i] = thresholds_samp[np.min(np.where(error_ger_bin == i))]/normalizing_factor
        max_ger[i] = thresholds_samp[np.max(np.where(error_ger_bin == i))]/normalizing_factor
            
    return min_cuv, max_cuv, min_ger, max_ger

def gen_scale(n,reverse=False):
    s=arange(0,1,1/n)
    while s.shape[0] !=n:
        if s.shape[0]>n:
            s=s[:n]
        if s.shape[0]<n:
            s=arange(0,1,1/(n+0.1))
    if reverse:
        s=s[-1::-1]
    return s

def generate_samples(data, size=500, num_chunks=20):
    for i in range(200):
        if i == 0:
            min_cuv = np.zeros(num_chunks, dtype=float)
            max_cuv = np.zeros(num_chunks, dtype=float)
            min_ger = np.zeros(num_chunks, dtype=float)
            max_ger = np.zeros(num_chunks, dtype=float)
        
        samp_indices = np.random.randint(len(data), size=size)
        
        X_samp = data[samp_indices, :-1]
        y_samp = np.array(data[samp_indices, -1], dtype=int)
        
        dsamp = xgb.DMatrix(X_samp, label=y_samp)    
        y_samp_pred = bst.predict(dsamp, iteration_range=[0,bst.best_ntree_limit], output_margin=True)

        thresholds_samp = sorted(np.unique(np.round(y_samp_pred, 2)))
        error_cuv_samp, error_ger_samp = xgbh.get_error_values(y_samp_pred, y_samp, thresholds_samp)
        
        min_cuv_samp, max_cuv_samp, min_ger_samp, max_ger_samp = get_error_ranges(error_cuv_samp, error_ger_samp, thresholds_samp)
        
        if i == 0:
            min_cuv = min_cuv_samp
            max_cuv = max_cuv_samp
            min_ger = min_ger_samp
            max_ger = max_ger_samp
        else:
            min_cuv[min_cuv > min_cuv_samp] = min_cuv_samp[min_cuv > min_cuv_samp]
            max_cuv[max_cuv < max_cuv_samp] = max_cuv_samp[max_cuv < max_cuv_samp]
            min_ger[min_ger > min_ger_samp] = min_ger_samp[min_ger > min_ger_samp]
            max_ger[max_ger < max_ger_samp] = max_ger_samp[max_ger < max_ger_samp]         
    
    for i in range(20):
        plt.plot([min_cuv[i], max_cuv[i]], [i/20.0, i/20.0], 'b')
        plt.plot([min_ger[i], max_ger[i]], [i/20.0, i/20.0], 'r')

def solve(x1,x2,y1,y2):
    b=(y1-y2)/(x1-x2)
    a=0.5*(y1+y2-b*(x1+x2))
    return a,b

def plot_roc(test,pred):
    plt.figure(figsize=(8, 6))
    fpr, tpr, thresholds = roc_curve(y_test, y_pred)
    plt.plot(fpr, tpr)
    plt.xlim([0,1])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title("ROC Curve after")
    plt.grid()
    plt.show()

dir = '/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55/all_features_modified.csv'
df = pd.read_csv(dir)
drops = ['animal', 'section', 'index', 'row', 'col'] 
df=df.drop(drops,axis=1)

train,test,all=get_train_and_test(df)
print(train.num_row(), test.num_row(), all.num_row())
param = create_parameter()
evallist = [(train, 'train'), (test, 'eval')]

bst,log = test_xgboost(depth=1,num_round=1000,param = param,evallist = evallist)
bst,log = test_xgboost(depth=2,num_round=1000,param = param)
bst,log = test_xgboost(depth=3,num_round=400,param = param)
bst,log = test_xgboost(depth=4,num_round=1000,param = param)
bst,log = test_xgboost(depth=5,num_round=1000,param = param)


num_round=250
bst = xgb.train(param, train, num_round, evallist, verbose_eval=False)
y_pred = bst.predict(test, iteration_range=[1,bst.best_ntree_limit], output_margin=True)
y_test=test.get_label()
plot_roc(y_test,y_pred)

pos_preds=y_pred[y_test==1]
neg_preds=y_pred[y_test==0]
pos_preds.shape,neg_preds.shape

hist([pos_preds,neg_preds],bins=20);

figure(figsize=[15,8])
num_round=200

bst_list=[]
for i in range(30):
    train,test,all=get_train_and_test(df)
    bst = xgb.train(param, train, num_round, evallist, verbose_eval=False)
    bst_list.append(bst)
    y_pred = bst.predict(test, iteration_range=[1,bst.best_ntree_limit], output_margin=True)
    y_test=test.get_label()
    pos_preds=y_pred[y_test==1]
    neg_preds=y_pred[y_test==0]
    pos_preds=sort(pos_preds)
    neg_preds=sort(neg_preds)
    plot(pos_preds,gen_scale(pos_preds.shape[0]));
    plot(neg_preds,gen_scale(neg_preds.shape[0],reverse=True))

DATA_DIR='/data/cell_segmentation/'
with open(DATA_DIR+'BoostedTrees.pkl','bw') as pkl_file:
    pk.dump(bst_list,pkl_file)

with open(DATA_DIR+'BoostedTrees.pkl','br') as pkl_file:
    bst_list=pk.load(pkl_file)

train,test,all=get_train_and_test(df)
labels=all.get_label()
scores=np.zeros([df.shape[0],len(bst_list)])
for i in range(len(bst_list)):
    bst=bst_list[i]
    scores[:,i] = bst.predict(all, iteration_range=[1,bst.best_ntree_limit], output_margin=True)
_max=np.max(scores,axis=1)
_min=np.min(scores,axis=1)
_mean=np.mean(scores,axis=1)
_std=np.std(scores,axis=1)

figure(figsize=[15,10])
scatter(_mean,_std,c=labels,s=3)
title('mean and std of scores for 30 classifiers')
xlabel('mean')
ylabel('std')
grid()

_mean.shape, full_df.shape, _std.shape
full_df['mean_score']=_mean
full_df['std_score']=_std
full_df.columns


predictions=[]
for i,row in full_df.iterrows():
    p=decision(float(row['mean_score']),float(row['std_score']))
    predictions.append(p)
full_df['predictions']=predictions

full_df.to_csv(DATA_DIR+'demo_scores.csv')

full_df.columns

detection_df=full_df[full_df['predictions']!=-2]
detection_df = detection_df[['animal', 'section', 'row', 'col','label', 'mean_score',
       'std_score', 'predictions']]
detection_df.head()

detection_df.to_csv(DATA_DIR+'detections_DK55.csv',index=False)

from collections import Counter
Counter(predictions)

figure(figsize=[15,10])
scatter(_mean,_std,c=predictions+labels,s=5)

title('mean and std of scores for 30 classifiers')
xlabel('mean')
ylabel('std')
grid()

a,b=solve(-1,5,2,4)
x=arange(-2,5)
plot(x,a+b*x)

with open('../data/172/BoostedTrees.pkl','bw') as pkl_file:
    pk.dump(bst_list,pkl_file)

plot_margins(0.03)
plot_margins(0.1)
plot_margins(0.8)

data  = np.load("Data/processed_data_15mb.np")

    
plt.figure(figsize=(8, 6))
thr_lower_index = np.min(np.where((tpr > 0.95)))
thr_upper_index = np.max(np.where((tpr  < 0.6)))
thr_lower, thr_upper = thresholds[thr_lower_index], thresholds[thr_upper_index]
thr_lower_norm = thr_lower/(np.max(thresholds) - np.min(thresholds))
thr_upper_norm = thr_upper/(np.max(thresholds) - np.min(thresholds))
print("Thresholds (lower, upper):", thr_lower_norm, thr_upper_norm)

generate_samples(data, num_chunks=20)
plt.plot([thr_lower_norm, thr_lower_norm], [0, 1], 'm:')
plt.plot([thr_upper_norm, thr_upper_norm], [0, 1], 'm:')
plt.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
plt.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
plt.xlabel('Score')
plt.ylabel('CDF')
legends = ['Cuviers_100', 'Gervais_100']
plt.legend(legends)
plt.show()



