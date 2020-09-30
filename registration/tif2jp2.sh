#!/bin/bash

MATLABCMD="/usr/local/bin/matlab -nodisplay -nodesktop -nosplash -r "

#define path
INPUT=/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK43/tif/
OUTPUT=/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK43/jp2/
$MATLABCMD "maxNumCompThreads(2); tif2jp2('$INPUT', '$OUTPUT'); exit"
