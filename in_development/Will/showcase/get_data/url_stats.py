from lib.SqlController import SqlController
import sys
import numpy as np
import matplotlib.pyplot as plt
controller = SqlController('DK52')
ids = controller.get_url_id_list()
url_size = []
for idi in ids:
    url = controller.get_urlModel(idi)
    url_size.append(sys.getsizeof(url.url))
url_size = np.array(url_size)
url_size = url_size/1024

url_size = np.sort(url_size)
url_size[-10:]
np.std(url_size)
plt.hist(url_size)
plt.show()
print('done')