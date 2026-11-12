select round((m.ts-trace_start())/1e9,3) sec,round(m.dur/1e6,3) ms,
 (select count(*) from slice c where c.track_id=m.track_id and c.ts>=m.ts and c.ts<m.ts+m.dur and c.name='ExpNotRow#onMeasure(MessagingStyle)') rows
from slice m where m.name='NotificationChildrenContainer#onMeasure' order by m.ts;
select count(*) skippedWrites from slice where name='ShadeGroup#unchangedCount';
