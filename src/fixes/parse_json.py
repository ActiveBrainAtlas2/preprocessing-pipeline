import argparse
import json
import os
import sys
import pandas as pd
from sqlalchemy.orm.exc import NoResultFound
from lib.sqlcontroller import SqlController
MANUAL=1
BETH=2
HOME = os.path.expanduser("~")
DIR = os.path.join(HOME, 'programming/pipeline_utility/src')
abbreviation='point'
sys.path.append(DIR)

def parse_layer(animal, id,debug):
    """
    Get the id from https://activebrainatlas.ucsd.edu/activebrainatlas/admin/neuroglancer/urlmodel/
    When you hover over the animal link, you can see the ID in the url, or just click on it.
    """
    sqlController = SqlController(animal)
    try:
        data = sqlController.get_urlModel(id)
    except NoResultFound as nrf:
        print('No results for {} error: {}'.format(animal, nrf))
        return
 
    json_txt = json.loads(data.url)
    layers = json_txt['layers']
    data = []
    for layer in layers:
        if 'annotations' in layer:
            name = layer['name']
            annotation = layer['annotations']
            # d = [row['point'] for row in annotation if 'point' in row]
            d = {row['description']:row['point'] for row in annotation if 'point' in row and 'description' in row}
            for row in annotation:
                if 'point' in row and 'description' in row:
                    description = str(row['description']).strip()
                else:
                    description = None
                x,y,z = row['point']
                data.append([name,description, x, y, int(round(z))])
            
    df = pd.DataFrame(data, columns=['layer','description','x','y','section'])
    positive = df[df.layer=='POSITIVE']
    negative = df[df.layer=='Negative']
    add_df_to_layer_data(animal,positive,sqlController,'positive',debug)
    add_df_to_layer_data(animal,negative,sqlController,'negative',debug)

def add_df_to_layer_data(animal,df,sqlController,layer,debug):
    for index, row in df.iterrows():
        x,y,z = sqlController.convert_coordinate_pixel_to_microns((row['x'],row['y'],row['section']))
        if debug:
            print('Add layer', animal, abbreviation, x, y, z, BETH, layer,MANUAL)
        else:
            print('Add layer', animal, abbreviation, x, y, z, BETH, layer,MANUAL)
            sqlController.add_layer_data(abbreviation, animal, layer, x, y, z, person_id=BETH, input_type_id=MANUAL)



if __name__ == '__main__':
    # parser = argparse.ArgumentParser(description='Work on Animal')
    # parser.add_argument('--animal', help='Enter animal', required=True)
    # parser.add_argument('--id', help='Enter primary key of URL JSON', required=False, default=0)
    # parser.add_argument('--debug', help='Enter true or false', required=False, default='true')
    # args = parser.parse_args()
    # debug = args.debug
    # animal = args.animal
    # id = int(args.id) 
    # parse_layer(animal, id,debug)

    parse_layer('DK55', 332,False)
