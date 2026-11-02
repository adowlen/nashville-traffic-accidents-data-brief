# Independent verification ledger - Nashville traffic accidents brief (2026-11-02)

Verifier: code/verify_independent.py (Section 11 pass; implementation
shares no code with the builder - pyarrow decode of the raw snapshot
plus stdlib aggregation, and live server-side ArcGIS queries).
Run: 2026-11-02 13:37 UTC, against the 2026-11-02 snapshot
(222,903 rows) and the live layer (222,903 rows at verify time, drift
+0). Full output: data/verify_independent_output.txt.

## Result

**51 of 51 checks passed. No discrepancies. No figure corrected by
the verifier; no figure caveated beyond the caveats already in the
brief.**

## What was reproduced

- Method A (snapshot recount, 33 checks): total rows and uniqueness
  (ObjectId, Accident_Number); exactly 1 empty stub row (ObjectId 6);
  known-count rows 222,902; injury crashes 67,953; fatal crashes 865;
  people injured 95,219; people killed 926; hit-and-run Y 60,336 and
  share of known 27.07 percent; exactly-00:00 local timestamps
  17,709; 9 served precinct labels, all 6 characters or fewer; null
  precinct rows 21,217; Southeast (SOUTHE) 27,179; collision counts
  Front to Rear 65,984, ANGLE 58,377, null 13,127; pedestrian-involved
  crashes 3,330 and pedestrian fatalities 280 (HarmfulCodes tokens);
  pedalcycle-involved 530; vehicles == 0 rows 25,107; the full
  local-year table 2019-2026 on known-count rows; and the stub-only
  difference between all-rows and by-year counts (+1 in 2020, 0 in
  every other year).
- Method B (live ArcGIS server-side, 18 checks): live total, live
  sums of injuries and fatalities, live injury-crash and fatal-crash
  counts, live null-count rows (the stub, 1), live hit-and-run Y and
  share, live precinct labels/nulls/Southeast, live collision counts,
  live pedestrian and pedalcycle token counts and pedestrian
  fatalities, live vehicles == 0 rows, and live exactly-midnight
  timestamps by the server-filtered candidate method. Every live
  check matched the snapshot figures exactly (no drift at verify
  time).

## Documented limitation (from the verifier output)

A server-side per-year groupBy yields UTC years, not America/Chicago
local years, so the local-year table is verified strictly against the
snapshot (Method A24/A25), with the live total bounding any drift.
