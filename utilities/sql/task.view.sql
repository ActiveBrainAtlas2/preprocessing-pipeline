
drop view if exists task_view;

create view task_view as
select
A.prep_id, 
count(distinct PL.id)/ (select count(*) from progress_lookup) as percent_complete,
SUM(CASE WHEN T.completed = 1 THEN 1 ELSE 0 END) as complete,
DATE_FORMAT(MAX(T.created), '%b %d, %Y') as created
from animal A
left join task T on A.prep_id = T.prep_id
left join progress_lookup PL on T.lookup_id = PL.id
GROUP BY A.prep_id
;


select * from task_view;

