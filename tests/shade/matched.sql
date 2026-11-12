with m as (select ts,dur from slice where name='NotificationChildrenContainer#onMeasure' and dur>0), r as (select ts,dur from slice where name='ShadeListBuilder.buildList' and dur>0), last as (select ts from slice where name='ExpNotRow#onNotifUpdated (leaf)')
select round((m.ts-trace_start())/1e9,3) sec, round(m.dur/1e6,3) ms,
 exists(select 1 from last l join r on r.ts>l.ts and r.ts<l.ts+80000000 where m.ts>=r.ts+r.dur and m.ts<r.ts+r.dur+4000000) after_leaf_list,
(select count(*) from slice x where x.name='ShadeGroup#unchangedCount') skips from m order by m.ts