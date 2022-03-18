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
from lib.logger import logger
from sklearn.metrics import roc_curve
import pickle as pk
from collections import Counter
from cell_extractor.CellDetectorBase import CellDetectorBase
print(xgb.__version__)
from glob import glob
# %load lib/Logger.py
import pandas as pd
from cell_extractor.Predictor import Predictor
from cell_extractor.CellAnnotationUtilities import CellAnnotationUtilities

from cell_extractor.Detector import Detector   

class DataLoader(CellAnnotationUtilities):
    def load_original_training_features(self):
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
    
    def load_new_features_with_coordinate(self):
        dir = '/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55/all_features.csv'
        df = pd.read_csv(dir,index_col = 0)
        base = CellDetectorBase('DK55',round=1)
        test_counts,train_sections = pk.load(open(base.QUALIFICATIONS,'rb'))
        all_segment = np.array([df.col,df.row,df.section]).T

        cells = test_counts['computer sure, human unmarked']
        cells = np.array([[ci[1]['x'],ci[1]['y'],ci[1]['section']] for ci in cells])
        cells_index = self.find_cloest_neighbor_among_points(all_segment,cells)

        original = train_sections['original training set after mind change']
        original = np.array([[ci[1]['x'],ci[1]['y'],ci[1]['section']] for ci in original])
        original_index = self.find_cloest_neighbor_among_points(all_segment,original)

        qc_annotation_input_path = '/scratch/programming/preprocessing-pipeline/in_development/yoav/marked_cell_detector/data2/'
        neg = qc_annotation_input_path+'/DK55_premotor_manual_negative_round1_2021-12-09.csv'
        pos = qc_annotation_input_path+'/DK55_premotor_manual_positive_round1_2021-12-09.csv'
        neg = pd.read_csv(neg,header=None).to_numpy()
        pos = pd.read_csv(pos,header=None).to_numpy()
        positive = self.find_cloest_neighbor_among_points(all_segment,pos)
        negative = self.find_cloest_neighbor_among_points(all_segment,neg)
        dirs=glob('/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55/CH3/*/DK55*.csv') 
        manual_sections = [int(i.split('/')[-2]) for i in dirs]
        labels = np.zeros(len(df))
        positive_index = cells_index+original_index+positive
        for i in positive_index:
            labels[i] = 1
        df['label'] = labels
        include = [labels[i]==1 or i in negative or all_segment[i,2] in manual_sections for i in range(len(df))]
        df_in_section = df[include]
        return df_in_section

    def load_new_features(self):
        df_in_section = self.load_new_features_with_coordinate()
        drops = ['animal', 'section', 'index', 'row', 'col'] 
        df_in_section=df_in_section.drop(drops,axis=1)
        return df_in_section

    def load_refined_original_feature(self):
        dir = '/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55/all_features.csv'
        df = pd.read_csv(dir,index_col = 0)
        base = CellDetectorBase('DK55',round=1)
        test_counts,train_sections = pk.load(open(base.QUALIFICATIONS,'rb'))
        all_segment = np.array([df.col,df.row,df.section]).T

        original = train_sections['original training set after mind change']
        original = np.array([[ci[1]['x'],ci[1]['y'],ci[1]['section']] for ci in original])
        original_index = self.find_cloest_neighbor_among_points(all_segment,original)

        dirs=glob('/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55/CH3/*/DK55*.csv') 
        manual_sections = [int(i.split('/')[-2]) for i in dirs]
        labels = np.zeros(len(df))
        for i in original_index:
            labels[i] = 1
        df['label'] = labels
        drops = ['animal', 'section', 'index', 'row', 'col'] 
        df=df.drop(drops,axis=1)
        include = [labels[i]==1 or all_segment[i,2] in manual_sections for i in range(len(df))]
        df_in_section = df[include]
        return df_in_section

class CellDetectorTrainer(Detector,DataLoader):
    def __init__(self,animal,round =2):
        super().__init__(animal,round = round)
        self.last_round = CellDetectorBase(animal,round = round-1)
        self.init_parameter()
        self.predictor = Predictor()

    def gen_scale(self,n,reverse=False):
        s=np.arange(0,1,1/n)
        while s.shape[0] !=n:
            if s.shape[0]>n:
                s=s[:n]
            if s.shape[0]<n:
                s=np.arange(0,1,1/(n+0.1))
        if reverse:
            s=s[-1::-1]
        return s

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
            bst = xgb.train(param, train, niter, evallist, verbose_eval=False)
            bst_list.append(bst)
            y_pred = bst.predict(test, iteration_range=[1,bst.best_ntree_limit], output_margin=True)
            y_test=test.get_label()
            pos_preds=y_pred[y_test==1]
            neg_preds=y_pred[y_test==0]
            pos_preds=np.sort(pos_preds)
            neg_preds=np.sort(neg_preds)
            plt.plot(pos_preds,self.gen_scale(pos_preds.shape[0]));
            plt.plot(neg_preds,self.gen_scale(neg_preds.shape[0],reverse=True))
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
        print(depth)
        return bst,Logger
    
    def plot_score_scatter(self,df,bst_tree):
        scores,labels,_mean,_std = self.calculate_scores(df,bst_tree)
        plt.figure(figsize=[15,10])
        plt.scatter(_mean,_std,c=labels,s=3)
        plt.title('mean and std of scores for 30 classifiers')
        plt.xlabel('mean')
        plt.ylabel('std')
        plt.grid()
    
    def plot_decision_scatter(self,features,model):
        scores,labels,_mean,_std = self.calculate_scores(features,model)
        predictions=self.get_prediction(_mean,_std)
        plt.figure(figsize=[15,10])
        plt.scatter(_mean,_std,c=predictions+labels,s=5)
        plt.title('mean and std of scores for 30 classifiers')
        plt.xlabel('mean')
        plt.ylabel('std')
        plt.grid()
    
    def save_predictions(self,features,bst_list):
        detection_df = self.load_new_features_with_coordinate()
        scores,labels,_mean,_std = self.calculate_scores(features,bst_list)
        predictions=self.get_prediction(_mean,_std)
        detection_df['mean_score'],detection_df['std_score'] = _mean,_std
        detection_df['label'] = labels
        detection_df['predictions'] = predictions
        detection_df=detection_df[predictions!=-2]
        detection_df = detection_df[['animal', 'section', 'row', 'col','label', 'mean_score','std_score', 'predictions']]
        detection_df.to_csv(self.DETECTION_RESULT_DIR,index=False)
    
    def load_detections(self):
        return pd.read_csv(self.DETECTION_RESULT_DIR)
    
    def add_detection_to_database(self):
        detection_df = trainer.load_detections()
        points = np.array([detection_df.col,detection_df.row,detection_df.section]).T
        for pointi in points:
            pointi = pointi*np.array([0.325,0.325,20])
            trainer.sqlController.add_layer_data_row(trainer.animal,34,1,pointi,52,f'detected_soma_round_{self.round}')

if __name__=='__main__':
    trainer = CellDetectorTrainer('DK55',round = 2)
    manual_df = trainer.get_combined_features_of_train_sections()
    trainer.test_xgboost(manual_df)