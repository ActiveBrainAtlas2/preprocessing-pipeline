## Database design of the base tables
This is a listing of the base tables used by the Active Brain Atlas project.
Each table has all the columns listed along with the column type and some
additional description. Columns that have never been used are marked by *NOTUSED*. 
For a graphical (ERD) view of the database, click this [diagram](database.erd.png).
### Sorting tables by name and use
### Tables used by the scheduling app
    1. `location`
    1. `location_primary_people`
    1. `schedule`
 
### Tables used by the problem reporting system for image QC
    1. `journals`
    1. `problem_category`

### Tables used by the preprocessing pipeline python logging system
    1. `logs`
### Tables used by the workflow reporting process
    1. `progress_lookup`
    1. `resource`
    1. `task`
    1. `task_resources`
    1. `task_roles`

1. All tables beginning with the `engine_` and `gitdata` prefixes 
are tables that are used by CVAT.These tables can't be updated by the programmer
 and are listed below:
    1. `engine_attributespec`
    1. `engine_clientfile`
    1. `engine_data`
    1. `engine_image`
    1. `engine_job`
    1. `engine_jobcommit`
    1. `engine_label`
    1. `engine_labeledimage`
    1. `engine_labeledimageattributeval`
    1. `engine_labeledshape`
    1. `engine_labeledshapeattributeval`
    1. `engine_labeledtrack`
    1. `engine_labeledtrackattributeval`
    1. `engine_plugin`
    1. `engine_pluginoption`
    1. `engine_project`
    1. `engine_remotefile`
    1. `engine_segment`
    1. `engine_serverfile`
    1. `engine_task`
    1. `engine_trackedshape`
    1. `engine_trackedshapeattributeval`
    1. `engine_video`
    1. `git_gitdata`

1. All tables beginning with `django_` and `auth_` 
are used by the Django database portal and
cannot be changed by the programmer and are listed below:
    1. `auth_group`
    1. `auth_group_permissions`
    1. `auth_permission`
    1. `authtoken_token`
    1. `auth_user`
    1. `auth_user_groups`
    1. `django_admin_log`
    1. `django_content_type`
    1. `django_migrations`
    1. `django_plotly_dash_dashapp`
    1. `django_plotly_dash_statelessapp`
    1. `django_session`
    1. `django_site`
1. These tables are used by the oauth login system. CVAT uses this and we
will want to make use of these in the future:
    1. `account_emailaddress`
    1. `account_emailconfirmation`
    1. `socialaccount_socialaccount`
    1. `socialaccount_socialapp`
    1. `socialaccount_socialapp_sites`
    1. `socialaccount_socialtoken`

1. Below is a list of `donkey` tables that can *probably* be deleted:
    1. `atlas_coms`
    1. `center_of_mass`
    1. `detected_soma`
    1. `foundation_coms`
    1. `md589_beth`
    1. `md589_ed`
    1. `~jobs`
    1. `layer_data_history`
    1. `~log`
    1. `row_sequence`
    1. `seq`
    1. `table_metadata`
    1. `transformation`
    1. `file_operation`

### There are two views currently being used
1. `sections`
1. `task_view`

## Below is a list of tables initially created by Yoav and David and later modified by Ed

### animal
* `prep_id` varchar(20) PRIMARY KEY NOT NULL COMMENT 'Name for lab mouse/rat, max 20 chars'
* `performance_center` enum('CSHL','Salk','UCSD','HHMI','Duke') DEFAULT NULL
* `date_of_birth` date DEFAULT NULL COMMENT 'the mouse''s date of birth'
* `species` enum('mouse','rat') DEFAULT NULL
* `strain` varchar(50) DEFAULT NULL
* `sex` enum('M','F') DEFAULT NULL COMMENT '(M/F) either ''M'' for male, ''F'' for female'
* `genotype` varchar(100) DEFAULT NULL COMMENT 'transgenic description, usually "C57"; We will need a genotype table'
* `breeder_line` varchar(100) DEFAULT NULL COMMENT 'We will need a local breeding table'
* `vender` enum('Jackson','Charles River','Harlan','NIH','Taconic') DEFAULT NULL
* `stock_number` varchar(100) DEFAULT NULL COMMENT 'if not from a performance center'
* `tissue_source` enum('animal','brain','slides') DEFAULT NULL
* `ship_date` date DEFAULT NULL
* `shipper` enum('FedEx','UPS') DEFAULT NULL
* `tracking_number` varchar(100) DEFAULT NULL
* `aliases_1` varchar(100) DEFAULT NULL COMMENT 'names given by others'
* `aliases_2` varchar(100) DEFAULT NULL
* `aliases_3` varchar(100) DEFAULT NULL *NOTUSED*
* `aliases_4` varchar(100) DEFAULT NULL *NOTUSED*
* `aliases_5` varchar(100) DEFAULT NULL *NOTUSED*
* `comments` varchar(2001) DEFAULT NULL COMMENT 'assessment'
* `active` tinyint(4) NOT NULL DEFAULT 1
* `created` timestamp NULL DEFAULT current_timestamp()

### scan_run 
* `id` int(11) PRIMARY KEY NOT NULL AUTO_INCREMENT
* `prep_id` varchar(200) NOT NULL
* `performance_center` enum('CSHL','Salk','UCSD','HHMI') DEFAULT NULL COMMENT 'default population is from Histology'
* `machine` enum('Zeiss','Axioscan','Nanozoomer','Olympus VA') DEFAULT NULL
* `objective` enum('60X','40X','20X','10X') DEFAULT NULL
* `resolution` float NOT NULL DEFAULT 0 COMMENT '(µm) lateral resolution if available'
* `zresolution` float NOT NULL DEFAULT 20
* `number_of_slides` int(11) NOT NULL DEFAULT 0
* `scan_date` date DEFAULT NULL
* `file_type` enum('CZI','JPEG2000','NDPI','NGR') DEFAULT NULL
* `scenes_per_slide` enum('1','2','3','4','5','6') DEFAULT NULL
* `section_schema` enum('L to R','R to L') DEFAULT NULL COMMENT 'agreement is one row'
* `channels_per_scene` enum('1','2','3','4') DEFAULT NULL
* `slide_folder_path` varchar(200) DEFAULT NULL COMMENT 'the path to the slides folder on birdstore (files to be converted)'
* `converted_folder_path` varchar(200) DEFAULT NULL COMMENT 'the path to the slides folder on birdstore after convertion'
* `converted_status` enum('not started','converted','converting','error') DEFAULT NULL
* `ch_1_filter_set` enum('68','47','38','46','63','64','50') DEFAULT NULL COMMENT 'This is counterstain Channel'
* `ch_2_filter_set` enum('68','47','38','46','63','64','50') DEFAULT NULL
* `ch_3_filter_set` enum('68','47','38','46','63','64','50') DEFAULT NULL
* `ch_4_filter_set` enum('68','47','38','46','63','64','50') DEFAULT NULL
* `width` int(11) NOT NULL DEFAULT 0
* `height` int(11) NOT NULL DEFAULT 0
* `rotation` int(11) NOT NULL DEFAULT 0
* `flip` enum('none','flip','flop') NOT NULL DEFAULT 'none'
* `comments` varchar(2001) DEFAULT NULL COMMENT 'assessment'
* `active` tinyint(4) NOT NULL DEFAULT 1
* `created` timestamp NULL DEFAULT current_timestamp()

### slide
* `id` int(11) PRIMARY KEY NOT NULL AUTO_INCREMENT
* `scan_run_id` int(11) NOT NULL
* `slide_physical_id` int(11) NOT NULL COMMENT 'one per slide'
* `rescan_number` enum('','1','2','3') NOT NULL DEFAULT ''
* `slide_status` enum('Bad','Good') NOT NULL DEFAULT 'Good'
* `scenes` int(11) DEFAULT NULL
* `insert_before_one` tinyint(4) NOT NULL DEFAULT 0
* `insert_between_one_two` tinyint(4) NOT NULL DEFAULT 0
* `insert_between_two_three` tinyint(4) NOT NULL DEFAULT 0
* `insert_between_three_four` tinyint(4) NOT NULL DEFAULT 0
* `insert_between_four_five` tinyint(4) NOT NULL DEFAULT 0
* `insert_between_five_six` tinyint(4) NOT NULL DEFAULT 0
* `file_name` varchar(200) NOT NULL
* `comments` varchar(2001) DEFAULT NULL COMMENT 'assessment'
* `active` tinyint(4) NOT NULL DEFAULT 1
* `created` timestamp NULL DEFAULT current_timestamp()
* `file_size` float NOT NULL DEFAULT 0
* `processing_duration` float NOT NULL DEFAULT 0
* `processed` tinyint(4) NOT NULL DEFAULT 0
* `scene_qc_1` tinyint(4) NOT NULL DEFAULT 0
* `scene_qc_2` tinyint(4) NOT NULL DEFAULT 0
* `scene_qc_3` tinyint(4) NOT NULL DEFAULT 0
* `scene_qc_4` tinyint(4) NOT NULL DEFAULT 0
* `scene_qc_5` tinyint(4) NOT NULL DEFAULT 0
* `scene_qc_6` tinyint(4) NOT NULL DEFAULT 0


### slide_czi_to_tif 
* `id` int(11) PRIMARY KEY NOT NULL AUTO_INCREMENT
* `slide_id` int(11) NOT NULL
* `file_name` varchar(200) NOT NULL
* `scene_number` tinyint(4) NOT NULL
* `channel` tinyint(4) NOT NULL
* `width` int(11) NOT NULL DEFAULT 0
* `height` int(11) NOT NULL DEFAULT 0
* `comments` varchar(2000) DEFAULT NULL COMMENT 'assessment'
* `active` tinyint(4) NOT NULL DEFAULT 1
* `created` timestamp NULL DEFAULT current_timestamp()
* `file_size` float NOT NULL DEFAULT 0
* `scene_index` int(11) NOT NULL DEFAULT 0
* `processing_duration` float NOT NULL DEFAULT 0

### histology
* `id` int(11) PRIMARY KEY NOT NULL AUTO_INCREMENT
* `prep_id` varchar(20) NOT NULL
* `virus_id` int(11) DEFAULT NULL
* `label_id` int(11) DEFAULT NULL
* `performance_center` enum('CSHL','Salk','UCSD','HHMI') DEFAULT NULL COMMENT 'default population is from Injection'
* `anesthesia` enum('ketamine','isoflurane','pentobarbital','fatal plus') DEFAULT NULL
* `perfusion_age_in_days` tinyint(3) unsigned NOT NULL DEFAULT 0
* `perfusion_date` date DEFAULT NULL
* `exsangination_method` enum('PBS','aCSF','Ringers') DEFAULT NULL
* `fixative_method` enum('Para','Glut','Post fix') DEFAULT NULL
* `special_perfusion_notes` varchar(200) DEFAULT NULL
* `post_fixation_period` tinyint(3) unsigned NOT NULL DEFAULT 0 COMMENT '(days)'
* `whole_brain` enum('Y','N') DEFAULT NULL
* `block` varchar(200) DEFAULT NULL COMMENT 'if applicable'
* `date_sectioned` date DEFAULT NULL
* `side_sectioned_first` enum('ASC','DESC') NOT NULL DEFAULT 'ASC'
* `sectioning_method` enum('cryoJane','cryostat','vibratome','optical','sliding microtiome') DEFAULT NULL
* `section_thickness` tinyint(3) unsigned NOT NULL DEFAULT 20 COMMENT '(µm)'
* `orientation` enum('coronal','horizontal','sagittal','oblique') DEFAULT NULL
* `oblique_notes` varchar(200) DEFAULT NULL
* `mounting` enum('every section','2nd','3rd','4th','5ft','6th') DEFAULT NULL COMMENT 'used to automatically populate Placeholder'
* `counterstain` enum('thionin','NtB','NtFR','DAPI','Giemsa','Syto41') DEFAULT NULL
* `comments` varchar(2001) DEFAULT NULL COMMENT 'assessment'
* `created` timestamp NOT NULL DEFAULT current_timestamp()
* `active` tinyint(4) NOT NULL DEFAULT 1

### organic_label *this table is not being used at all*
* `id` int(11) PRIMARY KEY NOT NULL AUTO_INCREMENT
* `label_id` varchar(20) NOT NULL
* `label_type` enum('Cascade Blue','Chicago Blue','Alexa405','Alexa488','Alexa647','Cy2','Cy3','Cy5','Cy5.5','Cy7','Fluorescein','Rhodamine B','Rhodamine 6G','Texas Red','TMR') DEFAULT NULL
* `type_lot_number` varchar(20) DEFAULT NULL
* `type_tracer` enum('BDA','Dextran','FluoroGold','DiI','DiO') DEFAULT NULL
* `type_details` varchar(500) DEFAULT NULL
* `concentration` float NOT NULL DEFAULT 0 COMMENT '(µM) if applicable'
* `excitation_1p_wavelength` int(11) NOT NULL DEFAULT 0 COMMENT '(nm)'
* `excitation_1p_range` int(11) NOT NULL DEFAULT 0 COMMENT '(nm)'
* `excitation_2p_wavelength` int(11) NOT NULL DEFAULT 0 COMMENT '(nm)'
* `excitation_2p_range` int(11) NOT NULL DEFAULT 0 COMMENT '(nm)'
* `lp_dichroic_cut` int(11) NOT NULL DEFAULT 0 COMMENT '(nm)'
* `emission_wavelength` int(11) NOT NULL DEFAULT 0 COMMENT '(nm)'
* `emission_range` int(11) NOT NULL DEFAULT 0 COMMENT '(nm)'
* `label_source` enum('','Invitrogen','Sigma','Thermo-Fisher') DEFAULT NULL
* `source_details` varchar(100) DEFAULT NULL
* `comments` varchar(2000) DEFAULT NULL COMMENT 'assessment'
* `created` timestamp NOT NULL DEFAULT current_timestamp()
* `active` tinyint(4) NOT NULL DEFAULT 1

### injection
* `id` int(11) PRIMARY KEY NOT NULL AUTO_INCREMENT
* `prep_id` varchar(200) NOT NULL
* `label_id` int(11) DEFAULT NULL
* `performance_center` enum('CSHL','Salk','UCSD','HHMI','Duke') DEFAULT NULL
* `anesthesia` enum('ketamine','isoflurane') DEFAULT NULL
* `method` enum('iontophoresis','pressure','volume') DEFAULT NULL
* `injection_volume` float NOT NULL DEFAULT 0 COMMENT '(nL)'
* `pipet` enum('glass','quartz','Hamilton','syringe needle') DEFAULT NULL
* `location` varchar(20) DEFAULT NULL COMMENT 'examples: muscle, brain region'
* `angle` varchar(20) DEFAULT NULL
* `brain_location_dv` float NOT NULL DEFAULT 0 COMMENT '(mm) dorsal-ventral relative to Bregma'
* `brain_location_ml` float NOT NULL DEFAULT 0 COMMENT '(mm) medial-lateral relative to Bregma; check if positive'
* `brain_location_ap` float NOT NULL DEFAULT 0 COMMENT '(mm) anterior-posterior relative to Bregma'
* `injection_date` date DEFAULT NULL
* `transport_days` int(11) NOT NULL DEFAULT 0
* `virus_count` int(11) NOT NULL DEFAULT 0
* `comments` varchar(2001) DEFAULT NULL COMMENT 'assessment'
* `created` timestamp NOT NULL DEFAULT current_timestamp()
* `active` tinyint(4) NOT NULL DEFAULT 1

### injection_virus
* `id` int(11) PRIMARY KEY NOT NULL AUTO_INCREMENT
* `injection_id` int(11) NOT NULL
* `virus_id` int(11) NOT NULL
* `created` timestamp NOT NULL DEFAULT current_timestamp()
* `active` tinyint(4) NOT NULL DEFAULT 1

### virus
* `id` int(11) PRIMARY KEY NOT NULL AUTO_INCREMENT
* `virus_name` varchar(50) NOT NULL
* `virus_type` enum('Adenovirus','AAV','CAV','DG rabies','G-pseudo-Lenti','Herpes','Lenti','N2C rabies','Sinbis') DEFAULT NULL
* `virus_active` enum('yes','no') DEFAULT NULL
* `type_details` varchar(500) DEFAULT NULL
* `titer` float NOT NULL DEFAULT 0 COMMENT '(particles/ml) if applicable'
* `lot_number` varchar(20) DEFAULT NULL
* `label` enum('YFP','GFP','RFP','histo-tag') DEFAULT NULL
* `label2` varchar(200) DEFAULT NULL
* `excitation_1p_wavelength` int(11) NOT NULL DEFAULT 0 COMMENT '(nm) if applicable'
* `excitation_1p_range` int(11) NOT NULL DEFAULT 0 COMMENT '(nm) if applicable'
* `excitation_2p_wavelength` int(11) NOT NULL DEFAULT 0 COMMENT '(nm) if applicable'
* `excitation_2p_range` int(11) NOT NULL DEFAULT 0 COMMENT '(nm) if applicable'
* `lp_dichroic_cut` int(11) NOT NULL DEFAULT 0 COMMENT '(nm) if applicable'
* `emission_wavelength` int(11) NOT NULL DEFAULT 0 COMMENT '(nm) if applicable'
* `emission_range` int(11) NOT NULL DEFAULT 0 COMMENT '(nm) if applicable0'
* `virus_source` enum('Adgene','Salk','Penn','UNC') DEFAULT NULL
* `source_details` varchar(100) DEFAULT NULL
* `comments` varchar(2000) DEFAULT NULL COMMENT 'assessment'
* `created` timestamp NOT NULL DEFAULT current_timestamp()
* `active` tinyint(4) NOT NULL DEFAULT 1

## Tables specifically related to Neuroglancer metadata
### layer_data 
* `id` int(11) PRIMARY KEY NOT NULL AUTO_INCREMENT
* `prep_id` varchar(20) NOT NULL
* `structure_id` int(11) NOT NULL
* `person_id` int(11) NOT NULL
* `updated_by` int(11) DEFAULT NULL
* `input_type_id` int(11) NOT NULL DEFAULT 1
* `vetted` enum('yes','no') DEFAULT NULL
* `layer` varchar(255) DEFAULT NULL,
* `x` float DEFAULT NULL
* `y` float DEFAULT NULL
* `section` float NOT NULL DEFAULT 0
* `active` tinyint(1) DEFAULT NULL
* `created` datetime(6) NOT NULL
* `updated` timestamp NOT NULL DEFAULT current_timestamp()

### structure 
* `id` int(11) PRIMARY KEY NOT NULL AUTO_INCREMENT
* `abbreviation` varchar(25) COLLATE utf8_bin NOT NULL
* `description` longtext COLLATE utf8_bin NOT NULL
* `color` int(11) NOT NULL DEFAULT 100
* `hexadecimal` char(7) COLLATE utf8_bin DEFAULT NULL
* `active` tinyint(1) NOT NULL
* `created` datetime(6) NOT NULL

### com_type 
* `id` int(11) PRIMARY KEY NOT NULL AUTO_INCREMENT
* `input_type` varchar(50) NOT NULL
* `description` varchar(255) DEFAULT NULL
* `active` tinyint(1) NOT NULL DEFAULT 1
* `created` datetime(6) NOT NULL
* `updated` timestamp NOT NULL DEFAULT current_timestamp()

### neuroglancer_urls
* `id` int(11) PRIMARY KEY NOT NULL AUTO_INCREMENT
* `person_id` int(11) DEFAULT NULL
* `url` longtext NOT NULL
* `active` tinyint(1) DEFAULT NULL
* `vetted` tinyint(1) DEFAULT NULL
* `created` datetime(6) NOT NULL
* `user_date` varchar(25) DEFAULT NULL
* `comments` varchar(255) DEFAULT NULL
* `updated` timestamp NOT NULL DEFAULT current_timestamp()




* `elastix_transformation`
* `file_log`

