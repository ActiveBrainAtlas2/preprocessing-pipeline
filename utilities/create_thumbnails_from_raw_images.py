import os


from utilities2015 import execute_command
from metadata import ROOT_DIR

## Downsample and normalize images in the "_raw" folder
raw_folder =  os.path.join(ROOT_DIR, stack, 'raw')
for img_name in os.listdir(raw_folder):
    input_fp = os.path.join(raw_folder, img_name)
    output_fp = os.path.join( ROOT_DIR, stack, 'preps', 'thumbnail', img_name )
    
    # Create thumbnails
    execute_command("convert \""+input_fp+"\" -resize 3.125% -auto-level -normalize \
                    -compress lzw \""+output_fp+"\"")
