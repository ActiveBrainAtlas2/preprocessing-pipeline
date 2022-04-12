from Will.toolbox.tmp.LoadCom import ComLoader
from abakit.lib.SqlController import SqlController
loader = ComLoader()
loader.load_detected_com()
loader.load_data()
controller = SqlController('DK52')
animal = 'DK63'
layer = 'KuiDetection'
detected = loader.detected[animal]

for str,coord in detected.items():
    x,y,section = coord
    controller.add_layer_data(str, animal, layer, x, y, section, input_type_id = 3,person_id = 34)
print('done')