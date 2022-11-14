from cell_extractor.CellDetectorBase import CellDetectorBase
import os
import pickle
import pandas as pd

animal = 'DK55'
section = 180
base = CellDetectorBase(animal)
dir=f'/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55/CH3/{section}/'
manual = np.loadcsv()
pd.read_csv(dir+'DK55_premotor_180_2021-10-18.csv')
examples = pickle.load(open(dir+'extracted_cells_180.pkl','rb'))

os.listdir(dir)