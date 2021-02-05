import os, sys
import argparse
import numpy as np
import dask.array as da
import neuroglancer
import neuroglancer.cli
import dask.array
from skimage import io

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager



def add_dask_layer(state):
    """Adds a lazily-computed data source backed by dask."""
    # https://docs.dask.org/en/latest/array-creation.html#using-dask-delayed
    fileLocationManager = FileLocationManager('X')
    INPUT = os.path.join(fileLocationManager.prep, 'CH1/thumbnail_aligned')

    def make_array(k):
        print('Computing k=%d' % (k, ))
        filepath = os.path.join()
        img = io.imread(filepath)
        return np.full(shape=(256, 256), fill_value=k, dtype=np.uint8)

    #lazy_make_array = dask.delayed(make_array, pure=True)

    files = sorted(os.listdir(INPUT))
    lazy_chunks = []
    for f in files[0:15]:
        filepath = os.path.join(INPUT, f)
        img = io.imread(filepath)
        lazy_chunks.append(dask.delayed(img.reshape(1, img.shape[0],img.shape[1])))

    img0 = lazy_chunks[0].compute()  # load the first chunk (assume rest are same shape/dtype)
    arrays = [
        dask.array.from_delayed(lazy_chunk, dtype=img0.dtype, shape=img0.shape)
        for lazy_chunk in lazy_chunks
    ]

    x = dask.array.concatenate(arrays)
    print(type(img0), np.shape(img0))
    print(type(x), np.shape(x))
    sys.exit()
    resolution = 1000
    scale = 3
    scales = (resolution*scale, resolution*scale, resolution*scale)
    dims = neuroglancer.CoordinateSpace(
        names=['x', 'y', 'z'],
        units=['nm', 'nm', 'nm'],
        scales=scales)

    state.layers['dask'] = neuroglancer.ImageLayer(source=neuroglancer.LocalVolume(x, dimensions=dims))
    #state.layers['dask'] = neuroglancer.SegmentationLayer(source=neuroglancer.LocalVolume(x, dimensions=dims))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    neuroglancer.cli.add_server_arguments(ap)
    args = ap.parse_args()
    neuroglancer.cli.handle_server_arguments(args)
    viewer = neuroglancer.Viewer()
    with viewer.txn() as s:
        add_dask_layer(s)
    print(viewer)
