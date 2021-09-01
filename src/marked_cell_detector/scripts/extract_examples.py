import sys
import cv2
import pandas as pd
import numpy as np
import os
import cv2
from numpy.linalg import norm
from time import time

animal = 'DK55'

def collect_examples(labels,pos_locations,Stats,img,min_size=int(100/2),origin=[0,0]):
    global cell_index
    Examples=[]
    for j in range(len(labels)):
        _,_,width,height,area = Stats[2][j,:]
        if area>100000:  # ignore the background segment
            continue
        col,row= Stats[3][j,:] #get coordinates of center points
        height2=max(2*height,min_size)  # calculates size of image to extract
        width2=max(2*width,min_size)
        example={'animal':animal,
                 'section':section,
                 'index':cell_index,
                 'label':int(labels[j]),
                 'area':area,
                 'row':row,
                 'col':col,
                 'origin':origin,
                 'height':height,
                 'width':width,
                 'image':img[int(row-height2):int(row+height2),int(col-width2):int(col+width2)]
                }
        cell_index+=1
        Examples.append(example)
    return Examples

if __name__=='__main__':
    print(sys.argv)
    t0=time()
    section = int(sys.argv[1])
    DATA_DIR =sys.argv[2]
    #section=164
    #DATA_DIR="./data/%d/"%section
    print('section=%d, DATA_DIR=%s'%(section,DATA_DIR))


    dfpath = os.path.join(DATA_DIR, '%d.csv'%section)  # read manual COMs (=training data)
    df = pd.read_csv(dfpath)

    # in_row_min=5400; in_row_max=6800; in_col_min=8000; in_col_max=13000
    # parameters
    # the original images are width=60000, height=34000.
    #### Tile organzation
    # 5 rows (height/5), 2 columns (width/2)

    width = 60000
    height = 34000
    tile_height = int(height / 5)
    tile_width=int(width/2)
    radius = 400
    color = (2000)

    print('width=%d, tile_width=%d ,height=%d, tile_height=%d'%(width, tile_width,height,tile_height))
    origins={}
    for i in range(10):
        row=int(i/2)
        col=i%2
        origins[i] = (row*tile_height,col*tile_width)
    print('origins=',origins)

    # Main Loop

    E=[]
    Stats_list=[]
    diff_list=[]
    cell_index=0  # counter for cells across all tiles.
    
    for tile in range(10):

        file = 'tile-%d.tif'%tile
        infile = os.path.join(DATA_DIR, file)
        img = np.float32(cv2.imread(infile, -1))
        print('tile=',tile,end=',')

        small=cv2.resize(img,(0,0),fx=0.05,fy=0.05, interpolation=cv2.INTER_AREA)
        blur=cv2.GaussianBlur(small,ksize=(21,21),sigmaX=10)
        relarge=cv2.resize(blur,(0,0),fx=20,fy=20) #,interpolation=cv2.INTER_AREA)
        diff=img-relarge
        diff_list.append(diff)

        thresh=2000
        Stats=cv2.connectedComponentsWithStats(np.int8(diff>thresh))

        print('Computer Detections=',Stats[0],end=',')
        Stats_list.append(Stats)
        if Stats[0]<2:
            print('skipping tile')
            continue

        origin= np.array(origins[tile],dtype=np.int32)
        pos_coor=np.int32(df[['y','x']])-origin   #order if y then x (or row then col)

        L_pos_coor=[]
        for i in range(pos_coor.shape[0]):
            row,col=list(pos_coor[i,:])
            if row<0 or row>=tile_height or col<0 or col>=tile_width:
                continue
            L_pos_coor.append(np.array([row,col]))
        print('Manual Detections = %d'%len(L_pos_coor))

        labels=np.zeros(Stats[2].shape[0]) # true vs false label
        pos_locations=np.zeros([Stats[2].shape[0],2])
        if len(L_pos_coor) >0:   #if there are detections, associate them with segments to generate 1 labels
            pos_coor_tile=np.stack(L_pos_coor)  

            candid_coor=np.int32(Stats[3])   # Stats[3] gives the location of the center of each component in x,y order
            dummy=np.copy(candid_coor[:,0])
            candid_coor[:,0]=candid_coor[:,1]
            candid_coor[:,1]=dummy

            #compare closest to label on segmentation map
            Dists=[]
            for i in range(len(pos_coor_tile)):
                c=norm(candid_coor-pos_coor_tile[i],axis=1)
                row,col=pos_coor_tile[i]
                index1=np.argmin(c)  #the index of the closest manual COM
                index2=Stats[1][row,col] # the index of the connected component at row,col location
                labels[index2]=1
                pos_locations[index2,:]=[row,col]
                if index1 !=index2 :
                    Dists.append((i,np.min(c),index2,index1))
            print('tile=%d positives=%d, unmatched (size=%d):\n '%(tile,sum(labels),len(Dists)),Dists)

        examples=collect_examples(labels,pos_locations,Stats,diff,origin=origin)
        E.append((tile,examples))

    Examples=[]
    for i in range(len(E)):
        Examples+=E[i][1]

    out={'Examples':Examples
         #'diff_list': diff_list,
         #'Stats_list':Stats_list
        }
    print('about to write',time()-t0)
    t1=time()
    import pickle as pkl
    with open(DATA_DIR+'/extracted_cells.pkl','bw') as pkl_file:
        pkl.dump(out,pkl_file)
    print('finished writing ',time()-t1)
