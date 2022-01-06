import os
import subprocess
braini = 'DK54'
script_folder = os.path.dirname(os.path.realpath(__file__))
command = f'source/scratch/programming/start ;cd {script_folder}; ./parallel_create_examples {braini}'
ret = subprocess.run(command, capture_output=True, shell=True)