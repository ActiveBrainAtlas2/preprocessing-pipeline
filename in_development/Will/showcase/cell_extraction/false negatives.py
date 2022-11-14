import cv2
import pickle as pk
from collections import Counter
import numpy as np
from cell_extractor.CellDetectorBase import CellDetectorBase
from cell_extractor.ExampleFinder import ExampleFinder
import matplotlib.pyplot as plt
from skimage.transform import downscale_local_mean
import os

def find_examples_next_to_false_negative_points():
    memory={}
    corresponding_example=[]
    i=0
    distances = []
    for celli in false_negative:
        i+=1
        point=np.array([[celli[1]['y'],celli[1]['x']]])
        section=int(celli[1]['section'])

        if section in memory:
            connected_segment_center=memory[section]
        else:
            section_example_file= dir+'/CH3/%s/extracted_cells_%s.pkl'%(section,section)
            section_examples=pk.load(open(section_example_file,'rb'))['Examples']
            section_examples=[ei for layeri in section_examples for ei in layeri]
            connected_segment_center=[]
            for example in section_examples:
                origin_row,origin_col = example['origin']
                row=example['row']+origin_row
                col=example['col']+origin_col
                connected_segment_center.append((row,col))
            connected_segment_center=np.stack(connected_segment_center)
            memory[section]=connected_segment_center
        distance=np.sqrt(np.sum(np.square(connected_segment_center-point),axis=1))
        closest=np.argmin(distance)
        distances.append(distance[closest])
        closest_example=section_examples[closest]
        corresponding_example.append({'point':point,
                    'section' : section,
                    'distance':distance[closest],
                    'details':closest_example})
    return corresponding_example

def plotting():
    plt.figure()
    plt.imshow(map,origin='lower')
    plt.scatter(example_coord_sectioni[:,1],example_coord_sectioni[:,0],s=3,c='r')
    plt.xlim([6000,10000])
    plt.ylim([3000,6500])
    for i, _ in enumerate(example_coord_sectioni):
        plt.text(example_coord_sectioni[i,1], example_coord_sectioni[i,0],f'{i}')
    plt.show()

    plt.figure()
    plt.imshow(map,origin='lower')
    plt.scatter(example_coord_sectioni[:,1],example_coord_sectioni[:,0],s=3,c='r')
    plt.xlim([6000,10000])
    plt.ylim([3000,6500])
    for i, _ in enumerate(manual_coord_sectioni_tilei):
        plt.text(manual_coord_sectioni_tilei[i,1], manual_coord_sectioni_tilei[i,0],f'{i}')
    plt.show()

    tile5of174_ds = downscale_local_mean(tilei_of_sectioni, (5, 5,1))
    map_ds = downscale_local_mean(map, (5, 5))

    plt.figure()
    plt.imshow(map_ds,origin='lower')
    plt.scatter(example_coord_sectioni[:,1]/5,example_coord_sectioni[:,0]/5,s=3,c='r')
    plt.xlim([6000/5,10000/5])
    plt.ylim([3000/5,6500/5])
    for i, _ in enumerate(example_coord_sectioni):
        plt.text(example_coord_sectioni[i,1]/5, example_coord_sectioni[i,0]/5,f'{i}')
    plt.show()

    plt.figure()
    plt.imshow(tile5of174_ds.astype(np.uint8),origin='lower')
    plt.scatter(manual_coord_sectioni_tilei[:,1]/5,manual_coord_sectioni_tilei[:,0]/5,s=3)
    plt.xlim([5000/5,12000/5])
    plt.ylim([3000/5,6500/5])
    plt.show()

    plt.figure()
    plt.imshow(tilei_of_sectioni.astype(np.uint8),origin='lower')
    plt.scatter(manual_coord_sectioni_tilei[:,1]/5,manual_coord_sectioni_tilei[:,0]/5,s=3)
    plt.xlim([5000,12000])
    plt.ylim([3000,6500])
    plt.show()

    plt.figure(figsize=[50,60])
    for i in range(len(corresponding_example_sectioni)):
        plt.subplot(5,10,2*i+1)
        plt.imshow(corresponding_example_sectioni[i]['details']['image_CH1'],cmap='gray')
        plt.subplot(5,10,2*i+2)
        plt.imshow(corresponding_example_sectioni[i]['details']['image_CH3'],cmap='gray')

dir='/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55'
false_negative=pk.load(open(os.path.abspath(os.path.dirname(__file__)+'/../../yoav/'+
    'marked_cell_detector/notebooks/computerMissed.pkl'),'rb'))

corresponding_example = find_examples_next_to_false_negative_points()
sections = np.unique([mi['section'] for mi in corresponding_example])

base = CellDetectorBase('DK55',disk = 'net/birdstore/Active_Atlas_Data')
for sectioni in sections:
    false_negative_sectioni = [mi for mi in false_negative if mi[1]['section']==sectioni]
    coord_sectioni = np.array([[mi[1]['y'],mi[1]['x']] for mi in false_negative_sectioni])
    corresponding_example_sectioni = [mi for mi in corresponding_example \
            if mi['section']==sectioni]
    example_coord_sectioni = []
    for examplei in corresponding_example_sectioni:
        examplei = examplei['details']
        origin = examplei['origin']
        point = np.array([examplei['row'],examplei['col']])
        point = point + origin
        example_coord_sectioni.append(point)

    for tilei in range(10):
        manual_coord_sectioni_tilei,_ = base.get_manual_annotation_in_tilei(coord_sectioni,tilei)
        example_coord_sectioni_tilei,_ = base.get_manual_annotation_in_tilei(example_coord_sectioni,tilei)
        if len(manual_coord_sectioni_tilei) == 0 :
            continue

        finder = ExampleFinder('DK55',sectioni,disk = 'net/birdstore/Active_Atlas_Data')
        finder.load_and_preprocess_image(tilei)
        finder.find_connected_segments(finder.difference_ch3)
        ncell,map,stats,location = finder.connected_segment_info
        tilei_of_sectioni = cv2.imread(base.CH3+f'/{sectioni:03}/{sectioni:03}tile-{tilei}.tif')
        # origin = finder.tile_origins[tilei]
        # location = (location-origin).astype(int)
        assert(len(manual_coord_sectioni_tilei) == len(example_coord_sectioni_tilei)) 
        npoints = len(example_coord_sectioni)
        for pointi in range(npoints):
            manual_coord = manual_coord_sectioni_tilei[pointi]
            section_coord = example_coord_sectioni_tilei[pointi]
            location
        map
        tilei_of_sectioni
        example_coord_sectioni
        manual_coord_sectioni_tilei


