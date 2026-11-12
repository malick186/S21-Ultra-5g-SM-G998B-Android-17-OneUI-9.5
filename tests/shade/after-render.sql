with a as (select s.* from slice s where s.name='ShadeListBuilder.buildList' and exists (select 1 from slice l where l.track_id=s.track_id and l.name='ExpNotRow#onNotifUpdated (leaf)' and s.ts between l.ts+l.dur and l.ts+l.dur+30000000))
select round((a.ts-trace_start())/1e9,3) t,round(a.dur/1e6,3) list_ms,
(select round(sum(x.dur)/1e6,3) from slice x where x.name='RenderStageManager.dispatchOnAfterRenderGroups' and x.track_id=a.track_id and x.ts>=a.ts and x.ts<a.ts+a.dur) group_callbacks_ms,
(select count(*) from slice x where x.name='ShadeGroup#unchangedCount' and x.track_id=a.track_id and x.ts>=a.ts and x.ts<a.ts+a.dur) skips,
(select round(m.dur/1e6,3) from slice m where m.name='NotificationChildrenContainer#onMeasure' and m.track_id=a.track_id and m.ts>=a.ts+a.dur and m.ts<a.ts+a.dur+4000000 order by m.ts limit 1) following_measure_ms from a order by a.ts;
