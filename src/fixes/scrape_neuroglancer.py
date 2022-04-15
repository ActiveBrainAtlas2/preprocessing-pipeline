import os, sys
import argparse
from pathlib import Path

PIPELINE_ROOT = Path('./src').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())
print(PIPELINE_ROOT.as_posix())
from lib.sqlcontroller import SqlController

#from lib.FileLocationManager import FileLocationManager



def fetch_animals_from_db():
    sqlController = SqlController('MD585')
    return sqlController.get_animal_list()
    


def parse_directories():
    DATA_ROOT = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data'
    animals = fetch_animals_from_db()
    for animal in animals:
        data_dir = os.path.join(DATA_ROOT, animal, 'neuroglancer_data')
        if os.path.exists(data_dir):
            for d in os.listdir(data_dir):
                print(animal, data_dir, d)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--debug', help='Enter debug True|False', required=False, default='false')

    args = parser.parse_args()
    debug = bool({'true': True, 'false': False}[str(args.debug).lower()])
    parse_directories()




                
        


