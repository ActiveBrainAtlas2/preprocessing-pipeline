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
from cell_extractor.retraining.lib import XGBHelper as xgbh
import pandas as pd
from cell_extractor.retraining.lib.logger import logger
from glob import glob
from sklearn.metrics import roc_curve
import pickle as pk
# from DefinePredictor import *
from collections import Counter

print(xgb.__version__)

class CellDetectorTrainer:
    def __init__(self):
        self.init_parameter()
        self.features = self.load_features()
        self.load_features()

    def createDM(self,df):
        labels=df['label']
        features=df.drop('label',axis=1)
        return xgb.DMatrix(features, label=labels)

    def get_train_and_test(self,df,frac=0.5):
        train = pd.DataFrame(df.sample(frac=0.5))
        test = df.drop(train.index,axis=0)
        print(train.shape,test.shape,train.index.shape,df.shape)
        train=self.createDM(train)
        test=self.createDM(test)
        all=self.createDM(df)
        return train,test,all

    def init_parameter(self):
        self.param = {}
        shrinkage_parameter = 0.3
        eval_metric = ['error','logloss']
        self.param['eta'] =shrinkage_parameter
        self.param['objective'] = 'binary:logistic'
        self.param['nthread'] = 7 
        self.param['eval_metric'] = eval_metric[1]
        print(self.param)
    
    def load_features(self):
        dir = '/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55/all_features_og.csv'
        df = pd.read_csv(dir)
        drops = ['animal', 'section', 'index', 'row', 'col'] 
        df=df.drop(drops,axis=1)
        return df

    def test_classifier(self,depth,niter):
        param = self.param
        param['max_depth'] = depth
        df = self.features
        train,test,all=self.get_train_and_test(df)
        print(train.num_row(), test.num_row(), all.num_row())
        evallist = [(train, 'train'), (test, 'eval')]
        bst_list=[]
        for i in range(30):
            train,test,all=self.get_train_and_test(df)
            bst = xgb.train(self.param, train, niter, evallist, verbose_eval=False)
            bst_list.append(bst)
        return bst_list
    
    def test_xgboost(self,depth=1,num_round=100):
        param = self.param
        param['max_depth']= depth
        train,test,_=self.get_train_and_test(self.features)
        evallist = [(train, 'train'), (test, 'eval')]
        _, axes = plt.subplots(1,2,figsize=(12,5))
        i=0
        for _eval in ['error','logloss']:
            Logger=logger()
            logall=Logger.get_logger()  
            param['eval_metric'] = _eval 
            bst = xgb.train(param, train, num_round, evallist, verbose_eval=False, callbacks=[logall])
            _=Logger.parse_log(ax=axes[i])
            i+=1
        return bst,Logger