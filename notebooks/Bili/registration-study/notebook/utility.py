import matplotlib.pyplot as plt
import numpy as np

def downsample(image, factor):
    pass

def imshow_midslice(image, ax=None):
    if ax == None:
        _, ax = plt.subplots(1, 3)
    mid_x, mid_y, mid_z = np.array(image.shape) // 2
    kwargs = {
        'aspect':'equal',
        'cmap': 'gray',
    }
    ax[0].imshow(image[:,:,mid_z], **kwargs)
    ax[0].set_xlabel('x1')
    ax[0].set_ylabel('x0')
    ax[1].imshow(image[:,mid_y,:], **kwargs)
    ax[1].set_xlabel('x2')
    ax[1].set_ylabel('x0')
    ax[2].imshow(image[mid_x,:,:], **kwargs)
    ax[2].set_xlabel('x2')
    ax[2].set_ylabel('x1')
    plt.tight_layout()
    plt.show()

def normalize_intensity(image):
    v_min, v_max = image.min(), image.max()
    image = (image - v_min) / (v_max - v_min)
    return image
