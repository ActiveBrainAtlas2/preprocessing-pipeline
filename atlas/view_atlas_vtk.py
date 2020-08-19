from ast import literal_eval
import numpy as np
import pandas as pd
import os, sys

HOME = os.path.expanduser("~")
DIR = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(DIR)
from utilities.utilities_view import load_meshes_v2, actor_mesh, load_mesh_v2, rescale_polydata, actor_sphere, launch_vtk

HOME = os.path.expanduser("~")

PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.imported_atlas_utilities import load_original_volume_v2, volume_to_polydata, \
    VOL_DIR, mesh_to_polydata, load_data, load_alignment_results_v3, transform_points


# Set this to true if want to show a largest possible SNR_L with the lowest possible level.
#use_big_snr_l = True
use_big_snr_l = True
render_config_atlas_path = 'render_config_atlas.csv'
experiments_path = 'lauren_experiments.csv'
render_config_atlas = pd.read_csv(render_config_atlas_path, index_col='name').to_dict()
render_config_atlas['color'] = {s: eval(c) for s, c in render_config_atlas['color'].items()}
render_config_atlas['level'] = {s: float(l) for s, l in render_config_atlas['level'].items()}

# atlas_spec = load_json(args.fixed_brain_spec)
# brain_m_spec = load_json(args.moving_brain_spec)
# registration_setting = args.registration_setting
# use_simple_global = args.use_simple_global

experiments = pd.read_csv(experiments_path, index_col=0).T.to_dict()

atlas_name = 'atlasV7'
atlas_spec = dict(name=atlas_name, resolution='10.0um', vol_type='score')

####################################

atlas_meshes_10um = load_meshes_v2(atlas_spec, sided=True, return_polydata_only=False,
                                               include_surround=False, level=0.9)
atlas_meshes_um = {s: mesh_to_polydata(vertices=v*10., faces=f) for s, (v, f) in atlas_meshes_10um.items()}

if use_big_snr_l:
    SNR_L_vol_10um, SNR_L_origin_10um_wrt_canonicalAtlasSpace = load_original_volume_v2(stack_spec=atlas_spec,
                                                                                        structure='SNR_L',
                                                                                        bbox_wrt='canonicalAtlasSpace')

#SNR_R_vol_10um, SNR_R_ori_10um_wrt_canonicalAtlasSpace =\
#DataManager.load_original_volume_v2(stack_spec=atlas_spec, structure='SNR_R', bbox_wrt='canonicalAtlasSpace')
#SNR_L_nominal_location_1um_wrt_canonicalAtlasSpace = load_data(DataManager.get_structure_mean_positions_filepath(atlas_name=atlas_name, resolution='1um'))['SNR_L']
#SNR_L_nominal_location_10um_wrt_canonicalAtlasSpace = SNR_L_nominal_location_1um_wrt_canonicalAtlasSpace / 10.
#SNR_L_vol_10um, SNR_L_origin_10um_wrt_canonicalAtlasSpace = \
#mirror_volume_v2(SNR_R_vol_10um, SNR_L_nominal_location_10um_wrt_canonicalAtlasSpace)

    level = 0.000001
    num_simplify_iter = 4

    SNR_L_mesh_level01_vertices_10um, SNR_L_mesh_level01_faces = \
volume_to_polydata(volume=(SNR_L_vol_10um, SNR_L_origin_10um_wrt_canonicalAtlasSpace),
                   level=level,
                     num_simplify_iter=num_simplify_iter,
                     smooth=True,
                     return_vertex_face_list=True)

    SNR_L_mesh_level01_um = mesh_to_polydata(vertices=SNR_L_mesh_level01_vertices_10um * 10.,
faces=SNR_L_mesh_level01_faces)

    atlas_meshes_um['SNR_L'] = SNR_L_mesh_level01_um

atlas_structure_actors_um = {s: actor_mesh(m,
                       color=np.array(render_config_atlas['color'][s])/255.,
                                           opacity=render_config_atlas['opacity'][s],
                                    )
            for s, m in atlas_meshes_um.items()}

shell_polydata_10um_wrt_canonicalAtlasSpace = load_mesh_v2(brain_spec=dict(name=atlas_name, vol_type='score', resolution='10.0um'),
                                                                   structure='shell')

shell_polydata_um_wrt_canonicalAtlasSpace = rescale_polydata(shell_polydata_10um_wrt_canonicalAtlasSpace, 10.)

shell_actor_um_wrt_canonicalAtlasSpace = actor_mesh(shell_polydata_um_wrt_canonicalAtlasSpace, (1,1,1), opacity=.1,
                              wireframe=False)

marker_resolution = '10.0um'

markers_rel2atlas_actors = {}
aligned_markers_rel2atlas_um_all_brains = {}

for brain_name, experiment_info in experiments.items():
    # Load Neurolucida format.
    #def get_lauren_markers_filepath(stack, structure, resolution):
    #    return os.path.join(ROOT_DIR, 'lauren_data', 'markers', stack, stack + '_markers_%s_%s.npy' % (resolution, structure))

    #markers_path = get_lauren_markers_filepath(brain_name, structure='All', resolution=marker_resolution)
    markers_path = os.path.join(VOL_DIR, 'lauren_data', 'markers', brain_name + '_markers_%s_%s.npy' % (marker_resolution, 'All'))
    markers = load_data(markers_path, filetype="npy")

    #sample_n = min(len(markers), max(len(markers)/5, 10))	# Choice: sample 20% of each experiment but at least 10 markers
    sample_n = min(len(markers), 200) 	# Choice: randomly sample 50 markers for each experiment
    #sample_n = len(markers)		# Choice: show all markers
    print(brain_name, 'showing', sample_n, '/', len(markers))
    markers = markers[np.random.choice(list(range(len(markers))), size=sample_n, replace=False)]

    brain_f_spec = dict(name=brain_name, vol_type='annotationAsScore', structure='SNR_L', resolution='10.0um')
    brain_m_spec = dict(name=atlas_name, resolution='10.0um', vol_type='score', structure='SNR_L')
    alignment_spec = dict(stack_m=brain_m_spec, stack_f=brain_f_spec, warp_setting=7)
    print(alignment_spec)
    tf_atlas_to_subj = load_alignment_results_v3(alignment_spec, what='parameters', out_form=(4,4))

    markers_rel2subj = {marker_id: marker_xyz for marker_id, marker_xyz in enumerate(markers)}

    aligned_markers_rel2atlas = {marker_ind: transform_points(pts=p, transform=np.linalg.inv(tf_atlas_to_subj))
                                for marker_ind, p in markers_rel2subj.items()}

    aligned_markers_rel2atlas_um = {marker_ind: p * 10.0
                                    for marker_ind, p in aligned_markers_rel2atlas.items()}

    aligned_markers_rel2atlas_um_all_brains[brain_name] = aligned_markers_rel2atlas_um

    markers_rel2atlas_actors[brain_name] = [actor_sphere(position=(x,y,z), radius=20,
                                                        color=literal_eval(experiment_info['marker_color']),
                                                        opacity=.6 )
                               for marker_id, (x,y,z) in aligned_markers_rel2atlas_um.items()]


#print('markers_rel2atlas_actors.items()', markers_rel2atlas_actors.items())
l_atlas_structure_actors_um = list(atlas_structure_actors_um.values())

actor1 = [m for b, marker_actors in markers_rel2atlas_actors.items() for m in marker_actors ]
actor2 = l_atlas_structure_actors_um
actor3 = [shell_actor_um_wrt_canonicalAtlasSpace]
actor4 = [actor_sphere(position=(0,0,0), radius=5, color=(1,1,1), opacity=1.)]
actors = actor1 + actor2 + actor3 + actor4
# init_angle='horizontal_topDown'
# init_angle='coronal_posteriorToAnterior'
#init_angle='sagittal'
launch_vtk(actors, init_angle='45', window_name='Hey you', window_size=None,
            interactive=True, snapshot_fn=None, snapshot_magnification=1,
            axes=True, background_color=(0,0,0), axes_label_color=(1,1,1),
            animate=False, movie_fp=None, framerate=10,
              view_up=None, position=None, focal=None, distance=1, depth_peeling=True)

