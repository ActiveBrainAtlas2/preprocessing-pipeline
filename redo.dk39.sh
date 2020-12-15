#!/bin/bash


rm -f /net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK39/preps/CH1/thumbnail_aligned/*.tif
rm -f /net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK39/preps/CH1/thumbnail_cleaned/*.tif
python create_clean.py --animal DK39 --channel 1 --rotation 1 --flip flip
#cp -vf /net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK39/preps/CH1/thumbnail_cleaned/215.tif \
#/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK39/preps/CH1/thumbnail_cleaned/216.tif
#cp -vf /net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK39/preps/CH1/thumbnail_cleaned/218.tif \
#/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK39/preps/CH1/thumbnail_cleaned/217.tif

