import pandas as pd
from pipeline.Controllers.SqlController import SqlController
import numpy as np

class DataLoader:
    def __init__(self):
        path = '/home/zhw272/Downloads/Grand Atlas Pipeline Log - In-Vivo.csv'
        self.animal_log = pd.read_csv(path,header=[1])
        self.IDs = np.array(self.animal_log.iloc[:,1].to_list())
        self.goals = self.animal_log.Goal
        self.controller = SqlController('Atlas')
        self.premotors = self.animal_log[self.animal_in_database_and_premotor()]

    def animal_in_database(self):
        return [self.controller.animal_exists(id) for id in self.IDs]
    
    def premotor_tracings(self):
        premotor = []
        for goali in self.goals:
            if isinstance(goali,str):
                premotor.append('premotor' in goali.lower())
            else:
                premotor.append(False)
        return np.array(premotor)
    
    def animal_in_database_and_premotor(self):
        return np.logical_and(self.animal_in_database(),self.premotor_tracings())

if __name__ == '__main__':
    loader = DataLoader()
    loader.premotors.head()
    for _,row in loader.premotors.iterrows():
        print(row['Mouse ID'],row['Goal'])