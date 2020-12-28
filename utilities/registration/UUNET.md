1. get conda installer from https://www.anaconda.com/products/individual#download-section
2. run Anaconda install, hit enter to accept license
after that has run, run these commands:
3. conda install numpy ninja pyyaml mkl mkl-include setuptools cmake cffi typing_extensions future six requests dataclasses
4. conda install -c pytorch magma-cuda91
You need to create these directories in your home dir
mkdir /home/tbroggini/nnUNet_raw
mkdir /home/tbroggini/nnUNet_preprocessed
mkdir /home/tbroggini/nnUNet_trained_models


put this at the bottom of your .bashrc file:

export nnUNet_raw_data_base="/home/tbroggini/nnUNet_raw"
export nnUNet_preprocessed="/home/tbroggini/nnUNet_preprocessed"
export RESULTS_FOLDER="/home/tbroggini/nnUNet_trained_models"


log out and then back in to make sure they got set. Test by doing:
echo $RESULTS_FOLDER

That should echo that folder.

Test the install with an example:
https://github.com/MIC-DKFZ/nnUNet/blob/master/documentation/training_example_Hippocampus.md

I already put the data in your home folder, just run these commands:

nnUNet_convert_decathlon_task -i ~/Task04_Hippocampus


### You can now run nnU-Nets pipeline configuration (and the preprocessing) with the following line:

nnUNet_plan_and_preprocess -t 4

### Where 4 refers to the task ID of the Hippocampus dataset.

#### Now you can already start network training. This is how you train a 3d full resoltion U-Net on the Hippocampus dataset:

nnUNet_train 3d_fullres nnUNetTrainerV2 4 0
