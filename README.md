# Cleaning up the existing pipline for python3
# Utilities for the Active Atlas Pipeline
# Installation
1. create a virtual environment in your home dir: python3 -m venv ~/.virtualenvs/pipeline3
1. source ~/.virtualenvs/pipeline3/bin/activate
1. pip install -r requirements.txt 
### For Neuroglancer scripts,
1. git clone https://github.com/HumanBrainProject/neuroglancer-scripts.git
2. python3 -m venv ~/.virtualenvs/neuroglancer
3. source ~/.virtualenvs/neuroglancer/bin/activate
4. cd neuroglancer-scripts
5. python setup.py install
6. Look in ~/.virtualenvs/neuroglancer/bin/ for the precomputed scripts
### Directory structure of the pipeline
1. The base directory is located on birdstore at: /net/birdstore/Active_Atlas_Data/data_root/pipeline_data
2. All brains are located in the base directory.
3. To view the post tif pipeline process go here: [Neuroglancer process](PROCESS.md)
### Annotations
1. Annotation keys are viewable: [here](https://activebrainatlas.ucsd.edu/annotation-keys.html)
