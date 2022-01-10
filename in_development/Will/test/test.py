import cv2
import pickle as pk
from collections import Counter
import numpy as np
dir='/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55'
missed=pk.load(open('preprocessing-pipeline/in_development/yoav/marked_cell_detector/notebooks/computerMissed.pkl','rb'))
extracted={}
misses=[]
i=0
m = missed[0]
x=m[1]['x']; y=m[1]['y']
point=np.array([[x,y]])
section=int(m[1]['section'])
if section in extracted:
    locs=extracted[section]
else:
    extracted_file= dir+'/CH3/%s/extracted_cells_%s.pkl'%(section,section)
    ext=pk.load(open(extracted_file,'rb'))
    all_examples=[]
    for example in ext['Examples']:
        all_examples+=example
    locs=[]
    for example in all_examples:
        origin_row,origin_col = example['origin']
        row=example['row']+origin_row
        col=example['col']+origin_col
        locs.append((col,row))
    locs=stack(locs)
    extracted[section]=locs 
diff=locs-point
dist=sqrt(sum(diff*diff,axis=1))
closest=argmin(dist)
print(dist[closest])
ex=all_examples[closest]
misses.append({'point':point,
                'distance':dist[closest],
                'details':ex})