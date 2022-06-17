from cell_extractor.Predictor import Predictor
import numpy as np
import xgboost as xgb
import matplotlib.pyplot as plt
class Detector():
    def __init__(self,model=None,predictor:Predictor=Predictor()):
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
        _mean=np.mean(scores,axis=1)
        _std=np.std(scores,axis=1)
        return scores,labels,_mean,_std

    def get_prediction(self,_mean,_std):
        predictions=[]
        for mean,std in zip(_mean,_std):
            p=self.predictor.decision(float(mean),float(std))
            predictions.append(p)
        return np.array(predictions)

    def plot_score_scatter(self,df):
        scores,labels,_mean,_std = self.calculate_scores(df)
        plt.figure(figsize=[15,10])
        plt.scatter(_mean,_std,c=labels,s=3)
        plt.title('mean and std of scores for 30 classifiers')
        plt.xlabel('mean')
        plt.ylabel('std')
        plt.grid()
    
    def plot_decision_scatter(self,features):
        scores,labels,_mean,_std = self.calculate_scores(features)
        predictions=self.get_prediction(_mean,_std)
        plt.figure(figsize=[15,10])
        plt.scatter(_mean,_std,c=predictions+labels,s=5)
        plt.title('mean and std of scores for 30 classifiers')
        plt.xlabel('mean')
        plt.ylabel('std')
        plt.grid()