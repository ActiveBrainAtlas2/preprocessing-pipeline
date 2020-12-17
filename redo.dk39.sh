#!/bin/bash


rm -f /net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK39/preps/CH1/thumbnail_aligned/*.tif
rm -f /net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK39/preps/CH1/thumbnail_cleaned/*.tif
python create_clean.py --animal DK39 --channel 1 --rotation 1 --flip flip
cp -vf /net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK39/preps/CH1/thumbnail_cleaned/217.tif \
/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK39/preps/CH1/thumbnail_cleaned/216.tif
cd registration
python create_registration.py --animal DK39 --iterations 1
cd ..
rm -f /net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK39/preps/CH1/thumbnail_aligned/*.tif
rm -f /net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK39/preps/CH1/thumbnail_cleaned/*.tif
python create_clean.py --animal DK39 --channel 1 --rotation 1 --flip flip
cd registration
python process_registration.py
cd ..
echo "finished"

