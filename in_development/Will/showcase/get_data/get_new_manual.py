from lib.UrlGenerator import UrlGenerator
from abakit.lib.Controllers.SqlController import SqlController
from Will.toolbox.tmp.LoadCom import ComLoader
import pickle
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import glob
controller = SqlController('DK52')
class ManualVSAffineAtlasCOM(LoadCom):

    def load_detected_com(self):
        path = '/home/zhw272/Downloads/'
        pattern = '*_correct_coms.pkl'
        files = glob.glob(path+pattern)
        self.detected = {}
        for filei in files:
            animal_string_start = filei.index('DK')
            animali = filei[animal_string_start:animal_string_start+4]
            coms = pickle.load(open(filei,'rb'))
            comskeys = list(coms.keys())
            comvals = list(coms.values())
            comvals = [np.array(vali)*np.array([0.325,0.325,20]) for vali in comvals]
            self.detected[animali] = dict(zip(comskeys,comvals))

    def load_data(self):
        path = '/home/zhw272/Downloads/AtlasCOMsStack.pkl'
        file = open(path,'rb')
        self.aligned_atlas_coms  = pickle.load(file)
        self.animals = list(self.aligned_atlas_coms .keys())
        self.new_coms = {}
        self.stats = {}
        self.all_coms = {}
        for animali in self.animals:
            self.new_coms[animali] = controller.get_layer_data_entry(prep_id = animali,layer = 'COM_addition')
        self.coms = {}
        for animali in self.animals:
            self.coms[animali] = controller.get_com_dict(prep_id = animali)
            self.all_coms[animali] = self.coms[animali]
            self.all_coms[animali].update(self.new_coms[animali])
        print('done')
    
    def set_distance_field(self,com1,com2):
        distance = {}
        distance_xyz = {}
        for animali in self.animals:
            comi1 = com1[animali]
            comi2 = com2[animali]
            if comi2 != {}:
                dist_xyz = np.array([comi2[structurei]-comi1[structurei] for structurei in comi2])
                dist = np.sqrt(np.power(dist_xyz,2).sum(1))
                distance[animali] = dict(zip(comi2.keys(),dist))
                distance_xyz[animali] = dict(zip(comi2.keys(),np.abs(dist_xyz)))
        return distance, distance_xyz
    
    def set_distance_field_kui(self,com1,com2):
        distance = {}
        distance_xyz = {}
        for animali in self.animals:
            comi1 = com1[animali]
            comi2 = com2[animali]
            print(animali)
            if comi2 != {}:
                dist_xyz = np.array([comi2[structurei]-comi1[structurei] for structurei in comi2])
                dist = np.sqrt(np.power(dist_xyz,2).sum(1))
                distance[animali] = dict(zip(comi2.keys(),dist))
                distance_xyz[animali] = dict(zip(comi2.keys(),dist_xyz))
        return distance, distance_xyz

    def find_distance(self):
        a1 = self.aligned_atlas_coms
        a2 = self.new_coms
        a2k = self.detected
        a1['DK63'] = {}
        a2['DK63'] = {}
        a2k['DK63'] = {}
        self.distance,self.distance_xyz = self.set_distance_field_kui(a1,a2)
        self.distance_og,self.distance_xyz_og = self.set_distance_field_kui(a1,a2k)
        self.distance_og,self.distance_xyz_og_abs = self.set_distance_field(a1,a2k)

    def save_csv(self):
        df = {}
        df['animal'] = []
        df['structure'] = []
        df['distance'] = []
        for animal, dict in self.distance.items():
            for structure, dist in dict.items():
                df['animal'].append(animal)
                df['structure'].append(structure) 
                df['distance'].append(dist)
        df = pd.DataFrame(df)
        df.to_csv('~/Desktop/manual_com_to_affine_transformed_atlas_com_distance.csv')

    def plot_data(self):
        plot_data = [[valuei for valuei in animali.values()] for animali in self.distance.values()]
        fig, ax = plt.subplots()
        plt.boxplot(plot_data)
        ax.set_xticklabels(self.distance.keys())
        print('done')
    
    def find_dist(self,np_array):
        return np.sqrt(np.sum(np.power(np_array,2)))
    
    def yoavs_csv(self,input_data,title):
        fields = {  'x':lambda dist_xyz:[pi[0] for pi in dist_xyz],
            'y':lambda dist_xyz:[pi[1] for pi in dist_xyz],
            'z':lambda dist_xyz:[pi[2] for pi in dist_xyz],
            'dist':lambda dist_xyz:[self.find_dist(pi) for pi in dist_xyz]}
        df = {}
        df['structure'] = []
        for fieldi in fields:
            df[fieldi + '_mean'] = []
            df[fieldi + '_std'] = []
            df[fieldi + '_%<50'] = []
            df[fieldi + '_%50-100'] = [] 
            df[fieldi + '_%>100'] = []
        for structurei,dist_xyz in input_data.items():
            df['structure'].append(structurei)
            for fieldi, field_function in fields.items():
                values = np.array(field_function(dist_xyz))
                df[fieldi + '_mean'].append(np.around(np.mean(values),2))
                df[fieldi + '_std'].append(np.around(np.std(values),2))
                df[fieldi + '_%<50'].append(np.around(np.sum(values<50)/len(values)*100))
                df[fieldi + '_%50-100'].append(np.around(np.sum(np.logical_and(values>50,values<100))/len(values)*100))
                df[fieldi + '_%>100'].append(np.around(np.sum(values>100)/len(values)*100))
        df = pd.DataFrame(df)
        df.to_csv('~/Desktop/'+title+'.csv')

    def get_dist_per_structure(self,distance_field):
        distance = getattr(self, distance_field)
        structures = []
        for animal, dict in distance.items():
            for structure, _ in dict.items():
                structures.append(structure)
        result = {}
        for structurei in structures:
            result[structurei] = []
            for animal, dict in distance.items():
                for structure, dist_xyz in dict.items():
                    if structure ==structurei:
                        result[structurei].append(dist_xyz)
        return result

    def yoavs_recipe(self):
        self.xyz_per_structure = self.get_dist_per_structure('distance_xyz')
        self.xyz_per_structure_og = self.get_dist_per_structure('distance_xyz_og')
        self.xyz_per_structure_og_abs = self.get_dist_per_structure('distance_xyz_og_abs')
        self.yoavs_csv(self.xyz_per_structure,title = 'manual_com_to_affine_transformed_atlas_com_distance_stat')
        self.yoavs_csv(self.xyz_per_structure_og,title = 'recreating_kui')
        self.yoavs_csv(self.xyz_per_structure_og_abs,title = 'recreating_kui_abs')

if __name__ =='__main__':
    ana = ManualVSAffineAtlasCOM()
    ana.load_detected_com()
    ana.load_data()
    ana.find_distance()
    ana.yoavs_recipe()
    # ana.save_csv()




