#!/bin/bash

if (($# < 2))
then
    echo "run program as: $0 DK39 2"
    echo "That will run it against DK39 channel 2"
    exit 1
fi
#define input
ANIMAL=$1
CHANNEL="CH$2"
#define matlab
MATLABCMD="/usr/local/bin/matlab -nodisplay -nodesktop -nosplash -r "

#define paths
PIPELINE_DIR="/net/birdstore/Active_Atlas_Data/data_root/pipeline_data"
IMG_PATH="$PIPELINE_DIR/$ANIMAL/preps/$CHANNEL/full/"
ROT_PATH="$PIPELINE_DIR/$ANIMAL/rotations/"
OUTPUT="$PIPELINE_DIR/$ANIMAL/preps/$CHANNEL/full_transformed/"
mkdir -p $OUTPUT
#################################start process: target to registered space##############################
##### transform
$MATLABCMD "maxNumCompThreads(1); transform_fast_marmo('$IMG_PATH', '$ROT_PATH', '$OUTPUT'); exit"
echo "Finished transform"

#function transform_fast_marmo(img_path, recon_path, output_dir, csv_path)
