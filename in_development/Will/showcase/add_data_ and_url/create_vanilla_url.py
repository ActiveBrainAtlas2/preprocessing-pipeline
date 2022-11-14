import sys
import os
path = os.path.abspath(os.path.join( os.path.dirname( __file__ ), '..' ,'..'))
sys.path.append(path)
from pipeline.lib.UrlGenerator import UrlGenerator
from pipeline.Controllers.SqlController import SqlController
animal = 'DK39'
urlGen = UrlGenerator()
sqlController = SqlController(animal,schema = 'active_atlas_production')
image_layer = 'precomputed://https://activebrainatlas.ucsd.edu/data/'+animal+'/neuroglancer_data/'
urlGen.add_precomputed_image_layer(image_layer+'C1','C1')
urlGen.add_precomputed_image_layer(image_layer+'C2',layer_color='red',name ='C2')
urlGen.add_precomputed_image_layer(image_layer+'C3',layer_color='green',name = 'C3')
url = urlGen.get_url()
print('done')
# sqlController.add_url(url,animal+'cell detection vetting')