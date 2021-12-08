# A listing of all tables in the active_atlas_production database
This is a listing of all tables used by the Active Brain Atlas project.

### Brain tables
1. `animal`
1. `scan_run` 
1. `slide`
1. `slide_czi_to_tif` 
1. `histology`
1. `organic_label` *this table is not being used at all*
1. `injection`
1. `injection_virus`
1. `virus`

## Tables specifically related to Neuroglancer metadata
1. `layer_data` 
1. `structure`
1. `com_type`
1. `neuroglancer_urls`
1. `elastix_transformation`
1. `file_log`
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

### Tables used by CVAT
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

### Tables used by the Django portal
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
    
### Tables used by oauth system
1. `account_emailaddress`
1. `account_emailconfirmation`
1. `socialaccount_socialaccount`
1. `socialaccount_socialapp`
1. `socialaccount_socialapp_sites`
1. `socialaccount_socialtoken`

### Rogue tables
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

