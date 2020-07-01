import os
import socket
import neuroglancer
import subprocess
import numpy as np
from neuroglancer.server import global_server_args

NEUROGLANCER_ROOT = '/home/eddyod/MouseBrainSlicer_data'


class Neuroglancer_Viewer:
    def __init__(self, stack='MD585'):
        self.stack = stack
        self.local_volume_fp_root = './'

        neuroglancer.set_server_bind_address('0.0.0.0')
        global_server_args['bind_port'] = 8099

        # Create viewer
        self.viewer = neuroglancer.Viewer()

        # Get the IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        print('s.getsockname', s.getsockname())
        ip_name = s.getsockname()[0]
        s.close()
        #ip_name = '127.0.0.1'

        # Removes the following symbols: ', ", [, ]
        self.url = str('http://' + ip_name + ':' + self.viewer.get_viewer_url().split(':')[2])  ##Remote URL
        #self.url = self.viewer

    def set_local_volume_fp(self, fp):
        if fp[len(fp) - 1] != '/':
            fp = fp + '/'
        self.local_volume_fp_root = fp

    def download_volumes(self):
        s3_root_fp = 's3://test-bucket-sid/alex_neuroglancer_volumes/' + self.stack + '/human_annotations_5um/'
        local_volume_fp = self.local_volume_fp_root + self.stack + '/human_annotations_5um/'

        command_list = ['aws', 's3', 'cp', '--recursive', s3_root_fp, local_volume_fp]
        subprocess.call(command_list)

    def add_stack(self):
        if self.stack == 'MD585':
            with self.viewer.txn() as s:
                s.layers[self.stack + '_image'] = neuroglancer.ImageLayer( \
                    source='precomputed://https://mousebrainatlas-datajoint-jp2k.s3.amazonaws.com/precomputed/MD585_fullres')
        elif self.stack == 'MD589':
            with self.viewer.txn() as s:
                s.layers[self.stack + '_image'] = neuroglancer.ImageLayer( \
                    source='precomputed://https://mousebrainatlas-datajoint-jp2k.s3.amazonaws.com/precomputed/MD589_fullres')
        elif self.stack == 'MD594':
            with self.viewer.txn() as s:
                s.layers[self.stack + '_image'] = neuroglancer.ImageLayer( \
                    source='precomputed://https://mousebrainatlas-datajoint-jp2k.s3.amazonaws.com/precomputed/MD594_fullres')

    def add_volume(self, colored=True):
        volume_filepath = os.path.join(self.local_volume_fp_root, self.stack, 'human_annotation/solid_volume_5um')
        if colored:
            volume_fn = 'volume_colored.npy'
            color_segments = []
            for i in range(1, 50):
                color_segments.append(i)
        else:
            volume_fn = 'volume.npy'

        xy_ng_resolution_um = 5
        volume_data = np.load(os.path.join(volume_filepath, volume_fn))
        # deprecated voxel_size = [xy_ng_resolution_um * 1000, xy_ng_resolution_um * 1000, 20000],  # X Y Z
        dims = neuroglancer.CoordinateSpace(
            names=['x', 'y', 'z'],
            units=['nm', 'nm', 'nm'],
            scales=[10, 10, 10])

        with self.viewer.txn() as s:
            s.layers[self.stack + "_Annotations"] = neuroglancer.SegmentationLayer(
                source=neuroglancer.LocalVolume(
                    data=volume_data,  # Z,Y,X
                    dimensions=dims,
                    voxel_offset=[0, 0, 0]  # X Y Z
                ),
                segments=color_segments
            )

    def reset_orientation(self):
        with self.viewer.txn() as s:
            # Resets X/Y/Z plane orientation

            #s.navigation.pose.orientation = [0, 0, 0, 1]
            # Zooms out
            #s.navigation.zoomFactor = 5000  # 5000 If xy, 10000 If 4panel
            # Resets 3D Viewer Orientation
            s.perspectiveOrientation = [0, 0, 0, 1]
            # Zooms out
            #s.perspectiveZoom = 75000

            s.layout = 'xy'  # '3d'/'4panel'/'xy'

    def stop(self):
        neuroglancer.stop()


viewers = []

print('MD589')
viewers.append( Neuroglancer_Viewer(stack='MD589') )
viewers[0].add_stack()
viewers[0].set_local_volume_fp( fp=NEUROGLANCER_ROOT )
viewers[0].add_volume()
viewers[0].reset_orientation()
print(viewers[0].url)
