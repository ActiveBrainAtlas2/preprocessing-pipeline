from pathlib import Path
import argparse

import numpy as np
import tifffile as tiff

import neuroglancer

parser = argparse.ArgumentParser(description='create meshes')
parser.add_argument('img_path_str', type=str, help='path to images')
parser.add_argument('voxel_size', nargs=3, type=int,
                    help='voxel size (x, y, z)')

args = parser.parse_args()

img_path_str = args.img_path_str
voxel_size = args.voxel_size

json_descriptor = '{{"fragments": ["mesh.{}.{}"]}}'

img_path = Path(img_path_str)

mesh_list = []
for f in sorted(img_path.glob('*.tif')):
    A = tiff.imread(str(f))
    mesh_list.append(A)
mesh = np.dstack(mesh_list)
mesh = np.transpose(mesh, (2, 0, 1))

ids = [int(i) for i in np.unique(mesh[:])]

vol = neuroglancer.LocalVolume(
    data=mesh,
    voxel_size=voxel_size,
)

img_path.parent.joinpath(
    'output', 'mesh').mkdir(exist_ok=True, parents=True)

for ID in ids[1:]:
    print(ID)
    mesh_data = vol.get_object_mesh(ID)
    with open(
            str(img_path.parent / 'output' / 'mesh' / '.'.join(
                ('mesh', str(ID), str(ID)))), 'wb') as meshfile:
        meshfile.write(mesh_data)
    with open(
            str(img_path.parent / 'output' / 'mesh' / ''.join(
                (str(ID), ':0'))), 'w') as ff:
        ff.write(json_descriptor.format(ID, ID))

print('ids to insert into URL:')
ids_string = '[\'' + '\'_\''.join([str(i) for i in ids[1:]]) + '\']'
print(ids_string)

print('done')
