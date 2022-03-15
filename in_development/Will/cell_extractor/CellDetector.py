
import numpy as np
from numpy import *
import xgboost as xgb
import pandas as pd
from glob import glob
import pickle as pk
from  os.path import getsize # get the size of file. 
from cell_extractor.CellDetectorBase import CellDetectorBase

class CellDetector(CellDetectorBase):

    def __init__(self,animal,round = 2, *args, **kwargs):
        print('version of xgboost is:',xgb.__version__,'should be at least 1.5.0')
        super().__init__(animal,round=round,*args, **kwargs)
        self.detector = self.load_detector()
    
    def calculate_and_save_detection_results(self):
        features = self.get_combined_features()
        scores,labels,_mean,_std = self.detector.calculate_scores(features)
        predictions=self.get_prediction(_mean,_std)
        detection_df['mean_score'],detection_df['std_score'] = _mean,_std
        detection_df['label'] = labels
        detection_df['predictions'] = predictions
        detection_df=detection_df[predictions!=-2]
        detection_df = detection_df[['animal', 'section', 'row', 'col','label', 'mean_score','std_score', 'predictions']]
        detection_df.to_csv(self.DETECTION_RESULT_DIR,index=False)

if __name__ == '__main__':
    detector = CellDetector('DK52')
    detector.calculate_and_save_detection_results()