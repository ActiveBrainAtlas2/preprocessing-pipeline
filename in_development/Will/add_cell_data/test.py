from controller import FeaturesController
import numpy as np
from cell_model import Cell
import zlib
controller = FeaturesController()
test_array  =np.random.rand(10)
test_array_bytes = test_array.tobytes()
test_array_bytes = zlib.compress(test_array_bytes)
cell = Cell(id = 1,prep_id = 'test',section = 1,x = 1, y = 1,cell_images = test_array_bytes)
controller.drop_cell_by_id(1)
controller.add_row(cell)
celli = controller.get_cell_by_id(1)
received_bytes = celli.cell_images
received_bytes = zlib.decompress(received_bytes)
y = np.frombuffer(received_bytes, test_array.dtype)
assert(np.array_equal(y,test_array))