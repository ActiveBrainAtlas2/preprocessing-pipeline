import numpy as np
from skimage import io
import os
import pandas as pd
import cv2
from subprocess import Popen

HOME = os.path.expanduser("~")
animal = 'DK39'
DIR = f'/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{animal}'
INPUT = os.path.join(DIR, 'preps', 'CH3', 'full_aligned')
dfpath = os.path.join(HOME, f'programming/brains/{animal}', f'{animal}.CH3.Premotor.csv')
df = pd.read_csv(dfpath)
df.drop(["Description"], inplace=True, axis=1)
print(df.head())

section = 156
premotor = df[(df["Layer"] == 'premotor') & (df["Section"] == section)]
print(premotor.head())
pts = premotor[['X','Y']].values / 1
points = pts.tolist()

file = f'{section}.tif' 
infile = os.path.join(INPUT, file)

OUTPUT = f'{HOME}/programming/brains/{animal}/CH3'
os.makedirs(OUTPUT, exist_ok=True)
outpath =  os.path.join(OUTPUT, f'{section}.points.tif')

cmd = f'convert {infile} -fill transparent -stroke yellow'  
for point in points:
    endcircle = point[0] + (20*5)
    cmd += f' -draw "circle {point[0]},{point[1]},{endcircle},{point[1]}" '
cmd += f' {outpath}'

proc = Popen(cmd, shell=True)
proc.wait()
print(cmd)
chop = 55800//2

cmd = f'convert {outpath} -gravity West -chop {chop}x0 {outpath}' 
proc = Popen(cmd, shell=True)
proc.wait()
print(cmd)

cmd = f'convert {outpath} -resize 10% -normalize -auto-level -compress lzw {outpath}' 
proc = Popen(cmd, shell=True)
proc.wait()
print(cmd)