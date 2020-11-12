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
#################################start process: target to registered space##############################

# transform high resolution images
IMG_PATH="$PIPELINE_DIR/$ANIMAL/preps/$CHANNEL/jp2"
REG_TIF_FULL="$PIPELINE_DIR/$ANIMAL/preps/$CHANNEL/full_registered"
##### is this used? CSV_PATH=$PIPELINE_DIR/Data/$ANIMAL/INPUT_DATA/
$MATLABCMD "maxNumCompThreads(2); transform('$IMG_PATH', '$VTK_DIR', '$REG_TIF_FULL'); exit"
echo "Finished first part"
