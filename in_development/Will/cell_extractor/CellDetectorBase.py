import os
from time import time
from glob import glob
from atlas.lib.Brain import Brain
import pickle as pkl
import pandas as pd
import numpy as np
from cell_extractor.DetectionPlotter import DetectionPlotter
from cell_extractor.Predictor import Predictor

class CellDetectorBase(Brain):
    def __init__(self,animal='DK55',section = 0,disk = '/net/birdstore/Active_Atlas_Data/',round = 1,segmentation_threshold=2000,replace=False):
        self.attribute_functions = dict(
            tile_origins = self.get_tile_origins)
        super().__init__(animal)
        self.replace = replace
        self.disk = disk
        self.round = round
        self.plotter = DetectionPlotter()
        self.segmentation_threshold=segmentation_threshold
        self.ncol = 2
        self.nrow = 5
        self.section = section
        self.set_folder_paths()
        self.check_path_exists()
        self.get_tile_and_image_dimensions()
        self.get_tile_origins()
        self.check_tile_information()
        self.predictor = Predictor()
    
    def set_folder_paths(self):
        self.DATA_PATH = f"/{self.disk}/cell_segmentation/"
        self.ANIMAL_PATH = os.path.join(self.DATA_PATH,self.animal)
        self.DETECTOR = os.path.join(self.DATA_PATH,'detectors')
        self.FEATURE_PATH = os.path.join(self.ANIMAL_PATH,'features')
        self.DETECTION = os.path.join(self.ANIMAL_PATH,'detections')
        self.AVERAGE_CELL_IMAGE_DIR = os.path.join(self.ANIMAL_PATH,'average_cell_image.pkl')
        self.TILE_INFO_DIR = os.path.join(self.ANIMAL_PATH,'tile_info.csv')
        self.CH3 = os.path.join(self.ANIMAL_PATH,"CH3")
        self.CH1 = os.path.join(self.ANIMAL_PATH,"CH1")
        self.CH3_SECTION_DIR=os.path.join(self.CH3,f"{self.section:03}")
        self.CH1_SECTION_DIR=os.path.join(self.CH1,f"{self.section:03}")
        self.ALL_FEATURES = os.path.join(self.ANIMAL_PATH,'all_features.csv')
        self.QUALIFICATIONS = os.path.join(self.FEATURE_PATH,f'categories_round{self.round}.pkl')
        self.POSITIVE_LABELS = os.path.join(self.FEATURE_PATH,f'positive_labels_for_round_{self.round}_threshold_{self.segmentation_threshold}.pkl')
        self.DETECTOR_PATH = os.path.join(self.DETECTOR,f'detector_round_{self.round}_threshold_{self.segmentation_threshold}.pkl')
        self.DETECTION_RESULT_DIR = os.path.join(self.DETECTION,f'detections_{self.animal}.{str(self.round)}_threshold_{self.segmentation_threshold}.csv')
        self.ALL_FEATURES = os.path.join(self.FEATURE_PATH,f'all_features_threshold_{self.segmentation_threshold}.csv')

    def check_path_exists(self):
        check_paths = [self.ANIMAL_PATH,self.FEATURE_PATH,self.DETECTION,self.DETECTOR]
        for path in check_paths:
            os.makedirs(path,exist_ok = True)
    
    def get_tile_information(self):
        self.check_attributes(['tile_origins'])
        ntiles = len(self.tile_origins)
        tile_information = pd.DataFrame(columns = ['id','tile_origin','ncol','nrow','width','height'])
        for tilei in range(ntiles):
            tile_informationi = dict(
                id = tilei,
                tile_origin = self.tile_origins[tilei],
                ncol = self.ncol,
                nrow = self.nrow,
                width = self.width,
                height = self.height) 
            tile_information = tile_information.append(tile_informationi,ignore_index=True)
        return tile_information
    
    def save_tile_information(self):
        tile_information = self.get_tile_information()
        try:
            tile_information.to_csv(self.TILE_INFO_DIR,index = False)
        except IOError as e:
            print(e)
    
    def check_tile_information(self):
        if os.path.exists(self.TILE_INFO_DIR):
            tile_information = pd.read_csv(self.TILE_INFO_DIR)
            tile_information.tile_origin = tile_information.tile_origin.apply(eval)
            assert (tile_information == self.get_tile_information()).all().all()
        else:
            self.save_tile_information()
        
    def get_tile_and_image_dimensions(self):
        self.width,self.height = self.get_image_dimension()
        self.tile_height = int(self.height / self.nrow )
        self.tile_width=int(self.width/self.ncol )
    
    def get_tile_origins(self):
        self.check_attributes(['width'])
        self.tile_origins={}
        for i in range(self.nrow*self.ncol):
            row=int(i/self.ncol)
            col=i%self.ncol
            self.tile_origins[i] = (row*self.tile_height,col*self.tile_width)

    def get_tile_origin(self,tilei):
        self.check_attributes(['tile_origins'])
        return np.array(self.tile_origins[tilei],dtype=np.int32)
    
    def get_sections_with_string(self,search_string):
        sections = os.listdir(self.CH3)
        sections_with_string = []
        for sectioni in sections:
            if glob(os.path.join(self.CH3,sectioni,search_string)):
                sections_with_string.append(int(sectioni))
        return sorted(sections_with_string)

    def get_sections_without_string(self,search_string):
        sections = os.listdir(self.CH3)
        sections_with_string = []
        for sectioni in sections:
            if not glob(os.path.join(self.CH3,sectioni,search_string)):
                sections_with_string.append(int(sectioni))
        return sorted(sections_with_string)

    def get_sections_with_csv(self):
        return self.get_sections_with_string('*.csv')
    
    def get_sections_without_csv(self):
        return self.get_sections_without_string('*.csv')

    def get_sections_with_example(self,threshold=2000):
        return self.get_sections_with_string(f'extracted_cells*{threshold}*')

    def get_sections_without_example(self,threshold=2000):
        return self.get_sections_without_string(f'extracted_cells*{threshold}*')
    
    def get_sections_with_features(self,threshold=2000):
        return self.get_sections_with_string(f'puntas_*{threshold}*')

    def get_sections_without_features(self,threshold=2000):
        return self.get_sections_without_string(f'puntas_*{threshold}*')

    def get_example_save_path(self):
        return self.CH3_SECTION_DIR+f'/extracted_cells_{self.section}_threshold_{self.segmentation_threshold}.pkl'
    
    def get_feature_save_path(self):
        return self.CH3_SECTION_DIR+f'/puntas_{self.section}_threshold_{self.segmentation_threshold}.csv'
    
    def load_examples(self):
        save_path = self.get_example_save_path()
        try:
            with open(save_path,'br') as pkl_file:
                self.Examples=pkl.load(pkl_file)
        except IOError as e:
            print(e)
        
    def load_all_examples_in_brain(self,label = 1):
        sections = self.get_sections_with_csv()
        examples = []
        for sectioni in sections:
            base = CellDetectorBase(self.animal,sectioni)
            base.load_examples()
            examplei = [i for tilei in base.Examples for i in tilei if i['label'] == label]
            examples += examplei
        return examples
    
    def load_features(self):
        path=self.get_feature_save_path()
        try:
            self.features = pd.read_csv(path)
        except IOError as e:
            print(e)
    
    def save_features(self):
        df=pd.DataFrame()
        i = 0
        for featurei in self.features:
            df_dict = pd.DataFrame(featurei,index = [i])
            i+=1
            df=df.append(df_dict)
        outfile=self.get_feature_save_path()
        print('df shape=',df.shape,'output_file=',outfile)
        try:
            df.to_csv(outfile,index=False)
        except IOError as e:
            print(e)
    
    def save_examples(self):
        try:
            with open(self.get_example_save_path(),'wb') as pkl_file:
                pkl.dump(self.Examples,pkl_file)
        except IOError as e:
            print(e)

    def get_manual_annotation_in_tilei(self,annotations,tilei):
        tile_origin= self.get_tile_origin(tilei)
        manual_labels_in_tile=[]
        n_manual_label = 0
        if annotations is not None:  
            manual_labels=np.int32(annotations)-tile_origin   
            for i in range(manual_labels.shape[0]):
                row,col=list(manual_labels[i,:])
                if row<0 or row>=self.tile_height or col<0 or col>=self.tile_width:
                    continue
                manual_labels_in_tile.append(np.array([row,col]))
            if not manual_labels_in_tile ==[]:
                manual_labels_in_tile=np.stack(manual_labels_in_tile)
            else:
                manual_labels_in_tile = np.array([])
            n_manual_label = len(manual_labels_in_tile) 
        return manual_labels_in_tile,n_manual_label
    
    def get_combined_features_of_train_sections(self):
        dirs=glob(self.CH3 + f'/*/{self.animal}*.csv')
        dirs=['/'.join(d.split('/')[:-1]) for d in dirs]
        df_list=[]
        for dir in dirs:
            filename=glob(dir + '/puntas*{self.segmentation_threshold}*.csv')[0]
            df=pd.read_csv(filename)
            print(filename,df.shape)
            df_list.append(df)
        full_df=pd.concat(df_list)
        full_df.index=list(range(full_df.shape[0]))
        drops = ['animal', 'section', 'index', 'row', 'col'] 
        full_df=full_df.drop(drops,axis=1)
        return full_df
    
    def get_combined_features(self):
        if not os.path.exists(self.ALL_FEATURES):
            self.create_combined_features()
        return pd.read_csv(self.ALL_FEATURES,index_col=False)

    def get_combined_features_for_detection(self):
        all_features = self.get_combined_features()
        drops = ['animal', 'section', 'index', 'row', 'col'] 
        all_features=all_features.drop(drops,axis=1)
        return all_features
    
    def create_combined_features(self):
        print('creating combined features')
        files=glob(self.CH3+f'/*/punta*{self.segmentation_threshold}.csv')  
        df_list=[]
        for filei in files:
            if os.path.getsize(filei) == 1:
                continue
            df=pd.read_csv(filei)
            df_list.append(df)
        full_df=pd.concat(df_list)
        full_df.index=list(range(full_df.shape[0]))
        full_df.to_csv(self.ALL_FEATURES,index=False)

    def get_qualifications(self):
        return pkl.load(open(self.QUALIFICATIONS,'rb'))
    
    def save_detector(self,detector):
        pkl.dump(detector,open(self.DETECTOR_PATH,'wb'))
    
    def load_detector(self):
        detector = pkl.load(open(self.DETECTOR_PATH,'rb'))
        return detector
    
    def save_custom_features(self,features,file_name):
        path = os.path.join(self.FEATURE_PATH,f'{file_name}.pkl')
        pkl.dump(features,open(path,'wb'))
    
    def list_available_features(self):
        return os.listdir(self.FEATURE_PATH)
    
    def load_features(self,file_name):
        path = os.path.join(self.FEATURE_PATH,f'{file_name}.pkl')
        if os.path.exists(path):
            features = pkl.load(open(path,'rb'))
        else:
            print(file_name + ' do not exist')
        return features
    
    def load_average_cell_image(self):
        if os.path.exists(self.AVERAGE_CELL_IMAGE_DIR):
            try:
                average_image = pkl.load(open(self.AVERAGE_CELL_IMAGE_DIR,'rb'))
            except IOError as e:
                print(e)
            self.average_image_ch1 = average_image['CH1']
            self.average_image_ch3 = average_image['CH3']

def get_sections_with_annotation_for_animali(animal):
    base = CellDetectorBase(animal)
    return base.get_sections_with_csv()

def get_sections_without_annotation_for_animali(animal):
    base = CellDetectorBase(animal)
    return base.get_sections_without_csv()
