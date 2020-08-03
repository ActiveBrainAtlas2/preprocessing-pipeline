Between "Create section limits" and "Download atlas"

- **Create intensity volume**. 
Run `./construct_intensity_volume.py DEMO998 --tb_version NtbNormalizedAdaptiveInvertedGamma --tb_resol thumbnail`

```bash
├── CSHL_volumes
│   └── DEMO998
│       └── DEMO998_wholebrainWithMargin_10.0um_intensityVolume
│           ├── DEMO998_wholebrainWithMargin_10.0um_intensityVolume.bp
│           └── DEMO998_wholebrainWithMargin_10.0um_intensityVolume_origin_wrt_wholebrain.txt
```

- **Manual rough global registration**. 
Run `DATA_ROOTDIR=/home/yuncong/brainstem/home/yuncong/demo_data ROOT_DIR=/home/yuncong/brainstem/home/yuncong/demo_data 
THUMBNAIL_DATA_ROOTDIR=/home/yuncong/brainstem/home/yuncong/demo_data python src/gui/brain_labeling_gui_v28.py DEMO998 
--img_version NtbNormalizedAdaptiveInvertedGammaJpeg`. 
Note down x and y coordinates of the center of 12N and of 3N. Also note down the z-coordinate of the midline. Coordinates 
show up when clicking on the high resolution panel while holding the space bar.

- Create `$DATA_ROOTDIR/CSHL_simple_global_registration/DEMO998_manual_anchor_points.ini` with the above information.

```bash
[DEFAULT]
x_12N=561
y_12N=204
x_3N=372
y_3N=167
z_midline=6
```

Between "download atlas" and "Download pre-trained classifiers"

- **Compute rough global registration matrix**. Run `python compute_simple_global_registration.py DEMO998 $DATA_ROOTDIR/CSHL_simple_global_registration/DEMO998_manual_anchor_points.ini`.

```bash
├── CSHL_simple_global_registration
│   ├── DEMO998_registered_atlas_structures_wrt_wholebrainXYcropped_xysecTwoCorners.json
│   └── DEMO998_T_atlas_wrt_canonicalAtlasSpace_subject_wrt_wholebrain_atlasResol.txt
