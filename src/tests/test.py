# from lib.TiffSegmentor import TiffSegmentor
# segmentor = TiffSegmentor('DK60',disk = 'scratch',n_workers = 10)
# segmentor.generate_tiff_segments(channel = 1,create_csv = False)
# segmentor.generate_tiff_segments(channel = 3,create_csv = True)
#%%
dir = '/net/birdstore/Marissa/DK73'
files = ['DK73_slide083_2022_02_02_axion2.czi','DK73_TEST_Sectioning_Profile.cz','ScreenShot_Segmentation_Align_DK73_slide83.PNG']
file = dir+'/'+files[1]
czi_file = dir+'/'+files[0]
# %%
import xml.etree.ElementTree as ET
import numpy as np
from czifile import imread
from scipy import ndimage
#%%
tree = ET.parse(file)
root = tree.getroot()
# %%
for child in root[1][0][1][1]:
     print(child.tag, child.attrib)

# %%
root[1][0][1][0][1].text
# %%
polygons = {}
positions = []
for polyi in root[1]:
    polygon_id = polyi.attrib['Id']
    point_text = polyi[2][0].text.split(' ')
    points = []
    for point in point_text:
        point = point.split(',')
        point = [round(float(i)) for i in point]
        points.append(point)
    points = np.array(points)
    polygons[polygon_id]=points
    positions.append([round(float(i)) for i in polyi[1][1][4].text.split(',')])
positions = np.array(positions)

# %%
import matplotlib.pyplot as plt
points = list(polygons.values())[3]
plt.figure()
ax = plt.gca()
ax.set_aspect(1)
ax.scatter(points[:,0],points[:,1])
# %%
img = imread(czi_file)
# %%
imi = img[0,0,0,:,:,0]
# %%
imi_ds = ndimage.interpolation.zoom(imi,.1)
# %%
