import sys
import cv2
import pandas as pd
import numpy as np
import os
import cv2
from numpy.linalg import norm
from time import time
import glob
from Brain import Brain
import pickle as pkl

class SampleExtractor(Brain):
    def __init__(self,animal,section):
        super().__init__(animal)
        self.t0=time()
        self.section=section
        self.DATA_DIR = f"/data/cell_segmentation/{self.animal}/CH3/"
        self.SECTION_DIR=os.path.join(self.DATA_DIR,f"{self.section:03}")
        print('section=%d, SECTION_DIR=%s'%(self.section,self.SECTION_DIR))
        self.thresh=2000
        self.cell_index = 0
        self.Examples=[]
        self.Stats_list=[]
        self.diff_list=[]
    
    def get_sections_with_csv(self):
        sections = os.listdir(self.DATA_DIR)
        sections_with_csv = []
        for sectioni in sections:
            if glob.glob(os.path.join(self.DATA_DIR,sectioni,f'*.csv')):
                sections_with_csv.append(int(sectioni))
        return sections_with_csv

    def load_manual_annotation(self):
        dfpath = glob.glob(os.path.join(self.SECTION_DIR, f'*{self.section}*.csv'))[0]
        self.manual_annotation = pd.read_csv(dfpath)
        
    def get_tile_and_image_dimensions(self):
        self.width,self.height = self.get_image_dimension()
        self.tile_height = int(self.height / 5)
        self.tile_width=int(self.width/2)

    def get_tile_origins(self):
        print('width=%d, tile_width=%d ,height=%d, tile_height=%d'
        %(self.width, self.tile_width,self.height,self.tile_height))
        self.tile_origins={}
        for i in range(10):
            row=int(i/2)
            col=i%2
            self.tile_origins[i] = (row*self.tile_height,col*self.tile_width)
        print('origins=',self.tile_origins)

    def collect_examples(self,labels,pos_locations,Stats,img,min_size=int(100/2),origin=[0,0]):
        Examples=[]
        for labeli in range(len(labels)):
            _,_,width,height,area = Stats[2][labeli,:]
            if area>100000:  # ignore the background segment
                continue
            col,row= Stats[3][labeli,:] #get coordinates of center points
            height2=max(2*height,min_size)  # calculates size of image to extract
            width2=max(2*width,min_size)
            example={'animal':animal,
                    'section':self.section,
                    'index':self.cell_index,
                    'label':int(labels[labeli]),
                    'area':area,
                    'row':row,
                    'col':col,
                    'origin':origin,
                    'height':height,
                    'width':width,
                    'image':img[int(row-height2):int(row+height2),int(col-width2):int(col+width2)]
                    }
            self.cell_index+=1
            Examples.append(example)
        return Examples

    def get_tilei(self,tilei):
        file = f'{self.section:03}tile-{tilei}.tif'
        infile = os.path.join(self.SECTION_DIR, file)
        img = np.float32(cv2.imread(infile, -1))
        print('tile=',tilei,end=',')
        return img
    
    def subtract_blurred_image(self,image):
        small=cv2.resize(image,(0,0),fx=0.05,fy=0.05, interpolation=cv2.INTER_AREA)
        blurred=cv2.GaussianBlur(small,ksize=(21,21),sigmaX=10)
        relarge=cv2.resize(blurred,(0,0),fx=20,fy=20) #,interpolation=cv2.INTER_AREA)
        difference=image-relarge
        return difference
    
    def get_tile_origin(self,tilei):
        return np.array(self.tile_origins[tilei],dtype=np.int32)
    
    def get_manual_labels_in_tilei(self,tilei):
        tile_origin= self.get_tile_origin(tilei)
        manual_labels=np.int32(self.manual_annotation[['y','x']])-tile_origin   
        manual_labels_in_tile=[]
        for i in range(manual_labels.shape[0]):
            row,col=list(manual_labels[i,:])
            if row<0 or row>=self.tile_height or col<0 or col>=self.tile_width:
                continue
            manual_labels_in_tile.append(np.array([row,col]))
        if not manual_labels_in_tile ==[]:
            manual_labels_in_tile=np.stack(manual_labels_in_tile)
        else:
            manual_labels_in_tile = np.array([])
        print('Manual Detections = %d'%len(manual_labels_in_tile))
        return manual_labels_in_tile
    
    def find_connected_segments(self,image):
        Stats=cv2.connectedComponentsWithStats(np.int8(image>self.thresh))
        print('Computer Detections=',Stats[0],end=',')
        segments_found = Stats[0]>2
        if not segments_found:
            print('skipping tile')
        return Stats,segments_found

    def find_examples(self):    
        self.load_manual_annotation()
        self.get_tile_and_image_dimensions()
        self.get_tile_origins()
        for tile in range(10):
            img = self.get_tilei(tile)
            difference = self.subtract_blurred_image(img)
            self.diff_list.append(difference)
            Stats,segments_found=self.find_connected_segments(difference)
            self.Stats_list.append(Stats)
            if not segments_found:
                continue
            manual_labels_in_tile = self.get_manual_labels_in_tilei(tile)
            nsegments = Stats[2].shape[0]
            segment_map = Stats[1]
            segment_labels=np.zeros(nsegments) 
            pos_locations=np.zeros([nsegments,2])
            nlabel = len(manual_labels_in_tile) 
            if  nlabel>0:   
                cell_candidate=np.int32(Stats[3])  
                cell_candidate = np.flip(cell_candidate,1)
                Dists=[]
                for labeli in range(nlabel):
                    distance_to_label=norm(cell_candidate-manual_labels_in_tile[labeli],axis=1)
                    row,col=manual_labels_in_tile[labeli]
                    cloest_segment=np.argmin(distance_to_label)  
                    segment_id=segment_map[row,col] 
                    segment_labels[segment_id]=1
                    pos_locations[segment_id,:]=[row,col]
                    if cloest_segment !=segment_id :
                        Dists.append((labeli,np.min(distance_to_label),segment_id,cloest_segment))
                print('tile=%d positives=%d, unmatched (size=%d):\n '%(tile,sum(segment_labels),len(Dists)),Dists)
            origin = self.get_tile_origin(tile)
            examples=self.collect_examples(segment_labels,pos_locations,Stats,difference,origin=origin)
            self.Examples.append((tile,examples))
        self.Examples=[examplei[1] for examplei in self.Examples]

    def save_examples(self):
        out={'Examples':self.Examples}
        print('about to write',time()-self.t0)
        t1=time()
        with open(self.SECTION_DIR+f'/extracted_cells_{self.section}.pkl','bw') as pkl_file:
            pkl.dump(out,pkl_file)
        print('finished writing ',time()-t1)

if __name__ == '__main__':
    animal = 'DK55'
    extractor = SampleExtractor(animal,1)
    sections_with_csv = extractor.get_sections_with_csv()
    for sectioni in sections_with_csv:
        print(f'processing section {sectioni}')
        extractor = SampleExtractor(animal,sectioni)
        extractor.find_examples()
        extractor.save_examples()