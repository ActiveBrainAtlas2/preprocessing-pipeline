import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

fig, ax = plt.subplots()
A = np.random.rand(10,5,5)
idx0 = 3
l = ax.imshow(A[idx0])

axidx = plt.axes([0.25, 0.15, 0.65, 0.03])
slidx = Slider(axidx, 'index', 0, 10, valinit=idx0, valfmt='%d')

def update(val):
    idx = slidx.val
    l.set_data(A[int(idx)])
    fig.canvas.draw_idle()
slidx.on_changed(update)

plt.show()