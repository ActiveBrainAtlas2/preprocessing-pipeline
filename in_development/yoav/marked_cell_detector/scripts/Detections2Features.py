import sys
import numpy as np
import pickle as pkl
import compute_image_features 
import cv2

# if __name__=='__main__':
    # DATA_DIR =sys.argv[1]

DATA_DIR='/data/cell_segmentation/DK55/CH3/180'
print('DATA_DIR=%s'%(DATA_DIR))

with open(DATA_DIR+'/extracted_cells_180.pkl','br') as pkl_file:
    E=pkl.load(pkl_file)
    Examples=E['Examples']

df_dict=None
thresh=2000
for i in range(len(Examples[0])):
    e=Examples[0][i]

    img = e['image_CH3']

    #calc features based on connected components
    Stats=cv2.connectedComponentsWithStats(np.int8(img>thresh))

    if Stats[1] is None:
        continue

    features={}
    for key in ['animal','section','index','label','area','height','width']:
        features[key]=e[key]

    features['row']=e['row']+e['origin'][0]
    features['col']=e['col']+e['origin'][1]

    #calc gradient based features
    corr,energy=compute_image_features.calc_img_features(img)
    features['corr']=corr
    features['energy']=energy

    ####

    seg=Stats[1]

    # Isolate the connected component at the middle of seg
    middle=np.array(np.array(seg.shape)/2,dtype=np.int16)
    middle_seg=seg[middle[0],middle[1]]
    middle_seg_mask = np.uint8(seg==middle_seg)

    # Calculate Moments
    moments = cv2.moments(middle_seg_mask)
    # Calculate Hu Moments
    huMoments = cv2.HuMoments(moments)

    features.update({'h%d'%i:huMoments[i,0]  for i in range(7)})
    features.update(moments)

    
    if df_dict==None:
        df_dict={}
        for key in features:
            df_dict[key]=[]

    for key in features:
        df_dict[key].append(features[key])


import pandas as pd
df=pd.DataFrame(df_dict)
print('done')

dfpath = '/data/cell_segmentation/DK55/CH3/180/puntas_180.csv'
df1 = pd.read_csv(dfpath)

df = df.iloc[0]
df1 = df1.iloc[0]

for key in df.keys():
    # print((key,np.where([key in key1 for key1 in df1.keys()])))
    df1_key_bool = np.array([key in key1 for key1 in df1.keys()])
    df1_key = np.array(df1.keys())[df1_key_bool][0]
    # print((key,df1_key))
    if np.any(df1_key_bool):
        print((df[key],df1[df1_key]))

# outfile=DATA_DIR+'/puntas.csv'
# print('df shape=',df.shape,'output_file=',outfile)

# df.to_csv(outfile,index=False)
