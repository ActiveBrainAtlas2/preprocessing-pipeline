import pickle as pkl
import cv2
import numpy as np

with open('mean.pkl','br') as pkl_file:
    stat=pkl.load(pkl_file) 

mean_s=stat['Mean']

def sobel(img):
    sobel_x = cv2.Sobel(img,cv2.CV_64F,1,0,ksize=5)
    sobel_y = cv2.Sobel(img,cv2.CV_64F,0,1,ksize=5)
    _mean=(np.mean(sobel_x)+np.mean(sobel_y))/2.
    _std=np.sqrt((np.var(sobel_x)+np.var(sobel_y))/2)
    sobel_x=(sobel_x - _mean)/_std
    sobel_y=(sobel_y - _mean)/_std
    return sobel_x, sobel_y
def trim(a,s0,s1):
    if(a.shape[0]>s0):
        d=int((a.shape[0]-s0)/2)
        a=a[d:d+s0,:]
    if(a.shape[1]>s1):
        d=int((a.shape[1]-s1)/2)
        a=a[:,d:d+s1]
    return a
def equalize_size(a,b):
    s0=min(a.shape[0],b.shape[0])
    s1=min(a.shape[1],b.shape[1])
    a=trim(a,s0,s1)
    b=trim(b,s0,s1)
    return a,b
def calc_img_features(img):
    img,mean=equalize_size(img,mean_s)
    mean_x,mean_y=sobel(mean)
    img_x,img_y=sobel(img)
    
    dot_prod = (mean_x*img_x)+(mean_y*img_y)
    corr=np.mean(dot_prod.flatten())
    
    mag=np.sqrt(img_x*img_x + img_y*img_y)
    energy=np.mean((mag*mean).flatten())
    return corr,energy
