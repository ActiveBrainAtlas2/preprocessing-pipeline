# ## Setting Parameters for XG Boost
# * Maximum Depth of the Tree = 3 _(maximum depth of each decision trees)_
# * Step size shrinkage used in update to prevents overfitting = 0.3 _(how to weigh trees in subsequent iterations)_
# * Maximum Number of Iterations = 1000 _(total number trees for boosting)_
# * Early Stop if score on Validation does not improve for 5 iterations
# 
# [Full description of options](https://xgboost.readthedocs.io/en/latest//parameter.html)

import numpy as np
import xgboost as xgb
import matplotlib.pyplot as plt
import pandas as pd
# from cell_extractor.retraining.lib.logger import logger
from sklearn.metrics import roc_curve
import pickle as pk
from collections import Counter
from cell_extractor.CellDetectorBase import CellDetectorBase
print(xgb.__version__)

# %load lib/Logger.py
import pandas as pd

class logger:
    """A helper class for defining a logger function and for parsing the
log, assuming it is created by XGBoost.
    Typical use:

    Logger=logger()
    logall=Logger.get_logger()

    bst = xgb.train(plst, dtrain, num_round, evallist, verbose_eval=False, callbacks=[logall])
    D=Logger.parse_log() #returns a dataframe with the logs.
    """
    def __init__(self):
        self.log=[]
         
    def get_logger(self):
        def logall(*argv,**argc):
            self.log.append(*argv)
        return logall

    def parse_log(self,ax=None):
        """ parse the log and generate plots"""
        D={'iter':[]}
        for _env in self.log:
            current_err={key:val for key,val in _env.evaluation_result_list}
            D['iter'].append(_env.iteration)
            for k in current_err.keys():
                if k in D:
                    D[k].append(current_err[k])
                else:
                    D[k]=[current_err[k]]
        for k in list(D.keys()):
            if len(D[k])==0:
                del D[k]

        df=pd.DataFrame(D)
        df=df.set_index('iter')
        test_col=[c for c in df.columns if 'eval' in c][0]
        print('test column=',test_col)
        _min=df[test_col].min()
        index_min=df[test_col].idxmin()
        title='min of %s=%f at %d'%(test_col,_min,index_min)
        if not ax is None:
            df.plot(grid=True,title=title,ax=ax)  
        return df


class CellDetectorTrainer(CellDetectorBase,DataLoader):
    def __init__(self,animal,round =2):
        super().__init__(animal,round = round)
        self.last_round = CellDetectorBase(animal,round = round-1)
        self.init_parameter()

    def createDM(self,df):
        labels=df['label']
        features=df.drop('label',axis=1)
        return xgb.DMatrix(features, label=labels)

    def get_train_and_test(self,df,frac=0.5):
        train = pd.DataFrame(df.sample(frac=frac))
        test = df.drop(train.index,axis=0)
        print(train.shape,test.shape,train.index.shape,df.shape)
        train=self.createDM(train)
        test=self.createDM(test)
        all=self.createDM(df)
        return train,test,all

    def init_parameter(self):
        self.default_param = {}
        shrinkage_parameter = 0.3
        self.default_param['eta'] =shrinkage_parameter
        self.default_param['objective'] = 'binary:logistic'
        self.default_param['nthread'] = 7 
        print(self.default_param)

    def train_classifier(self,features,depth,niter):
        param = self.default_param
        param['max_depth'] = depth
        df = features
        train,test,all=self.get_train_and_test(df)
        evallist = [(train, 'train'), (test, 'eval')]
        bst_list=[]
        for _ in range(30):
            train,test,all=self.get_train_and_test(df)
            bst = xgb.train(self.param, train, niter, evallist, verbose_eval=False)
            bst_list.append(bst)
        return bst_list
    
    def test_xgboost(self,df,depths = [1,3,5],num_round = 1000):
        for depthi in depths:
            self.test_xgboost_at_depthi(df,depth = depthi,num_round=num_round)

    def test_xgboost_at_depthi(self,features,depth=1,num_round=1000):
        param = self.default_param
        param['max_depth']= depth
        train,test,_=self.get_train_and_test(features)
        evallist = [(train, 'train'), (test, 'eval')]
        train,test,_=self.get_train_and_test(features)
        _, axes = plt.subplots(1,2,figsize=(12,5))
        i=0
        for _eval in ['error','logloss']:
            Logger=logger()
            logall=Logger.get_logger()  
            param['eval_metric'] = _eval 
            bst = xgb.train(param, train, num_round, evallist, verbose_eval=False, callbacks=[logall])
            _=Logger.parse_log(ax=axes[i])
            i+=1
        plt.show()
        return bst,Logger

class DataLoader:
    def find_corresponding_row_index(self,all_segment,search_array):
        index_array = []
        i = 0
        for celli in search_array:
            section = celli[2]
            in_section = all_segment[:,2]==section
            segments_in_section = all_segment[in_section,:2]
            diff = segments_in_section[:,:2]-celli[:2]
            dist = np.sqrt(np.sum(np.square(diff),axis=1))
            if len(dist) == 0:
                print(celli)
                print(i)
            cloest_segment = np.argmin(dist)
            corresponding_id = np.where(np.cumsum(in_section)==cloest_segment+1)[0][0]
            if dist[cloest_segment]==0:
                index_array.append(corresponding_id)
            elif dist[cloest_segment]<20:
                index_array.append(corresponding_id)
                print(f'cannot find equal,subbing point with distance: {dist[cloest_segment]}')
            else:
                print('skipping')
                continue
            if i%1000 == 0:
                print(i)
            i+=1
        return index_array

    def load_original_training_features():
        dirs=glob('/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55/CH3/*/DK55*.csv')  
        dirs=['/'.join(d.split('/')[:-1]) for d in dirs]
        df_list=[]
        for dir in dirs:
            filename=glob(dir + '/puntas*.csv')[0]
            df=pd.read_csv(filename)
            df_list.append(df)
        len(df_list)
        full_df=pd.concat(df_list)
        full_df.index=list(range(full_df.shape[0]))
        oog=pd.DataFrame(full_df)
        drops = ['animal', 'section', 'index', 'row', 'col'] 
        oog=oog.drop(drops,axis=1)
        return oog
    
    def load_new_features(self):
        dir = '/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55/all_features.csv'
        df = pd.read_csv(dir,index_col = 0)
        base = CellDetectorBase('DK55',round=1)
        test_counts,train_sections = pk.load(open(base.QUALIFICATIONS,'rb'))
        all_segment = np.array([df.col,df.row,df.section]).T

        base = CellDetectorBase('DK55',round=1)
        test_counts,train_sections = pk.load(open(base.QUALIFICATIONS,'rb'))
        all_segment = np.array([df.col,df.row,df.section]).T

        cells = test_counts['computer sure, human unmarked']
        cells = np.array([[ci[1]['x'],ci[1]['y'],ci[1]['section']] for ci in cells])
        cells_index = self.find_corresponding_row_index(all_segment,cells)

        original = train_sections['original training set after mind change']
        original = np.array([[ci[1]['x'],ci[1]['y'],ci[1]['section']] for ci in original])
        original_index = self.find_corresponding_row_index(all_segment,original)

        qc_annotation_input_path = '/scratch/programming/preprocessing-pipeline/in_development/yoav/marked_cell_detector/data2/'
        neg = qc_annotation_input_path+'/DK55_premotor_manual_negative_round1_2021-12-09.csv'
        pos = qc_annotation_input_path+'/DK55_premotor_manual_positive_round1_2021-12-09.csv'
        neg = pd.read_csv(neg,header=None).to_numpy()
        pos = pd.read_csv(pos,header=None).to_numpy()
        positive = self.find_corresponding_row_index(all_segment,pos)
        negative = self.find_corresponding_row_index(all_segment,neg)

        dirs=glob('/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55/CH3/*/DK55*.csv') 
        manual_sections = [int(i.split('/')[-2]) for i in dirs]

        dir = '/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55/all_features.csv'
        df = pd.read_csv(dir,index_col = 0)
        labels = np.zeros(len(df))
        positive_index = cells_index+original_index+positive
        # positive_index = original_index
        for i in positive_index:
            labels[i] = 1
        df['label'] = labels
        # drops = ['animal', 'section', 'index', 'row', 'col'] 
        # df=df.drop(drops,axis=1)
        # include = [labels[i]==1 or i in negative or all_segment[i,2] in manual_sections for i in range(len(df))]
        # include = [labels[i]==1 or all_segment[i,2] in manual_sections for i in range(len(df))]
        # df_in_section = df[include]
        df_in_section = df

    def load_refined_original_feature(self):
        dir = '/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55/all_features.csv'
        df = pd.read_csv(dir,index_col = 0)
        base = CellDetectorBase('DK55',round=1)
        test_counts,train_sections = pk.load(open(base.QUALIFICATIONS,'rb'))
        all_segment = np.array([df.col,df.row,df.section]).T

        original = train_sections['original training set after mind change']
        original = np.array([[ci[1]['x'],ci[1]['y'],ci[1]['section']] for ci in original])
        original_index = self.find_corresponding_row_index(all_segment,original)

        dirs=glob('/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55/CH3/*/DK55*.csv') 
        manual_sections = [int(i.split('/')[-2]) for i in dirs]
        dir = '/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55/all_features.csv'
        df = pd.read_csv(dir,index_col = 0)
        labels = np.zeros(len(df))
        for i in original_index:
            labels[i] = 1
        df['label'] = labels
        include = [labels[i]==1 or all_segment[i,2] in manual_sections for i in range(len(df))]
        df_in_section = df[include]
        return df_in_section

if __name__=='__main__':
    trainer = CellDetectorTrainer('DK55',round = 2)
    manual_df = trainer.get_combined_features_of_train_sections()
    # trainer.test_xgboost(trainer.combined_features)
    trainer.test_xgboost(manual_df)