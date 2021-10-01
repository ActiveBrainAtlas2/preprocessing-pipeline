import os, sys
#import pandas as pd
from collections import defaultdict
from subprocess import Popen
import argparse
import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform
HOME = os.path.expanduser("~")

HOME = os.path.expanduser("~")
DIR = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(DIR)

from lib.file_location import FileLocationManager
from model.layer_data import LayerData
from lib.sql_setup import session
SCALE = 10000/325.0


def create_points(animal, debug=False):
    CSV_DIR_PATH = f'/net/birdstore/Active_Atlas_Data/data_root/atlas_data/{animal}'
    csvfile = 'premotor.csv'

    csvpath = os.path.join(CSV_DIR_PATH, csvfile)
    print(csvpath)

    df = pd.read_csv(csvpath, header=None, names=['section', 'x', 'y'])   

    fileLocationManager = FileLocationManager(animal)
    samik = 'samik_xy'
    INPUT = os.path.join(fileLocationManager.prep, 'CH3', 'full')
    OUTPUT = os.path.join(fileLocationManager.prep, 'CH3', 'points', samik)
    os.makedirs(OUTPUT, exist_ok=True)
    sections = defaultdict(list)


    for index, row in df.iterrows():
        x = row['x']
        y = row['y']
        pts = [x,y]
        section = row['section']
        sections[section].append(pts)

    for section, points in sections.items():
        if debug:
            print(section, len(points))
            continue
        if len(points) < 2:
            print(f'Section {section} has less than 2 points')
            continue
        pts = np.array(points)
        means = np.mean(pts, axis=0)
        mean_x = means[0]
        mean_y = means[1]
        D = pdist(pts)
        D = squareform(D);
        max_distance, [I_row, I_col] = np.nanmax(D), np.unravel_index( np.argmax(D), D.shape )

        if debug:
            print(f'means for section {section} {means}, pts {pts}')


        file = str(section).zfill(3) + '.tif'
        infile = os.path.join(INPUT, file)

        if not os.path.exists(infile) and not debug:
            print(infile, 'does not exist')
            continue

        outpath =  os.path.join(OUTPUT, f'{section}.tif')

        if os.path.exists(outpath):
            print(outpath, 'exists')
            continue

        cmd = f'convert {infile} -normalize -auto-level {outpath}' 
        if debug:
            print(cmd)
        else:
            proc = Popen(cmd, shell=True)
            proc.wait()

        cmd = f'convert {outpath} -fill transparent -stroke yellow'  
        for point in points:
            endcircle = point[0] + (15*5)
            cmd += f' -draw "stroke-width 20 circle {point[0]},{point[1]},{endcircle},{point[1]}" '

        cmd += f' {outpath}'
        if debug:
            print(cmd)
        else:
            proc = Popen(cmd, shell=True)
            proc.wait()
        
        sizex = int(max_distance + 500)
        sizey = sizex
        offsetx = int(mean_x - max_distance/2)
        offsety = int(mean_y - max_distance/2)

        #cmd = f'convert {outpath} -gravity West -chop {chop}x0 {outpath}' 
        cmd = f'convert {outpath} -crop {sizex}x{sizey}+{offsetx}+{offsety} {outpath}' 
        if debug:
            print(cmd)
        else:
            proc = Popen(cmd, shell=True)
            proc.wait()

        pngfile = str(section).zfill(3) + '.png'
        pngpath = os.path.join(fileLocationManager.thumbnail_web, 'points', 'samik')
        os.makedirs(pngpath, exist_ok=True)
        png = os.path.join(pngpath, pngfile)
        cmd = f'convert {outpath} -resize 12% {png}' 
        if debug:
            print(cmd)
        else:
            proc = Popen(cmd, shell=True)
            proc.wait()
    if debug:
        print()
        print(sections)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--debug', help='Enter true or false', required=False, default='true')
    
 
    args = parser.parse_args()
    animal = args.animal
    debug = bool({'true': True, 'false': False}[str(args.debug).lower()])
    create_points(animal, debug)
