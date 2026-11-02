# Verification - Nashville traffic accidents brief (2026-11-02)

This package is the publication build of the verified 2026-11-01
shelf-ready study (hidden_files/nashville-traffic-accidents-study-2026-11-01/),
refreshed with a same-day pull on 2026-11-02. Builder pass, Section 10
pre-flight audit, and independent verifier pass (Section 11 method
diversity) were all re-run on the new snapshot in this build. Refresh
adaptation: the study code's exact-count assertions were replaced with
relationship assertions that read the expected values from the new
stats.json (identities, code-vs-description agreement, counter sums,
known + unknown = whole), so the gates test structure on the new data
rather than inheriting the 2026-11-01 counts. Every adaptation is
commented in the code files.

## Source verification (before any computation)

- Endpoint (live, queried 2026-11-02):
  `services2.arcgis.com/HdTo6HJqh92wn4D8/arcgis/rest/services/Traffic_Accidents_2/FeatureServer/0`
  ("Traffic Accidents", ArcGIS item 1df26ca05f3f407e95ab5a4fc013eab7,
  owner NashvilleOpenData), confirmed through the Nashville Hub in the
  2026-11-01 study, not a guessed URL.
- Live count at pull: **222,903** (222,842 at the 2026-11-01 study
  pull; drift +61 in one day, consistent with a daily-updated layer).
  Pulled in 223 pages of 1,000 (the service's maxRecordCount), ObjectId
  order; pulled count asserted equal to live count; ObjectId AND
  Accident_Number unique on all rows. Immutable snapshot:
  stack/nashville/snapshots/2026-11-02/traffic_accidents_raw.parquet
  (sha256 in data/pull_log.json).
- Fields as served (25): Accident_Number, Date_and_Time,
  Number_of_Motor_Vehicles, Number_of_Injuries, Number_of_Fatalities,
  Property_Damage, Hit_and_Run, Collision_Type_Description,
  Weather_Description, Illumination_Description, Street_Address, City,
  State, Precinct, Lat, Long, HarmfulCodes, HarmfulDescriptions,
  ObjectId, Zip, RPA, Weather, IlluACCIDEmination (the service's own
  mangled field name for the illumination code), Collision_Type,
  Reporting_Officer.
- Source documentation read: Traffic Accidents Metadata v2.0
  (2024-05-06, archived in this package as data/source-metadata.pdf).
  One record = a reported traffic accident; source system TITAN,
  exported daily; time period described as 2010-present (the served
  layer in fact starts 2019-01-01); "This information is not to be
  used or construed as an official MNPD accident report"; data subject
  to change during investigation and may contain erroneous
  information. Field appendices (collision, weather, illumination,
  harmful-event codes) are the code keys used for the HarmfulCodes
  token analysis.

## Headline figures (all verified below)

- 222,903 reported crashes, 2019-01-01 00:00 to 2026-10-31 19:32
  America/Chicago. Severity basis: 222,902 rows with counts populated;
  1 empty stub row (ObjectId 6; only Accident_Number, Date_and_Time,
  ObjectId served; its Accident_Number carries a 2013 prefix on a 2020
  date) is excluded from severity denominators, never from row counts.
  Yearly counts are on the known-count basis and sum to 222,902.
- Totals: 67,953 injury crashes (30.49% of known-count rows; 32.51%
  of the 200,695 fully-coded rows), 865 fatal crashes, 95,219 people
  injured, 926 people killed.
- By year (crashes / fatal crashes, known-count rows): 2019: 37,918 /
  100; 2020: 27,408 / 108 (27,409 rows as served, the stub sits in
  2020); 2021: 28,003 / 118; 2022: 26,319 / 125; 2023: 27,102 / 126;
  2024: 26,155 / 103; 2025: 26,985 / 100; 2026 partial through
  Oct 31: 23,012 / 85.
- Hit-and-run: 60,336 Y of 222,891 known (27.07%); 12 rows null.
  Fully-coded-basis Y share recomputed at QA: 28.63%.
- Pedestrian-involved (HarmfulCodes token 8): 3,330 crashes, 2,984
  injury crashes (89.6%), 278 fatal crashes, 280 fatalities = 30.24%
  of all fatalities. Pedalcycle-involved (token 9): 530 crashes,
  91.5% injury, 8 fatalities.
- Illumination fatal-crash shares: DARK - NOT LIGHTED 1.138%
  (12,565), DARK - LIGHTED 0.761% (51,640), DAYLIGHT 0.221%
  (134,199); ordering re-checked in complete years 2019-2025 alone
  on the new snapshot (0.220% / 0.764% / 1.156%).
- Time: peak hour 17:00 after excluding 17,709 exactly-00:00 rows;
  weekend fatal-crash share 0.545% vs weekday 0.336%.

## Methods checklist (brief-writing standards, section 3)

- Base rates and exposure: the layer carries no traffic-volume, VMT,
  trip, population, or street-mile denominator, by any geography or
  condition. Every figure is a count or a per-reported-crash share on
  a named population. The brief states the missing exposure
  denominator prominently in its definitions, in Finding 3, and in
  Finding 6, computes no per-mile or per-trip rate, and implies no
  causal pattern.
- Direction of causality: the illumination gradient (Finding 3) is
  framed as severity per reported crash across populations that
  differ in hour and road type, which the layer does not separate;
  the composition alternative is printed in "What this might mean."
  No infrastructure-placement claim is made in either direction.
- Category and definition changes: full Counters recorded before any
  computation (collision 11 + null, weather 14 + null, illumination
  8 + null, precinct 9 truncated labels + null; audit output). No
  rename or definition change inside the window is documented in the
  metadata. The breaks that exist are completeness breaks, printed
  where they bind: precinct not-recorded share 12-13% (2019-2023) to
  0.05% (2026); the minimally-coded subpopulation (13,127 rows); the
  vehicle-count outage (Dec 2021-Nov 2022 core window); the 2020
  weather-null gap (6,351 rows vs 1,250-3,905 in other years).
- Time windows: exact range 2019-01-01 to 2026-10-31 (America/
  Chicago) stated in the brief. 2026 is partial and compared only on
  the January-October frame (23,012 crashes / 85 fatal in Jan-Oct
  2026 vs 22,359 / 81 in Jan-Oct 2025). No plan or program comparison
  crosses a period in which it was not in effect: the NDOT signal
  measures in the Who can act section were installed from late
  October 2026, after effectively the whole window, and are framed as
  a forward evaluation baseline, not a comparison.
- Joins: no dataset join is used. Geography is the layer's own
  fields. Intersection figures aggregate the layer's own address
  strings under a sorted-token normalization, with the name-order
  control recorded below. No match-rate question arises; the
  unmatched analogue (rows without an intersection string, and the
  1,265-row junk bucket) is counted in stats.json.
- Small numbers: percentages carry counts throughout. Groups under
  about 30 are flagged: DAWN fatal crashes (12 of 2,538) and DUSK
  (15 of 3,946) are printed with counts on the chart and in the
  brief; the SMOG, SMOKE weather cell (23 crashes) carries its
  small_n flag in stats.json and the data panels and is used in no
  finding; REAR END (n = 1) is excluded from the collision chart and
  named in its footnote.
- Official definitions: collision, weather, illumination, and
  harmful-event meanings are the metadata's own appendices, cited in
  sources.md. MNPD precinct full names use the mapping recorded in
  stats.json (served labels are 6-character truncations).
- Layering admission test: no layer was added in this refresh. The
  2026-11-01 study considered and did not add a calls-for-service or
  lighting layer; the brief's claims are all makeable from the crash
  layer alone, and the lighting-condition claim the illumination
  finding points at is stated as an NDOT reporting action, not as a
  fused figure.

## Pre-flight audit

Script: code/audit_section10.py (run on the final pull, before charts
and prose were finalized). Full output (also in data/audit_output.txt):

```
rows in cleaned layer: 222903
[10.1.1] vehicles 0-sentinel rows: 25107 mapped unknown (never averaged as 0 vehicles); coords unknown 2 (1 null stub + 1 served 0,0); severity stub 1 PASS
[10.1.2] polarity: all 17709 flagged rows are exactly 00:00 local; unflagged hour-0 rows 3549 carry real minutes; hit_and_run_known Y count == served Y count 60,336 PASS
[10.1.3] injury-crash share denominator = 222902 known-count crashes, recomputed 0.3049; people totals (95,219 injuries / 926 fatalities) kept as people counts PASS
[10.1.4] Collision_Type_Description Counter: 11 values + null bucket, counts sum to 222903 PASS
[10.1.4] Weather_Description Counter: 14 values + null bucket, counts sum to 222903 PASS
[10.1.4] Illumination_Description Counter: 8 values + null bucket, counts sum to 222903 PASS
[10.1.4] Precinct Counter: 9 served labels (all <=6 chars, truncation documented) + null bucket, sums to 222903; collision Counter matches stats.json exactly PASS
[10.1.5] Precinct: known 201686 + unknown 21217 = 222903 PASS
[10.1.5] Hit_and_Run: known 222891 + unknown 12 = 222903 PASS
[10.1.5] Collision_Type_Description: known 209776 + unknown 13127 = 222903 PASS
[10.1.5] Lat: known 222901 + unknown 2 = 222903 PASS
[10.2] controls: (a) Briley junction name-order pair merges under the normalized key -> 788; (b) RPA and Precinct are jointly null on 21214 rows (one missingness mechanism); (c) pedestrian involvement agrees code-vs-description at 3,330, while pedalcycle is codes-only (530 vs 0 in descriptions) PASS
[completeness] minimally-coded rows 13127 == collision-null rows 13127, with 0 injury crashes among them (definitional, not safety); fully-coded basis 200695 crashes at 0.3251 injury share vs all-rows 0.3049 PASS
[12.3] effective window: 2019-01-01 00:00:00-06:00 to 2026-10-31 19:32:00-05:00; complete years 2019-2025, 2026 is a partial year and is compared only through the jan_oct table PASS
ALL SECTION 10 GATES PASS
```

## Internal controls (Section 10.2)

1. **Intersection normalization control.** Raw Street_Address splits
   single junctions by token order: the Briley Pkwy junction appears
   as BRILEY PKWYN & BRILEY PKWYS (439) and BRILEY PKWYS & BRILEY
   PKWYN (349) on the 2026-11-01 counts. Under the sorted-token key
   both merge to exactly 788, asserted in builder and audit on the
   new snapshot (the merged total is unchanged; the raw split was
   re-verified as an identity, raw pair total == normalized total).
2. **Geography missingness control.** RPA and Precinct are jointly
   null on 21,214 of the 21,217 precinct-null rows: one missingness
   mechanism (records that never got a reporting-area assignment),
   not two independent gaps.
3. **Harmful-code vs description control.** Pedestrian involvement
   agrees exactly between HarmfulCodes token 8 and the
   HarmfulDescriptions string (3,330 both ways), which validates the
   token method - and exposes that pedalcycle does not: token 9 on
   530 rows, the string PEDALCYCLE on 0 rows. Involvement figures
   are codes-only.
4. **Coding-completeness identity.** The collision-null set and the
   collision+weather+illumination-null set are the SAME 13,127 rows
   (collision-null with illumination known = 0 rows). That
   subpopulation records zero injuries on every known row and
   hit-and-run Y at 0.2% vs 28.8% on non-minimally-coded rows
   (recomputed at QA on the new snapshot: 0.19% vs 28.75%) - a
   separate, minimally-coded reporting path. Its zeros are
   definitional; stats.json therefore prints severity on both the
   all-reported and fully-coded bases, and every by-category table
   carries its unknown bucket.

## Independent verifier (Section 11)

Script: code/verify_independent.py (written from scratch for the
2026-11-01 study by a separate pass that never read the builder/audit
code; carried into this package with only its snapshot path and its
hit-and-run / stub-year claim derivations pointed at the new
stats.json). Full output in data/verify_independent_output.txt.
**51/51 checks pass, no discrepancies** (2026-11-02 run). Two
implementations sharing no code with the builder: (A) a pyarrow
decode of the raw snapshot aggregated with stdlib loops, Counters
and integer epoch divmod + zoneinfo for America/Chicago - rows,
uniqueness, the stub, all severity totals, hit-and-run, the 17,709
midnight timestamps, precinct labels/nulls/Southeast, collision
counts, harmful-code tokens, vehicles==0, and the full local-year
table (all-rows vs by-year differs only by the stub's +1 in 2020,
exactly as documented); (B) live server-side ArcGIS
count/statistics/groupBy queries - the live layer total at verify
time (2026-11-02 13:37 UTC) was exactly 222,903, identical to the
snapshot, so every live check passed on exact equality with zero
drift. One documented limitation, recorded in the verifier output:
a server-side per-year groupBy yields UTC years, so the local-year
table rests on the snapshot recount with the live total bounding
drift.

## QA cross-checks run during this build (beyond the trio)

Recomputed from the cleaned layer at QA time, because the brief
carries them as secondary claims: fully-coded hit-and-run Y share
28.63% (brief Finding 5); minimally-coded hit-and-run Y 0.19% vs
28.75% non-minimally-coded (brief Finding 8 prints 0.2% / 28.8%);
HarmfulCodes null on 99.94% of minimally-coded rows (brief prints
99.9%); Property Damage Y 18,676 / N 1 / blank 204,226 (brief
Finding 8; an early draft carried the study's 18,672 and was
corrected); weather null by year 2019: 3,264; 2020: 6,351; 2021:
3,905; 2022: 1,537; 2023: 2,248; 2024: 1,516; 2025: 1,500; 2026:
1,252 (brief data notes print 6,351 for 2020 and a 1,250-3,905
range for other years); illumination ordering in complete years
2019-2025 only: DAYLIGHT 0.220%, DARK - LIGHTED 0.764%, DARK - NOT
LIGHTED 1.156% (brief Finding 3). Every number in brief-draft.md
was cross-checked against the final stats.json in the same pass.

## Adversarial notes (self-check against the standards)

- **A1 No exposure denominator.** The layer has no traffic volume,
  VMT, or trip counts. Every figure is a count or a per-reported-crash
  share. Any draft language drifting toward "riskier to drive at
  night / in Madison" fails section 3; the brief's language is
  severity-per-reported-crash throughout, and the charts print the
  same limit on the graphic.
- **A2 The 2019 step-down.** Volume drops about 27% from 2019 to
  2020 and never returns, while fatal counts rise. COVID explains
  part of 2020 (the Mar-Jun 2020 monthly dip is in the data), but the
  brief's claim is deliberately limited to the two measured series;
  a reporting-mix change is carried as the strongest alternative
  explanation, unresolved.
- **A3 Severity is as-reported at export.** TITAN records change
  during investigation (metadata). The window now extends to
  Oct 31, 2026, two days before the pull, so the most recent days
  are the least settled; the Jan-Oct like-for-like frame limits,
  not eliminates, this.
- **A4 Precinct trend claims are the weakest in the package**
  because of the completeness break: a precinct's share can rise
  simply because its rows stopped being null. Brief precinct
  figures are cross-sectional (all-window, known rows) with the
  break printed in the finding and on the chart.
- **A5 Small numbers.** Weather cells like SMOG, SMOKE (23 crashes,
  fatal share 4.3%) are flagged small_n in stats.json and are never
  headline material.
- **A6 Named geography.** Intersection and ZIP figures are
  aggregates over hundreds to thousands of records, not named
  individual records; no address-level or person-level rows are
  printed anywhere in this package. Reporting_Officer and
  Street_Address raw values stay in the warehouse layer only.
- **A7 Hero and charts viewed during QA.** The hero (generated
  illustration, lit vs unlit crossing) was composited from
  stats.json by code/hero_composite.py and viewed: headline 30.2%,
  sub-line, and source line fully legible on the top scrim, scene
  unobscured. All four charts were viewed; two layout passes were
  needed (footnote clipping and label overlaps in the first render
  were fixed in code/charts.py and re-rendered, then re-viewed).

## Sync gate (section 10.3)

- README dependency list matches code imports: pull_data.py
  (requests, pandas, stdlib), build_stats.py (pandas, numpy,
  stdlib), audit_section10.py (pandas, stdlib), charts.py
  (matplotlib, stdlib), verify_independent.py (stdlib + pyarrow
  decode only), hero_composite.py (Pillow, stdlib). README lists
  exactly: Python standard library, matplotlib, numpy, pandas,
  Pillow, pyarrow, requests. No geopandas or shapely anywhere.
- Every number in brief-draft.md cross-checks against the final
  stats.json: figures were taken from stats.json at drafting, the
  secondary claims were recomputed from the cleaned layer in the QA
  pass recorded above, and the hero's text is generated from
  stats.json by code/hero_composite.py (it cannot drift from the
  stats). hero-headline.txt carries the same text.
- Review adjudication: the only review text inherited into this
  package is the 2026-11-01 study's verification record, which was
  read in full (verification.md and SHELF-READY.md) and whose
  figures were recomputed rather than inherited - the refresh's
  drift (+61 rows, +14 injury crashes, +17 people injured, fatal
  totals unchanged) is recorded above, and the one stale figure the
  QA pass caught in drafting (Property Damage Y) was corrected from
  the recomputation, not from the study text.

## Section 11.3 exception flags

- Findings touch MNPD (data owner) and NDOT levers in the Who can
  act section - no agency or official is named as a finding subject;
  the findings are about the crash population, and the coding traps
  are about the served view's fields, stated as measured facts with
  counts. This is the 2026-11-01 study's flag, carried forward.
- First use of this dataset as a published brief: flagged. (The
  dataset entered the warehouse as a study layer on 2026-11-01.)
- Surprising findings (carried from the study, unchanged on the
  refresh): the fatal-crash share ordering by illumination is
  monotone across all five coded conditions; hit-and-run crashes
  are less often injury crashes than others (18.0% vs 35.1%), the
  opposite of the direction a severity-first reading would expect.
- Nothing here touches the portfolio or any standing guardrail.
