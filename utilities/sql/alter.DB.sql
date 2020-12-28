drop table if exists __file_operation;
drop table if exists raw_section;
drop table if exists section;
drop procedure if exists fix_section;
drop procedure if exists insert_previous_section;
drop view if exists sections;

create view sections AS
select
sc.id,
a.prep_id,
s.file_name as czi_file,
sc.file_name,
sc.id as tif_id,
sc.scene_number,
sc.scene_index,
sc.channel,
sc.channel - 1 as channel_index,
sc.active,
sc.created
FROM animal a
INNER JOIN scan_run sr ON a.prep_id = sr.prep_id
INNER JOIN slide s ON sr.id = s.scan_run_id
INNER JOIN slide_czi_to_tif sc ON s.id = sc.slide_id
WHERE s.slide_status = 'Good'
AND sc.active = 1
ORDER BY s.slide_physical_id, sc.scene_number, sc.channel;
