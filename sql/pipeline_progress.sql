
drop view if exists chart_view;

drop table if exists chart_resource;                     
drop table if exists chart_roles;                    
drop table if exists chart_task_resources;               
drop table if exists chart_task;              
drop table if exists chart_schedule;                     
DROP TABLE IF EXISTS `task_resources`;
DROP TABLE IF EXISTS `task`;




DROP TABLE IF EXISTS `progress_lookup`;
CREATE TABLE `progress_lookup` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `description` text DEFAULT NULL,
  `script` varchar(200) DEFAULT NULL,
  `active` tinyint(4) NOT NULL DEFAULT 1,
  `created` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;




insert into progress_lookup (id, description, script, active, created) 
values (10,'Slides are scanned',  '', 1, now());

insert into progress_lookup (id, description, script, active, created) 
values (20,'CZI files are placed on birdstore',  '', 1, now());

insert into progress_lookup (id, description, script, active, created) 
values (30,'CZI files are scanned to get metadata',  'main.py', 1, now());

insert into progress_lookup (id, description, script, active, created) 
values (40,'QC is done on slides in web admin',  '', 1, now());

insert into progress_lookup (id, description, script, active, created) 
values (50,'CZI files are converted into numbered TIFs for channel 1',  'create_tifs.py', 1, now());

insert into progress_lookup (id, description, script, active, created) 
values (60,'Create channel 1 thumbnails',  'create_thumbnails.py', 1, now());

insert into progress_lookup (id, description, script, active, created) 
values (70,'Create channel 1 histograms',  'create_histogram.py', 1, now());

-- create masks
insert into progress_lookup (id, description, script, active, created) 
values (80,'Create thumbnail masks',  'create_masks.py', 1, now());

-- clean with masks
insert into progress_lookup (id, description, script, active, created) 
values (90,'Clean channel 1 thumbnail with mask',  'clean_with_mask.py', 1, now());


-- align
insert into progress_lookup (id, description, script, active, created) 
values (100,'Align channel 1 thumbnails with elastix',  'alignment.py', 1, now());

-- neuroglancer precompute
insert into progress_lookup (id, description, script, active, created) 
values (110,'Create neuroglancer tiles channel 1 thumbnails',  'precompute_images_local.py', 1, now());

-- ----------------------

-- full res stuff
insert into progress_lookup (id, description, script, active, created) 
values (120,'Create full res masks',  'create_masks.py', 1, now());

insert into progress_lookup (id, description, script, active, created) 
values (130,'Create channel 2 full res',  'create_tifs.py', 1, now());

insert into progress_lookup (id, description, script, active, created) 
values (140,'Create channel 2 thumbnails',  'create_thumbnails.py', 1, now());

insert into progress_lookup (id, description, script, active, created) 
values (150,'Create channel 2 histograms',  'create_histogram.py', 1, now());

insert into progress_lookup (id, description, script, active, created) 
values (160,'Create channel 3 full res',  'create_tifs.py', 1, now());

insert into progress_lookup (id, description, script, active, created) 
values (170,'Create channel 3 thumbnails',  'create_thumbnails.py', 1, now());

insert into progress_lookup (id, description, script, active, created) 
values (180,'Create channel 3 histograms',  'create_histogram.py', 1, now());


insert into progress_lookup (id, description, script, active, created) 
values (185,'Clean channel 1 full res with mask',  'clean_with_mask.py', 1, now());

insert into progress_lookup (id, description, script, active, created) 
values (190,'Clean channel 2 full res with mask',  'clean_with_mask.py', 1, now());

insert into progress_lookup (id, description, script, active, created) 
values (200,'Clean channel 3 full res with mask',  'clean_with_mask.py', 1, now());


insert into progress_lookup (id, description, script, active, created) 
values (209,'Align channel 1 full res',  'alignment.py', 1, now());

insert into progress_lookup (id, description, script, active, created) 
values (210,'Align channel 2 full res',  'alignment.py', 1, now());

insert into progress_lookup (id, description, script, active, created) 
values (220,'Align channel 3 full res',  'alignment.py', 1, now());

insert into progress_lookup (id, description, script, active, created) 
values (225,'Run precompute neuroglancer channel 1 full res',  'precompute_images_local.py', 1, now());

insert into progress_lookup (id, description, script, active, created) 
values (230,'Run precompute neuroglancer channel 2 full res',  'precompute_images_local.py', 1, now());

insert into progress_lookup (id, description, script, active, created) 
values (240,'Run precompute neuroglancer channel 3 full res',  'precompute_images_local.py', 1, now());




CREATE TABLE `task` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `lookup_id` int(11) NOT NULL,
  `prep_id` varchar(20) NOT NULL,
  `completed` tinyint(4) NOT NULL DEFAULT 0,
  `start_date` datetime DEFAULT NULL,
  `end_date` datetime DEFAULT NULL,
  `active` tinyint(4) NOT NULL DEFAULT 1,
  `created` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `UK__progress_data_prep_lookup` (`prep_id`,`lookup_id`),
  KEY `K__task_prep_id` (`prep_id`),
  KEY `K__task_data_lookup_id` (`lookup_id`),
  CONSTRAINT `FK__task_lookup_id` FOREIGN KEY (`lookup_id`) REFERENCES `progress_lookup` (`id`),
  CONSTRAINT `FK__task_prep_id` FOREIGN KEY (`prep_id`) REFERENCES `animal` (`prep_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


CREATE TABLE `task_resources` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `task_id` int(11) NOT NULL,
  `resource_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `UK__TR_task_id` (`task_id`,`resource_id`),
  KEY `K__TR_resource_id` (`resource_id`),
  CONSTRAINT `FK__TR_resource_id` FOREIGN KEY (`resource_id`) REFERENCES `resource` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `FK__TR_task_id` FOREIGN KEY (`task_id`) REFERENCES `task` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;


-- insert tasks
-- scanned
insert into task (lookup_id, prep_id,completed,start_date,end_date,active) values (10, 'DK39',1,now(), now(), 1);
insert into task (lookup_id, prep_id,completed,start_date,end_date,active) values (10, 'DK43',1,now(), now(), 1);
insert into task (lookup_id, prep_id,completed,start_date,end_date,active) values (10, 'DK52',1,now(), now(), 1);
insert into task (lookup_id, prep_id,completed,start_date,end_date,active) values (10, 'MD589',1,now(), now(), 1);
insert into task (lookup_id, prep_id,completed,start_date,end_date,active) values (10, 'MD585',1,now(), now(), 1);
-- put on birdstore
insert into task (lookup_id, prep_id,completed,start_date,end_date,active) values (20, 'DK39',1,now(), now(), 1);
insert into task (lookup_id, prep_id,completed,start_date,end_date,active) values (20, 'DK43',1,now(), now(), 1);
insert into task (lookup_id, prep_id,completed,start_date,end_date,active) values (20, 'DK52',1,now(), now(), 1);
insert into task (lookup_id, prep_id,completed,start_date,end_date,active) values (20, 'MD589',1,now(), now(), 1);
insert into task (lookup_id, prep_id,completed,start_date,end_date,active) values (20, 'MD585',1,now(), now(), 1);
-- metadata
insert into task (lookup_id, prep_id,completed,start_date,end_date,active) values (30, 'DK39',1,now(), now(), 1);
insert into task (lookup_id, prep_id,completed,start_date,end_date,active) values (30, 'DK43',1,now(), now(), 1);
insert into task (lookup_id, prep_id,completed,start_date,end_date,active) values (30, 'DK52',1,now(), now(), 1);
insert into task (lookup_id, prep_id,completed,start_date,end_date,active) values (30, 'MD589',1,now(), now(), 1);
insert into task (lookup_id, prep_id,completed,start_date,end_date,active) values (30, 'MD585',1,now(), now(), 1);
-- Inital QC
insert into task (lookup_id, prep_id,completed,start_date,end_date,active) values (40, 'DK39',1,now(), now(), 1);
insert into task (lookup_id, prep_id,completed,start_date,end_date,active) values (40, 'DK43',1,now(), now(), 1);
insert into task (lookup_id, prep_id,completed,start_date,end_date,active) values (40, 'DK52',1,now(), now(), 1);
insert into task (lookup_id, prep_id,completed,start_date,end_date,active) values (40, 'MD585',1,now(), now(), 1);
insert into task (lookup_id, prep_id,completed,start_date,end_date,active) values (40, 'MD589',1,now(), now(), 1);
