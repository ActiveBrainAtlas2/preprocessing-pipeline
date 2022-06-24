from attr import has
from cell_extractor.Predictor import GreedyPredictor
import numpy as np
import xgboost as xgb
import matplotlib.pyplot as plt
class Detector():
    def __init__(self,model=None,predictor:GreedyPredictor=GreedyPredictor()):
        self.model = model
        self.predictor = predictor

    def createDM(self,df):
        labels=df['label']
        features=df.drop('label',axis=1)
        return xgb.DMatrix(features, label=labels)
    
    def calculate_scores(self,features):
        all=self.createDM(features)
        labels=all.get_label()
        scores=np.zeros([features.shape[0],len(self.model)])
        for i in range(len(self.model)):
            bst=self.model[i]
            scores[:,i] = bst.predict(all, iteration_range=[1,bst.best_ntree_limit], output_margin=True)
        mean=np.mean(scores,axis=1)
        std=np.std(scores,axis=1)
        return scores,labels,mean,std

    def get_prediction(self,mean,std):
        predictions=[]
        for mean,std in zip(mean,std):
            p=self.predictor.decision(float(mean),float(std))
            predictions.append(p)
        return np.array(predictions)
    
    def calculate_and_set_scores(self,df):
        if not hasattr(self,'mean') or hasattr(self,'std') or hasattr(self,'labels'):
            _,self.labels,self.mean,self.std = self.calculate_scores(df)

    def plot_score_scatter(self,df):
        self.calculate_and_set_scores(df)
        plt.figure(figsize=[15,10])
        plt.scatter(self.mean,self.std,c=self.labels,s=3)
        plt.title('mean and std of scores for 30 classifiers')
        plt.xlabel('mean')
        plt.ylabel('std')
        plt.grid()
    
    def plot_decision_scatter(self,features):
        self.calculate_and_set_scores(features)
        if not hasattr(self,'predictions'):
            self.predictions=self.get_prediction(self.mean,self.std)
        plt.figure(figsize=[15,10])
        plt.scatter(self.mean,self.std,c=self.predictions+self.labels,s=5)
        plt.title('mean and std of scores for 30 classifiers')
        plt.xlabel('mean')
        plt.ylabel('std')
        plt.grid()