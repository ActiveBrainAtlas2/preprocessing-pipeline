import sys
import os
path = os.path.abspath(os.path.join( os.path.dirname( __file__ ), '..' ,'..'))
sys.path.append(path)
from lib.UrlGenerator import UrlGenerator
from abakit.lib.Controllers.SqlController import SqlController
animal = 'DK55'
urlGen = UrlGenerator()
sqlController = SqlController(animal)
image_layer = 'precomputed://https://activebrainatlas.ucsd.edu/data/'+animal+'/neuroglancer_data/'
urlGen.add_precomputed_image_layer(image_layer+'C1')
urlGen.add_precomputed_image_layer(image_layer+'C2',layer_color='red')
urlGen.add_precomputed_image_layer(image_layer+'C3',layer_color='green')
urlGen.add_annotation_layer('Sure')
urlGen.add_annotation_layer('Unsure',color_hex='#1e00ff')
urlGen.add_annotation_layer('Positive',color_hex='#00ffcc')
urlGen.add_annotation_layer('Negative',color_hex='#ee00ff')
url = urlGen.get_url()
print('done')
# sqlController.add_url(url,animal+'cell detection vetting')