from lib.sqlcontroller import SqlController
animal = 'DK39'
controller = SqlController(animal)
abbreviation = ''
layer =''
person_id = 26
input_type_id = 6
controller.add_layer_data(abbreviation, animal, layer, x, y, section, input_type_id)
