import os, sys
import torch
from torchtext.legacy import data
import pandas as pd
import numpy as np

# create Field objects
#image,id,tag,annotator,annotation_id
IMAGE = data.Field()
ID = data.Field()
TAG = data.Field()
ANNOTATOR = data.Field()
ANNOTATOR_ID = data.Field()

# create tuples representing the columns
fields = [
  ('image', IMAGE),
  ('id', ID),
  ('tag', TAG), # ignore age column
  ('annotator', ANNOTATOR),
  ('annotator_id', ANNOTATOR_ID)
]

# load the dataset in json format
train_ds, valid_ds, test_ds = data.TabularDataset.splits(
   path = 'data',
   train = 'train.tsv',
   validation = 'valid.tsv',
   test = 'test.tsv',
   format = 'tsv',
   fields = fields,
   skip_header = False
)

# check an example
#print(vars(train_ds[0]))

landmarks_frame = pd.read_csv('data/data.csv')
#print(landmarks_frame.head(1))

n = 1
img_name = landmarks_frame.iloc[n, 0]
landmarks = landmarks_frame.iloc[n, 1:]
print(type(landmarks))
sys.exit()
landmarks = np.asarray(landmarks)
landmarks = landmarks.astype('float').reshape(-1, 2)

#print('Image name: {}'.format(img_name))
#print('Landmarks shape: {}'.format(landmarks.shape))
#print('First 4 Landmarks: {}'.format(landmarks[:4]))