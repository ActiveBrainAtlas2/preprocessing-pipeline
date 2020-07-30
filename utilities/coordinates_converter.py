################
## Conversion ##
################
import os, sys
import numpy as np

#### visualattion_tools.py
sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.alignment_utility import convert_resolution_string_to_um, load_transforms
from utilities.sqlcontroller import SqlController

SECTION_THICKNESS = 20.  # in um

class CoordinatesConverter(object):
    def __init__(self, stack=None, section_list=None):
        """
        """
        # A 3-D frame is defined by the following information:
        # - plane: the anatomical name of the 2-D plane spanned by x and y axes.
        # - zdim_um: ??
        # - origin_wrt_wholebrain_um: the origin with respect to wholebrain, in microns.

        # Some are derivable from data_feeder
        # some from stack name
        # some must be assigned dynamically
        # this import has to be here to avoid circular imports
        from utilities.imported_atlas_utilities import load_original_volume_v2
        self.frames = {'wholebrain': {'origin_wrt_wholebrain_um': (0,0,0),
        'zdim_um': None},
        # 'sagittal': {'origin_wrt_wholebrain_um': None,
        # 'plane': 'sagittal', 'zdim_um': None},
        # 'coronal': {'origin_wrt_wholebrain_um': None,
        # 'plane': 'coronal', 'zdim_um': None},
        # 'horizontal': {'origin_wrt_wholebrain_um': None,
        # 'plane': 'horizontal', 'zdim_um': None},
        }

        self.resolutions = {}
        self.stack = stack
        xmin = 520
        xmax = 1004
        ymin = 128
        ymax = 496

        cropbox = np.array((xmin, xmax, ymin, ymax))

        # Define frame:wholebrainXYcropped
        cropbox_origin_xy_wrt_wholebrain_tbResol = cropbox[[0,2]]

        self.derive_three_view_frames(base_frame_name='wholebrainXYcropped',
        origin_wrt_wholebrain_um=np.r_[cropbox_origin_xy_wrt_wholebrain_tbResol, 0] * convert_resolution_string_to_um(self.stack, 'thumbnail'))

        # Define frame:wholebrainWithMargin
        intensity_volume_spec = dict(name=stack, resolution='10.0um', prep_id='wholebrainWithMargin', vol_type='intensity')
        thumbnail_volume, thumbnail_volume_origin_wrt_wholebrain_10um = load_original_volume_v2(intensity_volume_spec, return_origin_instead_of_bbox=True)
        thumbnail_volume_origin_wrt_wholebrain_um = thumbnail_volume_origin_wrt_wholebrain_10um * 10.

        # thumbnail_volume, (thumbnail_volume_origin_wrt_wholebrain_dataResol_x, thumbnail_volume_origin_wrt_wholebrain_dataResol_y, _) = \
        # DataManager.load_original_volume_v2(intensity_volume_spec, return_origin_instead_of_bbox=True)
        # thumbnail_volume_origin_wrt_wholebrain_um = np.r_[thumbnail_volume_origin_wrt_wholebrain_dataResol_x * 10., thumbnail_volume_origin_wrt_wholebrain_dataResol_y * 10., 0.]

        self.derive_three_view_frames(base_frame_name='wholebrainWithMargin',
                               origin_wrt_wholebrain_um=thumbnail_volume_origin_wrt_wholebrain_um,
                                     zdim_um=thumbnail_volume.shape[2] * 10.)

        # Define resolution:raw
        self.register_new_resolution('raw', convert_resolution_string_to_um(stack, 'raw'))

        if section_list is not None:
            self.section_list = section_list

    def set_data(self, data_feeder, stack=None):

        self.data_feeder = data_feeder
        self.stack = stack

        for frame_name, frame in self.frames.items():
            if hasattr(self.data_feeder, 'z_dim'):
                frame['zdim_um'] = self.data_feeder.z_dim * convert_resolution_string_to_um(self.stack, self.data_feeder.resolution)

        self.resolutions['image'] = {'um': convert_resolution_string_to_um(self.stack, self.data_feeder.resolution)}
        if hasattr(self.data_feeder, 'sections'):
            self.section_list = self.data_feeder.sections

            # cropbox_origin_xy_wrt_wholebrain_tbResol = DataManager.load_cropbox_v2(stack=stack, prep_id=self.prep_id)[[0,2]]
            # self.frames['wholebrainXYcropped'] = dict(origin_wrt_wholebrain_um=np.r_[cropbox_origin_xy_wrt_wholebrain_tbResol, 0] * convert_resolution_string_to_um(resolution='thumbnail', stack=stack),
            # plane='sagittal', 'zdim_um'=None)

    def derive_three_view_frames(self, base_frame_name, origin_wrt_wholebrain_um=(0,0,0), zdim_um=None):
        """
        Generate three new coordinate frames, based on a given bounding box.
        Names of the new frames are <base_frame_name>_sagittal, <base_frame_name>_coronal and <base_frame_name>_horizontal.

        Args:
            base_frame_name (str):
        """

        if base_frame_name == 'data': # define by data feeder
            if hasattr(self.data_feeder, 'z_dim'):
                zdim_um = self.data_feeder.z_dim * convert_resolution_string_to_um(self.stack, self.data_feeder.resolution)

        self.register_new_frame(base_frame_name, origin_wrt_wholebrain_um, zdim_um)

    def register_new_frame(self, frame_name, origin_wrt_wholebrain_um, zdim_um=None):
        """
        Args:
            frame_name (str): frame identifier
        """
        # assert frame_name not in self.frames, 'Frame name %s already exists.' % frame_name

        if frame_name not in self.frames:
            self.frames[frame_name] = {'origin_wrt_wholebrain_um': None, 'zdim_um': None}

        if zdim_um is not None:
            self.frames[frame_name]['zdim_um'] = zdim_um

        if origin_wrt_wholebrain_um is not None:
            self.frames[frame_name]['origin_wrt_wholebrain_um'] = origin_wrt_wholebrain_um

        # if plane is not None:
        #     self.frames[frame_name]['plane'] = plane

    def register_new_resolution(self, resol_name, resol_um):
        """
        Args:
            resol_name (str): resolution identifier
            resol_um (float): pixel/voxel size in micron
        """
        # assert resol_name not in self.resolutions, 'Resolution name %s already exists.' % resol_name
        self.resolutions[resol_name] = {'um': resol_um}

    def get_resolution_um(self, resol_name):

        if resol_name in self.resolutions:
            res_um = self.resolutions[resol_name]['um']
        else:
            res_um = convert_resolution_string_to_um(self.stack, resol_name)
        return res_um

    def convert_three_view_frames(self, p, base_frame_name, in_plane, out_plane, p_resol):
        """
        Convert among the three frames specified by the second method in this presentation
        https://docs.google.com/presentation/d/1o5aQbXY5wYC0BNNiEZm7qmjvngbD_dVoMyCw_tAQrkQ/edit#slide=id.g2d31ede24d_0_0

        Args:
            in_plane (str): one of sagittal, coronal and horizontal
            out_plane (str): one of sagittal, coronal and horizontal
        """

        if in_plane == 'coronal' or in_plane == 'horizontal' or out_plane == 'coronal' or out_plane == 'horizontal':
            zdim_um = self.frames[base_frame_name]['zdim_um']
            zdim = zdim_um / convert_resolution_string_to_um(self.stack, p_resol)

        if in_plane == 'sagittal':
            p_sagittal = p
        elif in_plane == 'coronal':
            x = p[..., 2]
            y = p[..., 1]
            z = zdim - p[..., 0]
            p_sagittal = np.column_stack([x,y,z])
        elif in_plane == 'horizontal':
            x = p[..., 0]
            y = p[..., 2]
            z = zdim - p[..., 1]
            p_sagittal = np.column_stack([x,y,z])
        else:
            raise Exception("Plane %s is not recognized." % in_plane)

        if out_plane == 'sagittal':
            p_out = p_sagittal
        elif out_plane == 'coronal':
            x = zdim - p_sagittal[..., 2]
            y = p_sagittal[..., 1]
            z = p_sagittal[..., 0]
            p_out = np.column_stack([x,y,z])
        elif out_plane == 'horizontal':
            x = p_sagittal[..., 0]
            y = zdim - p_sagittal[..., 2]
            z = p_sagittal[..., 1]
            p_out = np.column_stack([x,y,z])
        else:
            raise Exception("Plane %s is not recognized." % out_plane)

        return p_out

    def convert_resolution(self, p, in_resolution, out_resolution):
        """
        Rescales coordinates according to the given input and output resolution.
        This function does not change physical position of coordinate origin or the direction of the axes.
        """

        p = np.array(p)
        if p.ndim != 2:
            print(p, in_resolution, out_resolution)
        assert p.ndim == 2

        import re
        m = re.search('^(.*?)_(.*?)_(.*?)$', in_resolution)
        if m is not None:
            in_x_resol, in_y_resol, in_z_resol = m.groups()
            assert in_x_resol == in_y_resol
            uv_um = p[..., :2] * self.get_resolution_um(resol_name=in_x_resol)
            d_um = np.array([SECTION_THICKNESS * (sec - 0.5) for sec in p[..., 2]])
            p_um = np.column_stack([uv_um, d_um])
        else:
            if in_resolution == 'image':
                p_um = p * self.resolutions['image']['um']
            elif in_resolution == 'image_image_index':
                uv_um = p[..., :2] * self.get_resolution_um(resol_name='image')
                i_um = np.array([SECTION_THICKNESS * (self.section_list[int(idx)] - 0.5) for idx in p[..., 2]])
                p_um = np.column_stack([uv_um, i_um])
            elif in_resolution == 'section':
                uv_um = np.array([(np.nan, np.nan) for _ in p])
                # d_um = np.array([SECTION_THICKNESS * (sec - 0.5) for sec in p])
                d_um = SECTION_THICKNESS * (p[:, 0] - 0.5)
                p_um = np.column_stack([np.atleast_2d(uv_um), np.atleast_1d(d_um)])
            elif in_resolution == 'index':
                uv_um = np.array([(np.nan, np.nan) for _ in p])
                # i_um = np.array([SECTION_THICKNESS * (self.section_list[int(idx)] - 0.5) for idx in p])
                i_um = SECTION_THICKNESS * (np.array(self.section_list)[p[:,0].astype(np.int)] - 0.5)
                p_um = np.column_stack([uv_um, i_um])
            else:
                if in_resolution in self.resolutions:
                    p_um = p * self.resolutions[in_resolution]['um']
                else:
                    p_um = p * convert_resolution_string_to_um(resolution=in_resolution, stack=self.stack)


        m = re.search('^(.*?)_(.*?)_(.*?)$', out_resolution)
        if m is not None:
            out_x_resol, out_y_resol, out_z_resol = m.groups()
            assert out_x_resol == out_y_resol # i.e. image
            uv_outResol = p_um[..., :2] / self.get_resolution_um(resol_name=out_x_resol)
            sec_outResol = np.array([1 + int(np.floor(d_um / SECTION_THICKNESS)) for d_um in np.atleast_1d(p_um[..., 2])])
            p_outResol = np.column_stack([np.atleast_2d(uv_outResol), np.atleast_1d(sec_outResol)])
        else:
            if out_resolution == 'image':
                p_outResol = p_um / self.resolutions['image']['um']
            #elif out_resolution == 'image_image_section':
            #    uv_outResol = p_um[..., :2] / self.resolutions['image']['um']
            #    sec_outResol = np.array([1 + int(np.floor(d_um / SECTION_THICKNESS)) for d_um in np.atleast_1d(p_um[..., 2])])
            #    p_outResol = np.column_stack([np.atleast_2d(uv_outResol), np.atleast_1d(sec_outResol)])
            elif out_resolution == 'image_image_index':
                uv_outResol = p_um[..., :2] / self.get_resolution_um(resol_name='image')
                if hasattr(self, 'section_list'):
                    i_outResol = []
                    for d_um in p_um[..., 2]:
                        sec = 1 + int(np.floor(d_um / SECTION_THICKNESS))
                        if sec in self.section_list:
                            index = self.section_list.index(sec)
                        else:
                            index = np.nan
                        i_outResol.append(index)
                    i_outResol = np.array(i_outResol)
                else:
                    i_outResol = p_um[..., 2] / self.resolutions['image']['um']
                p_outResol = np.column_stack([uv_outResol, i_outResol])
            elif out_resolution == 'section':
                uv_outResol = p_um[..., :2] / self.resolutions['image']['um']
                sec_outResol = np.array([1 + int(np.floor(d_um / SECTION_THICKNESS)) for d_um in np.atleast_1d(p_um[..., 2])])
                p_outResol = np.column_stack([np.atleast_2d(uv_outResol), np.atleast_1d(sec_outResol)])[..., 2][:, None]
            elif out_resolution == 'index':
                uv_outResol = np.array([(np.nan, np.nan) for _ in p_um])
                # uv_outResol = p_um[..., :2] / self.resolutions['image']['um']
                if hasattr(self, 'section_list'):
                    i_outResol = []
                    for d_um in p_um[..., 2]:
                        sec = 1 + int(np.floor(d_um / SECTION_THICKNESS))
                        if sec in self.section_list:
                            index = self.section_list.index(sec)
                        else:
                            index = np.nan
                        i_outResol.append(index)
                    i_outResol = np.array(i_outResol)
                else:
                    i_outResol = p_um[..., 2] / self.resolutions['image']['um']
                p_outResol = np.column_stack([uv_outResol, i_outResol])[..., 2][:, None]
            else:
                if out_resolution in self.resolutions:
                    p_outResol = p_um / self.resolutions[out_resolution]['um']
                else:
                    p_outResol = p_um / convert_resolution_string_to_um(resolution=out_resolution, stack=self.stack)

        assert p_outResol.ndim == 2

        return p_outResol

    def convert_from_wholebrain_um(self, p_wrt_wholebrain_um, wrt, resolution):
        """
        Convert the coordinates expressed in "wholebrain" frame in microns to
        coordinates expressed in the given frame and resolution.

        Args:
            p_wrt_wholebrain_um (list of 3-tuples): list of points
            wrt (str): name of output frame
            resolution (str): name of output resolution.
        """

        p_wrt_wholebrain_um = np.array(p_wrt_wholebrain_um)
        # assert np.atleast_2d(p_wrt_wholebrain_um).shape[1] == 3, "Coordinates of each point must have three elements."
        assert p_wrt_wholebrain_um.ndim == 2

        if wrt == 'wholebrain':
            p_wrt_outdomain_um = p_wrt_wholebrain_um
        else:
            assert isinstance(wrt, tuple)
            base_frame_name, plane = wrt
            p_wrt_outSagittal_origin_um = p_wrt_wholebrain_um - self.frames[base_frame_name]['origin_wrt_wholebrain_um']
            assert p_wrt_outSagittal_origin_um.ndim == 2
            p_wrt_outdomain_um = self.convert_three_view_frames(p=p_wrt_outSagittal_origin_um, base_frame_name=base_frame_name,
                                                                in_plane='sagittal',
                                                                out_plane=plane,
                                                                p_resol='um')

        assert p_wrt_outdomain_um.ndim == 2
        p_wrt_outdomain_outResol = self.convert_resolution(p_wrt_outdomain_um, in_resolution='um', out_resolution=resolution)
        assert p_wrt_outdomain_outResol.ndim == 2
        return p_wrt_outdomain_outResol

    def convert_to_wholebrain_um(self, p, wrt, resolution):
        """
        Convert the coordinates expressed in given frame and resolution to
        coordinates expressed in "wholebrain" frame in microns.

        Args:
            p (list of 3-tuples): list of points
            wrt (str): name of input frame
            resolution (str): name of input resolution.
        """

        p = np.array(p)
        # assert np.atleast_2d(p).shape[1] == 3, "Coordinates must have three elements."
        p_um = self.convert_resolution(p, in_resolution=resolution, out_resolution='um')

        if wrt == 'wholebrain':
            p_wrt_wholebrain_um = p_um
        else:
            assert isinstance(wrt, tuple)
            base_frame_name, plane = wrt

            assert p_um.ndim == 2
            p_wrt_inSagittal_um = self.convert_three_view_frames(p=p_um, base_frame_name=base_frame_name,
                                                                in_plane=plane,
                                                                out_plane='sagittal',
                                                                p_resol='um')
            assert p_wrt_inSagittal_um.ndim == 2
            inSagittal_origin_wrt_wholebrain_um = self.frames[base_frame_name]['origin_wrt_wholebrain_um']
            p_wrt_wholebrain_um = p_wrt_inSagittal_um + inSagittal_origin_wrt_wholebrain_um

        return p_wrt_wholebrain_um

    def convert_frame_and_resolution(self, p, in_wrt, in_resolution, out_wrt, out_resolution,
                                     stack=None):
        """
        Converts between coordinates that are expressed in different frames and different resolutions.

        Use this in combination with DataManager.get_domain_origin().

        `wrt` can be either 3-D frames or 2-D frames.
        Detailed definitions of various frames can be found at https://goo.gl/o2Yydw.

        There are two ways to specify 3-D frames.

        1. The "absolute" way:
        - wholebrain: formed by stacking all sections of prep1 (aligned + padded) images
    - wholebrainWithMargin: tightly wrap around brain tissue. The origin is the nearest corner of the bounding box of all images' prep1 masks.
        - wholebrainXYcropped: formed by stacking all sections of prep2 images
        - brainstemXYfull: formed by stacking sections of prep1 images that contain brainstem
        - brainstem: formed by stacking brainstem sections of prep2 images
        - brainstemXYFullNoMargin: formed by stacking brainstem sections of prep4 images

        2. The "relative" way:
        - x_sagittal: frame of lo-res sagittal scene = sagittal frame of the intensity volume, with origin at the most left/rostral/dorsal position.
        - x_coronal: frame of lo-res coronal scene = coronal frame of the intensity volume, with origin at the most left/rostral/dorsal position.
        - x_horizontal: frame of lo-res horizontal scene = horizontal frame of the intensity volume, with origin at the most left/rostral/dorsal position.

        Build-in 2-D frames include:
        - {0: 'original', 1: 'alignedPadded', 2: 'alignedCroppedBrainstem', 3: 'alignedCroppedThalamus', 4: 'alignedNoMargin', 5: 'alignedWithMargin', 6: 'originalCropped'}

        Resolution specifies the physical units of the coordinate axes.
        Build-in `resolution` for 3-D coordinates can be any of these strings:
        - raw
        - down32
        - vol
        - image: gscene resolution, determined by data_feeder.resolution
        - raw_raw_index: (u in raw resolution, v in raw resolution, i in terms of data_feeder index)
        - image_image_index: (u in image resolution, v in image resolution, i in terms of data_feeder index)
        - image_image_section: (u in image resolution, v in image resolution, i in terms of section index)
        """

        sqlController = SqlController(stack)
        valid_sections = sqlController.get_valid_sections(stack, 1)

        if in_wrt == 'original' and out_wrt == 'alignedPadded':

            in_x_resol, in_y_resol, in_z_resol = in_resolution.split('_')
            assert in_x_resol == in_y_resol
            assert in_z_resol == 'section'
            in_image_resolution = in_x_resol

            out_x_resol, out_y_resol, out_z_resol = out_resolution.split('_')
            assert out_x_resol == out_y_resol
            assert out_z_resol == 'section'
            out_image_resolution = out_x_resol

            uv_um = p[..., :2] * convert_resolution_string_to_um(stack=stack, resolution=in_image_resolution)

            p_wrt_outdomain_outResol = np.zeros(p.shape)

            Ts_anchor_to_individual_section_image_resol = load_transforms(stack=stack, resolution='1um', use_inverse=True)

            different_sections = np.unique(p[:, 2])
            for sec in different_sections:
                curr_section_mask = p[:, 2] == sec
                #####TODO check this is getting the right section ###fn = metadata_cache['sections_to_filenames'][stack][sec]
                fn = valid_sections[sec]
                T_anchor_to_individual_section_image_resol = Ts_anchor_to_individual_section_image_resol[fn]
                uv_wrt_alignedPadded_um_curr_section = np.dot(T_anchor_to_individual_section_image_resol,
                                          np.c_[uv_um[curr_section_mask, :2],
                                                np.ones((np.count_nonzero(curr_section_mask),))].T).T[:, :2]

                uv_wrt_alignedPadded_outResol_curr_section = \
                uv_wrt_alignedPadded_um_curr_section / convert_resolution_string_to_um(stack=stack, resolution=out_image_resolution)

                p_wrt_outdomain_outResol[curr_section_mask] = \
                np.column_stack([uv_wrt_alignedPadded_outResol_curr_section,
                           sec * np.ones((len(uv_wrt_alignedPadded_outResol_curr_section),))])

            return p_wrt_outdomain_outResol

        elif in_wrt == 'alignedPadded' and out_wrt == 'original':


            in_x_resol, in_y_resol, in_z_resol = in_resolution.split('_')
            assert in_x_resol == in_y_resol
            assert in_z_resol == 'section'
            in_image_resolution = in_x_resol

            out_x_resol, out_y_resol, out_z_resol = out_resolution.split('_')
            assert out_x_resol == out_y_resol
            assert out_z_resol == 'section'
            out_image_resolution = out_x_resol

            uv_um = p[..., :2] * convert_resolution_string_to_um(stack=stack, resolution=in_image_resolution)

            p_wrt_outdomain_outResol = np.zeros(p.shape)

            Ts_anchor_to_individual_section_image_resol = load_transforms(stack=stack, resolution='1um', use_inverse=True)
            Ts_anchor_to_individual_section_image_resol = {fn: np.linalg.inv(T) for fn, T in Ts_anchor_to_individual_section_image_resol.items()}

            different_sections = np.unique(p[:, 2])
            for sec in different_sections:
                curr_section_mask = p[:, 2] == sec
                #####TODO check this is getting the right section ###fn = metadata_cache['sections_to_filenames'][stack][sec]
                fn = valid_sections[sec]
                ##### fn = metadata_cache['sections_to_filenames'][stack][sec]
                T_anchor_to_individual_section_image_resol = Ts_anchor_to_individual_section_image_resol[fn]
                uv_wrt_alignedPadded_um_curr_section = np.dot(T_anchor_to_individual_section_image_resol,
                                          np.c_[uv_um[curr_section_mask, :2],
                                                np.ones((np.count_nonzero(curr_section_mask),))].T).T[:, :2]

                uv_wrt_alignedPadded_outResol_curr_section = \
                uv_wrt_alignedPadded_um_curr_section / convert_resolution_string_to_um(stack=stack, resolution=out_image_resolution)

                p_wrt_outdomain_outResol[curr_section_mask] = \
                np.column_stack([uv_wrt_alignedPadded_outResol_curr_section,
                           sec * np.ones((len(uv_wrt_alignedPadded_outResol_curr_section),))])

            return p_wrt_outdomain_outResol

        else:
            p = np.array(p)
            assert p.ndim == 2
            p_wrt_wholebrain_um = self.convert_to_wholebrain_um(p, wrt=in_wrt, resolution=in_resolution)
            assert p_wrt_wholebrain_um.ndim == 2
            p_wrt_outdomain_outResol = self.convert_from_wholebrain_um(p_wrt_wholebrain_um=p_wrt_wholebrain_um, wrt=out_wrt, resolution=out_resolution)
            return p_wrt_outdomain_outResol
