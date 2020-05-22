import matplotlib
matplotlib.use('Agg') # set the backend before importing pyplot to be one without a display

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

import sys
_in=sys.argv[1]
_out=sys.argv[2]

def image_grid(result):
    i=0
    def show_in_grid(I,axes):
        axes.axis("off")
        I=I[-1:0:-1,:]
        axes.imshow(I.T, cmap="gray",aspect=1)

    fig = plt.figure(figsize=[11,8.5])

    gs = GridSpec(4, 3, figure=fig)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[0, 2])
    ax4 = fig.add_subplot(gs[1:,:])

    filename=result["file"][14:-4]
    fig.suptitle(filename)

    show_in_grid(result['src'],ax1)
    show_in_grid(result['blob'],ax2)
    show_in_grid(result['mask'],ax3)
    show_in_grid(result['scaled'],ax4)
    plt.subplots_adjust(wspace=.01, hspace=.01)

    pp.savefig(fig)
    plt.close()

import pickle as pk

with open(_in,'rb') as pickle_file:
    results=pk.load(pickle_file)

from matplotlib.backends.backend_pdf import PdfPages
pp=PdfPages(_out)
for i in range(len(results)):
    print('\r GenerateFlipbook',i,end='')
    image_grid(results[i])
pp.close()
