import os, sys
import argparse
from pathlib import Path

PIPELINE_ROOT = Path('./src').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())
print(PIPELINE_ROOT.as_posix())
from pipeline.lib.sqlcontroller import SqlController
from model.neuroglancer_data import AvailableNeuroglancerData
#from pipeline.lib.FileLocationManager import FileLocationManager
from datetime import datetime



def fetch_animals_from_db():
    sqlController = SqlController('MD585')
    return sqlController.get_animal_list()
    


def parse_directories():
    sqlController = SqlController('MD585')
    DATA_ROOT = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data'
    animals = fetch_animals_from_db()
    now = datetime.now()

    for animal in animals:
        data_dir = os.path.join(DATA_ROOT, animal, 'neuroglancer_data')
        if os.path.exists(data_dir):
            for description in os.listdir(data_dir):
                url = f'https://activebrainatlas.ucsd.edu/data/{animal}/neuroglancer_data/{description}'
                print(animal,  url, description)
                data = AvailableNeuroglancerData(prep_id=animal, url=url, description=description, active=1, 
                    created=now)
                sqlController.add_row(data)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--debug', help='Enter debug True|False', required=False, default='false')

    args = parser.parse_args()
    debug = bool({'true': True, 'false': False}[str(args.debug).lower()])
    parse_directories()




                
        


