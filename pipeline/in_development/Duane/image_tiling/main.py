import time
import os
import dask
from dask.distributed import LocalCluster, Client
from dask_image.imread import imread
from zarr.util import human_readable_size


animal = "DK59"
input_path = f'/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{animal}/preps/CH1/full_aligned'

#STEP 1 - READ IMAGE STACK
start = time.time()
image_stack = imread(f"{input_path}/*.tif")
end = time.time()
print("Operation time: ", (end - start), "sec")

sections = image_stack.shape[0]
img_rows = image_stack.shape[1]
img_columns = image_stack.shape[2]

print(f"ORG IMAGE STACK MEM: {human_readable_size(image_stack.nbytes)}")
print(f"ORG IMAGE STACK SHAPE: {image_stack.shape}")
print(f"ORG IMAGE STACK DTYPE: {image_stack.dtype}")

output_path = f'/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{animal}/neuroglancer_data/zarr/C1.zarr'
tmp_dir = "/data/tmp"
max_client_ram = "20GB"
max_n_workers = 1

#CREATE 'LOCAL CLUSTER' TO PROCESS CHUNKS IN SERIAL MANNER
cluster = LocalCluster(
    n_workers=max_n_workers,
    threads_per_worker=1,
    memory_limit=max_client_ram,
    local_directory=tmp_dir,
    processes=False,
)

#STEP 2 - RECHUNK TO FIT INTO RAM
tiles = image_stack.rechunk('auto', balance=True)

print(f"[PROPOSED] ZARR IMG STACK SHAPE: {tiles.shape}")
print(f"[PROPOSED] ZARR IMG STACK CHUNKSIZE: {tiles.chunksize}")
print(f"[PROPOSED] ZARR IMG STACK INDIVIDUAL CHUNK MEMORY USAGE: {dask.config.get('array.chunk-size')}")
print(f"[PROPOSED] ZARR IMG STACK TOTAL CHUNK COUNT: {len(tiles.chunks[0])*len(tiles.chunks[1])*len(tiles.chunks[2])}")


#STEP 3 - OUTPUT IMAGE STACK TO .zarr FORMAT
tiles.to_zarr(output_path, overwrite=True)