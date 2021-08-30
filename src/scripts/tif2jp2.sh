#!/bin/bash

if (($# < 2))
then
    echo "No input brainname,channel argument... exiting"
    exit 1
fi
#define input
ANIMAL=$1
CHANNEL="CH$2"


MATLABCMD="/usr/local/bin/matlab -nodisplay -nodesktop -nosplash -r "

#define path
INPUT="/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/$ANIMAL/preps/$CHANNEL/full"
OUTPUT="/data2/dklabs_dropbox/UCSD_to_from_CSHL/$ANIMAL/$CHANNEL"
mkdir -p $OUTPUT
$MATLABCMD "maxNumCompThreads(2); tif2jp2('$INPUT', '$OUTPUT'); exit"
