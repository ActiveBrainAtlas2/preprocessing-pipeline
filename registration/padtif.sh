#!/bin/bash

if (($# < 2))
then
    echo "run program as: ./$0 DK39 2"
    exit 1
fi
#define input
ANIMAL=$1
CHANNEL="CH$2"
#define matlab
MATLABCMD="/usr/local/bin/matlab -nodisplay -nodesktop -nosplash -r "

#define paths
PIPELINE_DIR="/net/birdstore/Active_Atlas_Data/data_root/pipeline_data"
VTK_DIR="$PIPELINE_DIR/$ANIMAL/preps/vtk"
# transform high resolution images
IMG_PATH="$PIPELINE_DIR/$ANIMAL/preps/$CHANNEL/jp2"
REG_TIF_FULL="$PIPELINE_DIR/$ANIMAL/preps/$CHANNEL/full_registered"
#padding the tif
FULL_REG_PAD="$PIPELINE_DIR/$ANIMAL/preps/$CHANNEL/full_registered_padded"
FULL_REG_PAD_JP2="$PIPELINE_DIR/$ANIMAL/preps/$CHANNEL/full_registered_padded_jp2"
mkdir -p $FULL_REG_PAD
mkdir -p $FULL_REG_PAD_JP2
$MATLABCMD "maxNumCompThreads(2); padtif('$REG_TIF_FULL', '$FULL_REG_PAD');exit"

