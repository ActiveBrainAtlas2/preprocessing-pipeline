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
IMG_PATH="$PIPELINE_DIR/$ANIMAL/preps/$CHANNEL/jp2"
REG_TIF_FULL="$PIPELINE_DIR/$ANIMAL/preps/$CHANNEL/full_registered"
FULL_REG_PAD="$PIPELINE_DIR/$ANIMAL/preps/$CHANNEL/full_registered_padded"
SEG_DIR="/net/birdstore/Active_Atlas_Data/data_root/atlas_data/vtk"
#################################start process: target to registered space##############################
##### transform
$MATLABCMD "maxNumCompThreads(2); transform('$IMG_PATH', '$VTK_DIR', '$REG_TIF_FULL'); exit"
echo "Finished transform"
##### pad
$MATLABCMD "maxNumCompThreads(2); padtif('$REG_TIF_FULL', '$FULL_REG_PAD');exit"
echo "Finished padding"
##### register
$MATLABCMD "transform_seg('$SEG_DIR/annotation_50.vtk', '$FULL_REG_PAD', '$ANIMAL', 5); exit"
echo "Finished registering"
