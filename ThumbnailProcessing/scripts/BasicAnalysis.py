import os, sys
import pandas as pd
import pickle as pk
import cv2
import matplotlib
import matplotlib.figure
import numpy as np

def im_type(src):
    print('dtype=',src.dtype,'shape=',src.shape)

def disp(image):
    figure(figsize=[30,8])
    im_type(image)
    imshow(image.T,'gray');

def find_threshold(src):
    fig = matplotlib.figure.Figure()
    ax = matplotlib.axes.Axes(fig, (0,0,0,0))
    n,bins,patches=ax.hist(src.flatten(),160);
    del ax, fig
    min_point=np.argmin(n[:5])
    thresh=min_point*64000/160+1000
    return thresh

def find_main_blob(stats,image):
    height,width=image.shape
    df=pd.DataFrame(stats)
    df.columns=['Left','Top','Width','Height','Area']
    df['blob_label']=df.index
    df=df.sort_values(by='Area',ascending=False)

    for row in df.iterrows():
        Left=row[1]['Left']
        Top=row[1]['Top']
        Width=row[1]['Width']
        Height=row[1]['Height']
        corners= int(Left==0)+int(Top==0)+int(Width==width)+int(Height==height)
        if corners<=2:
            return row


def scale_and_mask(src,mask,epsilon=0.01):
    vals=np.array(sorted(src[mask>10]))
    ind=int(len(vals)*(1-epsilon))
    _max=vals[ind]
    # print('thr=%d, index=%d'%(vals[ind],index))
    _range=2**16-1
    scaled=src*(45000./_max)
    scaled[scaled>_range]=_range
    scaled=scaled*(mask>10)
    return scaled,_max

#thumbnail=sys.argv[1:]
DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK39'
INPUT = os.path.join(DIR, 'preps', 'normalized')
thumbnail = sorted(os.listdir(INPUT))
results=[]
for i in range(len(thumbnail)):

    print('\r %d/%d'%(i,len(thumbnail)),end='')
    ###### read image
    filepath = os.path.join(INPUT, thumbnail[i])
    src = cv2.imread(filepath,-1)
    threshold = find_threshold(src)

    ###### Threshold it so it becomes binary
    ret, threshed = cv2.threshold(src,threshold,255,cv2.THRESH_BINARY)
    threshed=np.uint8(threshed)

    ###### Find connected elements
    # You need to choose 4 or 8 for connectivity type
    connectivity = 4
    output = cv2.connectedComponentsWithStats(threshed, connectivity, cv2.CV_32S)

    # Get the results
    # The first cell is the number of labels
    num_labels = output[0]
    # The second cell is the label matrix
    labels = output[1]
    # The third cell is the stat matrix
    stats = output[2]
    # The fourth cell is the centroid matrix
    centroids = output[3]

    # Find the blob that corresponds to the section.
    row=find_main_blob(stats,src)
    blob_label=row[1]['blob_label']

    #extract the blob
    blob=np.uint8(labels==blob_label)*255

    #Perform morphological closing
    kernel10 = np.ones((10,10),np.uint8)
    closing = cv2.morphologyEx(blob, cv2.MORPH_CLOSE, kernel10, iterations=5)
    # scale and mask
    scaled,_max=scale_and_mask(src,closing)

    # Create Viewable image:
    combined=np.copy(scaled)
    combined[closing<10]=20000
    result={'index':i,
           'file':thumbnail[i],
           'src':src,
           'threshold':threshold,
           'blob':blob,
           'mask':closing,
           'scaled':scaled,
           'percentile99':_max,
           'combined':combined}
    results.append(result)

with open('auto_masking_results.pkl','wb') as pickle_file:
    pk.dump(results, pickle_file, pk.HIGHEST_PROTOCOL)
