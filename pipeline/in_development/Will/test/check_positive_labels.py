import pickle
import numpy as np 
from cell_extractor.CellDetectorBase import CellDetectorBase
section = 180
animal = 'DK55'
base = CellDetectorBase(animal)
base.CH3 = '/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55/CH3/'
sections = base.get_sections_with_example()
sectioni = 180
print(sectioni)
dir=f'/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55/CH3/{section}/'
examples = pickle.load(open(dir+'extracted_cells_180.pkl','rb'))['Examples']
for ei in examples:
    ispos = [i['label']==1 for i in ei]
    npos = sum(ispos)
    print(len(ei))
    if len(ei)>157:
        print('label')
        print(ei[157]['label'])

labels = np.unique([i['label'] for ei in examples for i in ei])