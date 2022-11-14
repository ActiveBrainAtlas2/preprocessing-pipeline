import cv2
section = 180
dir=f'/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55/CH3/{section}/'
img = np.float32(cv2.imread(dir+'180tile-4.tif', -1))