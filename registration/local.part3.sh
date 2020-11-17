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
SEG_DIR="/net/birdstore/Active_Atlas_Data/data_root/atlas_data/vtk"
#################################start process: target to registered space##############################

# transform high resolution images
IMG_PATH="$PIPELINE_DIR/$ANIMAL/preps/$CHANNEL/jp2"
REG_TIF_FULL="$PIPELINE_DIR/$ANIMAL/preps/$CHANNEL/full_registered"
##### is this used? CSV_PATH=$PIPELINE_DIR/Data/$ANIMAL/INPUT_DATA/
#$MATLABCMD "maxNumCompThreads(2); transform('$IMG_PATH', '$VTK_DIR', '$REG_TIF_FULL'); exit"
echo "Finished first part"


# ################################start process: atlas to registered space################################
FULL_REG_PAD="$PIPELINE_DIR/$ANIMAL/preps/$CHANNEL/full_registered_padded"
#1 transform atlas to registered space in 5um space
mkdir -p $OUTPUT_DIR/low_seg/
# 2nd arg is
# 3rd arg is registered_input vtk files
$MATLABCMD "transform_seg('$SEG_DIR/annotation_50.vtk', '$FULL_REG_PAD', '$ANIMAL', 5); exit"

mkdir -p $OUTPUT_DIR/reg_high_seg/
$MATLABCMD "cd('$CODE_DIR'); maxNumCompThreads(2); segresize('$OUTPUT_DIR/low_seg/', '$OUTPUT_DIR/reg_high_tif/', '$OUTPUT_DIR/reg_high_seg/'); exit"


mkdir -p $OUTPUT_DIR/reg_high_seg_pad/
$MATLABCMD "cd('$CODE_DIR'); maxNumCompThreads(2); padseg('$OUTPUT_DIR/reg_high_seg/', '$OUTPUT_DIR/reg_high_seg_pad/'); done('$ANIMAL'); exit"
