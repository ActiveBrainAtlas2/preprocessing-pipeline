"""
Takes as input a numpy 3D arrays with structure boundaries resprested as a non-zero id and fills in the structures
in the 3D array.
"""


import boto3
import numpy as np
import os

struct = 'MD594'
S3_BUCKET = 'test-bucket-sid'
S3_FILE_LOC = f'alex_neuroglancer_volumes/{struct}/human_annotation/solid_volume_5um/volume_colored.npy'
DOWNLOAD_DIR = '/net/birdstore/Active_Atlas_Data/data_root/CSHL_volumes/vol_fill'
LOCAL_FILE_NAME = f'{struct}_full.npy'

s3_client = boto3.client('s3')

LOCAL_FILE_LOC = os.path.join(DOWNLOAD_DIR, LOCAL_FILE_NAME)
FINAL_FILE_LOC = os.path.join(DOWNLOAD_DIR, f'{struct}_full_filled.npy')

def main():
    # Download the file from S3

    s3_client = boto3.client('s3')

    # Download the file from S3
    print(f"Starting Download for {LOCAL_FILE_LOC}")
    s3_client.download_file(S3_BUCKET, S3_FILE_LOC, LOCAL_FILE_LOC)
    print("Download complete")

    vol_arr = np.load(LOCAL_FILE_LOC)

    print(f"Array Shape: {vol_arr.shape}")

    struct = {}

    for z in range(0, vol_arr.shape[0]):
        print(f"On Z: {z}")
        for x in range(0, vol_arr.shape[2]):
            struct = {}
            for y in range(0, vol_arr.shape[1]):
                curr_val = vol_arr[z][y][x]
                if curr_val != 0:
                    if curr_val in struct:
                        struct[curr_val].append(y)
                    else:
                        struct[curr_val] = [y]

            for st in struct:
                # print(f"Filling struct {st}")
                for y in range(struct[st][0], struct[st][-1]+1):
                    vol_arr[z][y][x] = st


    print(f"Finished filling cells")
    np.save(FINAL_FILE_LOC, vol_arr)


if __name__ == '__main__':
    main()
