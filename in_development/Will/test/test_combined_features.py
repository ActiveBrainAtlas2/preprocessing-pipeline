from cell_extractor.retraining.create_new_features import create_combined_features
import pandas as pd
import numpy as np
df_og = create_combined_features()
df_og = df_og.drop(['label','animal'],axis=1)
dir = '/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55/all_features_modified.csv'
df = pd.read_csv(dir)
df = df.drop(['Unnamed: 0','Unnamed: 0.1','label','animal'],axis=1)
df = df.drop(df.tail(1).index)
ncol = len(df.columns)
length = len(df)
for i in range(length):
    ogi = df_og.iloc[i].to_numpy()
    dfi = df.iloc[i].to_numpy()
    for coli in range(ncol):
        if not np.isclose(ogi[coli],dfi[coli]):
            if not np.isnan(ogi[coli]) and np.isnan(dfi[coli]):
                print(i,coli)


print('done')