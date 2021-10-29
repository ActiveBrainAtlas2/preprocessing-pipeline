import sys
import numpy as np
import pickle as pkl
import compute_image_features 
import cv2
import pandas as pd
from CellDetectorBase import CellDetectorBase

class FeatureFinder(CellDetectorBase):
    def __init__(self,animal,section):
        super().__init__(animal,section)
        print('DATA_DIR=%s'%(self.CH3))

    
    def main(self):
        self.load_examples()
        thresh=2000
        for tilei in range(len(self.Examples)):
            average_image = self.calculate_average_cell_images(self.Examples[tilei])
            for example in self.Examples[tilei]:
                image = example['image_CH3']
                self.features={}
                for key in ['animal','section','index','label','area','height','width']:
                    self.features[key] = example[key]
                self.features['row'] = example['row']+example['origin'][0]
                self.features['col'] = example['col']+example['origin'][1]
                if image.size == 0:
                    breakpoint()
                corr,energy = compute_image_features.calc_img_features(image,average_image)
                self.features['corr'] = corr
                self.features['energy'] = energy

                Stats=cv2.connectedComponentsWithStats(np.int8(image>thresh))
                if Stats[1] is None:
                    continue
                seg=Stats[1]

                # Isolate the connected component at the middle of seg
                middle=np.array(np.array(seg.shape)/2,dtype=np.int16)
                middle_seg=seg[middle[0],middle[1]]
                middle_seg_mask = np.uint8(seg==middle_seg)

                # Calculate Moments
                moments = cv2.moments(middle_seg_mask)
                self.features.update(moments)
                # Calculate Hu Moments
                huMoments = cv2.HuMoments(moments)
                self.features.update({'h%d'%i:huMoments[i,0]  for i in range(7)})


    def calculate_average_cell_images(self,examples):
        images = []
        for examplei in examples:
            images.append(examplei['image_CH3'])
        images = np.stack(images)
        average = np.average(images,axis=0)
        average = (average - average.mean())/average.std()
        return average

    def save_features(self):
        df_dict=None
        for i in range(len(self.Examples)):
            if df_dict==None:
                df_dict={}
                for key in self.features:
                    df_dict[key]=[]
            for key in self.features:
                df_dict[key].append(self.features[key])
        df=pd.DataFrame(df_dict)
        outfile=self.get_feature_save_path()
        print('df shape=',df.shape,'output_file=',outfile)
        df.to_csv(outfile,index=False)

if __name__ == '__main__':
    animal = 'DK55'
    finder = FeatureFinder(animal,1)
    sections_with_csv = finder.get_sections_with_csv()
    for sectioni in sections_with_csv:
        print(f'processing section {sectioni}')
        finder = FeatureFinder(animal,sectioni)
        finder.main()
        finder.save_features()