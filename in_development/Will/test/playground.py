import cv2
from skimage import io
import numpy as np 
import PIL
import matplotlib.pyplot as plt

url = 'https://i.ebayimg.com/images/g/9hQAAOSwfVVgBFqU/s-l1600.jpg'

image = io.imread(url)
r,g,b = cv2.split(image)
image = cv2.merge([b,g,r])
image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
ret, thresh = cv2.threshold(image,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
# You need to choose 4 or 8 for connectivity type
connectivity = 4  
# Perform the operation
n_connected,segment_visual,stats,segment_location = cv2.connectedComponentsWithStats(thresh, connectivity, cv2.CV_32S)

big_seg = stats[:,-1]>1000
big_seg_id = np.where(big_seg)[0]
stats,segment_location = stats[big_seg],segment_location[big_seg]
# plt.figure()
# plt.imshow(thresh,cmap='Greys')
# plt.show()

# plt.figure()
# plt.imshow(image,cmap='Greys')
# plt.show()


plt.figure(figsize=[10,60])
for i in range(sum(big_seg)): 
    nrow = 2
    ncol = 6
    plt.subplot(ncol,nrow,i+1)
    plt.imshow(segment_visual==big_seg_id[i])
    plt.scatter(segment_location[i,0], segment_location[i,1])
plt.show()