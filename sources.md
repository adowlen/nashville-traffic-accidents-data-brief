# Source audit: Nashville traffic accidents brief (2026-11-02)

Every figure in brief-draft.md, traced to its derivation. Counts were
produced by code/build_stats.py and are stored in stats.json; the
independent recomputation is in data/verify_independent_output.txt
(51 of 51 checks passed); the pre-flight audit is in
data/audit_output.txt and in verification.md.

## The datasets

1. Traffic accidents (primary, only dataset used for figures)
- Name: Traffic Accidents (Traffic_Accidents_2, layer 0), Metro Nashville open data, owner NashvilleOpenData
- ArcGIS item: 1df26ca05f3f407e95ab5a4fc013eab7, endpoint confirmed through the Nashville Hub search API in the 2026-11-01 study, not a guessed URL
- Endpoint used: https://services2.arcgis.com/HdTo6HJqh92wn4D8/arcgis/rest/services/Traffic_Accidents_2/FeatureServer/0
- Pull: 2026-11-02, paginated query ordered by ObjectId at the service maxRecordCount (1,000), 222,903 records; server count confirmed with returnCountOnly before download and equal to the local count. Immutable snapshot: stack/nashville/snapshots/2026-11-02/traffic_accidents_raw.parquet (sha256 d6b244991a29178c528af4b80fbfde94344205ba5f3d973f6841f5bd1, in data/pull_log.json).
- Saved copy: the warehouse snapshot above; derived panels in data/ (by_year_panel.csv, jan_oct_by_year_panel.csv, by_precinct_panel.csv, by_collision_panel.csv, by_illumination_panel.csv, by_weather_panel.csv, zip_top10_panel.csv, intersections_top10_by_injury_panel.csv)
- Fields relied on: Date_and_Time, Number_of_Injuries, Number_of_Fatalities, Number_of_Motor_Vehicles (limits only), Hit_and_Run, Collision_Type_Description, Weather_Description, Illumination_Description, Street_Address (aggregates only), Precinct, Zip, Lat/Long (audit only), HarmfulCodes, HarmfulDescriptions (control only), ObjectId, Accident_Number
- Source documentation: Traffic Accidents Metadata v2.0 (2024-05-06), archived as data/source-metadata.pdf. One record = a reported traffic accident; source system TITAN, exported daily; the export is not an official MNPD accident report and is subject to change during investigation.

2. Decision hooks (verified from primary or named sources, 2026-11-02)
- Metro Council special meeting, Thursday, November 5, 2026, 6:30 PM: Nashville.gov news release dated October 2, 2026, "Metro Council to Meet Thursday, November 5 Due to November 3 Election", https://www.nashville.gov/departments/council/news/metro-council-meet-thursday-november-5-due-november-3-election (Metropolitan Council Office): Vice Mayor Angie E. Henderson called a special meeting for Thursday, November 5, 2026 at 6:30 PM because the November 3, 2026 general election falls on the regular meeting date; associated committee meetings are held November 4-5, 2026. The committee schedule for November 4-5 (Nashville.gov, CommitteeSchedule-11-4-11-5-2026.pdf) lists the Transportation and Infrastructure Committee on Wednesday, November 4, 2026, 4:00-4:30 PM. The brief asserts no traffic-safety item on that meeting's agenda.
- NDOT 13-intersection pedestrian signal plan: The Nashville Focal, October 22, 2026, "Nashville plans turn-on-red restrictions and pedestrian signal changes at 13 intersections", https://focalnews.org/nashville-tn/local/nashville-plans-turn-on-red-restrictions-and-pedestrian-signal-changes-at-13-intersections : NDOT plans right-turn-on-red bans at seven intersections and leading pedestrian intervals at seven others (13 intersections in total, 25th Avenue South and Children's Way receiving both), introduced over the two weeks following October 22, after Councilmember Sandra Sepulveda withdrew the related legislation on October 19. Cited in the brief for timing only; no figure derives from this article, and the brief does not present it as an NDOT primary source.
- NDOT High Injury Network program context: Nashville.gov NDOT project page (High Injury Network (HIN) Local Intersection Improvements, last updated October 26, 2026) records NDOT's Vision Zero program framing. Used for the Who can act section's program naming only; no figure derives from it.

3. Official definitions
- Collision, weather, illumination, and harmful-event code meanings: the appendices of Traffic Accidents Metadata v2.0 (item 1 above). Harmful-event codes used: 8 = PEDESTRIAN, 9 = PEDALCYCLE (Appendix D).
- Precinct full names: MNPD precinct names under the mapping in stats.json (served labels are truncated to 6 characters: CENTRA, EAST, HERMIT, MADISO, MIDTOW, NORTH, SOUTH, SOUTHE, WEST).

## Figure-by-figure audit

1. **222,903 reported crashes; window January 1, 2019 to October 31, 2026 (America/Chicago)**
   Server count = downloaded rows = 222,903. Date_and_Time (epoch ms, converted to America/Chicago) min 2019-01-01 00:00 and max 2026-10-31 19:32. stats.json: rows, coverage.

2. **Totals: 67,953 injury crashes (30.49 percent of known-count rows), 865 fatal crashes, 95,219 people injured, 926 people killed; fully-coded basis 200,695 rows, 65,245 injury crashes (32.51 percent), 862 fatal crashes, 922 fatalities**
   Severity counted on the 222,902 rows with counts populated; the 1 stub row (ObjectId 6) is excluded. Derived labels: both bases are printed wherever severity is summarized. stats.json: totals_known_counts_rows, coding_completeness.

3. **By year: 37,918 / 27,408 / 28,003 / 26,319 / 27,102 / 26,155 / 26,985 crashes and 100 / 108 / 118 / 125 / 126 / 103 / 100 fatal crashes (2019-2025); 2026 partial 23,012 crashes, 85 fatal; Jan-Oct 2026 (23,012; 85) vs Jan-Oct 2025 (22,359; 81)**
   Local-year grouping of known-count rows (the stub sits in 2020: 27,409 rows as served). stats.json: by_year, jan_oct_by_year; panel: data/by_year_panel.csv, data/jan_oct_by_year_panel.csv.

4. **Pedestrian-involved: 3,330 crashes (1.5 percent of rows), 2,984 injury (89.6 percent), 278 fatal crashes, 280 fatalities = 30.24 percent of 926. Pedalcycle-involved: 530 crashes, 485 injury (91.5 percent), 8 fatalities**
   HarmfulCodes token membership (any position in the ";"-separated list). Control: HarmfulDescriptions contains PEDESTRIAN on exactly 3,330 rows and PEDALCYCLE on 0 rows. Derived. stats.json: vulnerable_road_users.

5. **Illumination fatal-crash shares: DAYLIGHT 0.221 percent (297 of 134,199), DUSK 0.380 (15 of 3,946), DAWN 0.473 (12 of 2,538), DARK - LIGHTED 0.761 (393 of 51,640), DARK - NOT LIGHTED 1.138 (143 of 12,565); ratio about 5 to 1 (derived: 1.138 / 0.221 = 5.15)**
   Illumination_Description value groups over known-count rows; full table including unknown (null) 13,806, UNKNOWN 2,531, Dark-Unknown Lighting 1,393, OTHER 284 in stats.json: severity_by_illumination; panel: data/by_illumination_panel.csv. Complete-years-only recheck (2019-2025): 0.220 / 0.764 / 1.156 percent, recomputed at QA from the cleaned layer.

6. **Collision severity: HEAD-ON 5,544 crashes, 56.08 percent injury, 1.569 percent fatal-crash (87 fatal crashes, 106 killed); NOT COLLISION W/MOTOR VEHICLE-TRANSPORT 37,857, 36.81 percent injury, 1.345 percent fatal-crash (509 fatal crashes, 525 killed); ANGLE 58,377, 37.52 / 0.274; Front to Rear 65,984, 34.14 / 0.111 (73 fatal crashes); unknown (null) 13,126 in the severity tables (13,127 rows in the full pull), zero recorded injuries and fatalities**
   Collision_Type_Description value groups over known-count rows. stats.json: severity_by_collision_type, collision_counter_all_rows; panel: data/by_collision_panel.csv.

7. **Hit-and-run: Y 60,336 of 222,891 populated (27.07 percent); unknown 12; injury share Y 18.03 percent vs N 35.11 percent; by-year Y share 22.08 percent in 2019, then 26.40 / 28.43 / 27.91 / 29.80 / 29.34 / 27.52 / 27.15 percent (2020-2026); fully-coded-basis Y share 28.63 percent**
   Hit_and_Run value counts; the fully-coded share was recomputed at QA from the cleaned layer over the 200,684 fully-coded rows with the field populated. Derived. stats.json: hit_and_run, by_year.

8. **Precinct (known rows only): Madison 19,186 crashes, 33.59 percent injury, 97 fatal; Southeast 27,179, 33.54, 115; Hermitage 25,551, 31.37, 103; North 20,842, 30.91, 104; South 28,566, 29.79, 127; West 19,314, 29.81, 67; East 16,540, 28.84, 63; Midtown Hills 26,311, 28.45, 56; Central 18,197, 24.53, 43. Known 201,686 rows; not recorded 21,217 (9.52 percent); not-recorded share by year about 12-13 percent (2019-2023), 8.6 percent (2024), 2.4 percent (2025), 0.05 percent (2026)**
   Precinct mapped through the full-name map; shares on known rows per period, printed as cross-sectional only. stats.json: precinct; panel: data/by_precinct_panel.csv.

9. **ZIP leaders: 37013 (26,126 crashes, 104 fatal crashes), 37211 (22,805, 105)**
   Zip value groups over known-count rows. stats.json: zip_top10_by_crashes; panel: data/zip_top10_panel.csv.

10. **Intersections (normalized key): Briley Pkwy N/S 788 crashes, 269 injury crashes; Nolensville Pike / Nolensville Rd 744, 250. Junk bucket "UNKNOWN RAMP & ROAD" 1,265 rows excluded from named lists; 170,113 rows carry an intersection key**
    Street_Address normalized by sorting the two sides of " & ". Control: the two raw Briley name orders sum to the same 788 as the normalized key (identity asserted in builder and audit). Aggregates only; no address is named beyond the junction strings the layer itself serves. stats.json: intersections; panel: data/intersections_top10_by_injury_panel.csv.

11. **Time: 17,709 rows (7.94 percent) stamped exactly 00:00 local; peak hour 17:00 excluding them (205,194 known-count rows remain after the exclusion; the stub row is one of the 17,709 midnight-stamped rows, which is why the known-count exclusion removes 17,708); weekend fatal-crash share 0.545 percent vs weekday 0.336 percent**
    Hour from the America/Chicago local timestamp; midnight-suspect flag polarity asserted in the audit (all flagged rows exactly 00:00; 3,549 unflagged hour-0 rows carry real minutes). stats.json: time_of_day.

12. **Coding limits: minimally-coded rows 13,127 (collision-null set identical to the all-three-null set); hit-and-run Y 0.19 percent on minimally-coded rows vs 28.75 percent on the rest (QA recomputation; brief prints 0.2 / 28.8); HarmfulCodes null on 99.94 percent of minimally-coded rows (brief prints 99.9); vehicles 0 on 25,107 rows with the Dec 2021-Nov 2022 outage pattern in stats.json; Property Damage Y 18,676, N 1, blank 204,226 (QA recomputation from the cleaned layer)**
    stats.json: coding_completeness, vehicles, property_damage_field (the Property Damage counts in stats.json were generated by build_stats.py from the same pull and agree with the QA recomputation).

13. **Hero figure: 30.2 percent, 280 of 926**
    Item 4's derived share (280 / 926 = 30.24 percent), composited from stats.json by code/hero_composite.py; hero-headline.txt carries the same text.
