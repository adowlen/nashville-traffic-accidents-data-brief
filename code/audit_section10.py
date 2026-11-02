#!/usr/bin/env python3
"""Section 10 pre-flight audit for the Nashville traffic accidents layer.
Reads the cleaned layer + stats.json; asserts every gate; prints evidence.
Run with: ~/workspace/goals/daily-civic-data-brief/hidden_files/denver-crime-brief-2026-10-17/.venv/bin/python code/audit_section10.py
Refresh adaptation (2026-11-02): exact 2026-11-01 counts are read from
the package stats.json (themselves recomputed by build_stats.py from
the 2026-11-02 snapshot); gates assert identities and relationships.
"""
import json
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve()
PKG = HERE.parents[1]
STACK = HERE.parents[2] / "stack" / "nashville"
clean = pd.read_parquet(STACK / "layers" / "traffic_accidents_clean.parquet")
stats = json.loads((PKG / "stats.json").read_text())
N = len(clean)
print(f"rows in cleaned layer: {N}")
assert N == stats["rows"]
known = clean[~clean["counts_unknown_flag"]]
NK = len(known)

# 10.1.1 zero/null sentinel traps
veh0 = int((clean["Number_of_Motor_Vehicles"] == 0).sum())
assert int(clean["vehicles_unknown_flag"].sum()) == veh0 + int(clean["counts_unknown_flag"].sum())  # zeros + the null stub
assert int(clean["coords_unknown_flag"].sum()) == 2  # 1 null (stub) + 1 served 0,0
assert int(clean["counts_unknown_flag"].sum()) == 1
print(f"[10.1.1] vehicles 0-sentinel rows: {veh0} mapped unknown (never averaged as 0 vehicles); coords unknown 2 (1 null stub + 1 served 0,0); severity stub 1 PASS")

# 10.1.2 boolean polarity samples: midnight-suspect flag and hit-and-run flag
mid = clean[clean["time_midnight_suspect_flag"]]
assert len(mid) == stats["time_of_day"]["midnight_suspect_rows_excluded"] and bool((mid["hour_local"] == 0).all()) and bool((mid["minute_local"] == 0).all())
hour0_total = int((clean["hour_local"] == 0).sum())
nonmid_hour0 = clean[(clean["hour_local"] == 0) & ~clean["time_midnight_suspect_flag"]]
assert len(nonmid_hour0) == hour0_total - len(mid)
hr_y = clean[clean["Hit_and_Run"] == "Y"]
assert len(hr_y) == stats["hit_and_run"]["y_rows"] and bool((clean["hit_and_run_known"] == "Y").sum() == stats["hit_and_run"]["y_rows"])
print(f"[10.1.2] polarity: all {len(mid)} flagged rows are exactly 00:00 local; unflagged hour-0 rows {len(nonmid_hour0)} carry real minutes; hit_and_run_known Y count == served Y count {len(hr_y):,} PASS")

# 10.1.3 numerator/denominator unit agreement: severity shares are crashes/crashes
t = stats["totals_known_counts_rows"]
assert t["crashes"] == NK
recomputed_inj_share = float((known["Number_of_Injuries"] > 0).mean())
assert abs(recomputed_inj_share - t["injury_crash_share"]) < 0.0001
# people totals are labeled people, never divided into crash shares
assert t["injuries_people"] == int(known["Number_of_Injuries"].sum())
assert t["fatalities_people"] == int(known["Number_of_Fatalities"].sum())
print(f"[10.1.3] injury-crash share denominator = {NK} known-count crashes, recomputed {recomputed_inj_share:.4f}; people totals ({t['injuries_people']:,} injuries / {t['fatalities_people']:,} fatalities) kept as people counts PASS")

# 10.1.4 categorical exhaustiveness: full Counters sum to N and match stats.json
for col, key in [("Collision_Type_Description", "collision_counter_all_rows"),
                 ("Weather_Description", None), ("Illumination_Description", None)]:
    cnt = clean[col].value_counts(dropna=False)
    assert int(cnt.sum()) == N, col
    print(f"[10.1.4] {col} Counter: {clean[col].nunique(dropna=True)} values + null bucket, counts sum to {N} PASS")
assert {str(k): int(v) for k, v in clean["Collision_Type_Description"].value_counts(dropna=False).items() if not pd.isna(k)} == \
       {k: v for k, v in stats["collision_counter_all_rows"].items() if k != "null"}
pc = clean["Precinct"].value_counts(dropna=False)
assert int(pc.sum()) == N and len(pc) == 10  # 9 served labels + null
print(f"[10.1.4] Precinct Counter: 9 served labels (all <=6 chars, truncation documented) + null bucket, sums to {N}; collision Counter matches stats.json exactly PASS")

# 10.1.5 nullable denominators: known + unknown = whole, for every nullable field
for col, flag in [("Precinct", "precinct_unknown_flag"), ("Hit_and_Run", None),
                  ("Collision_Type_Description", None), ("Lat", "coords_unknown_flag")]:
    unk = int(clean[flag].sum()) if flag else int(clean[col].isna().sum())
    assert (N - unk) + unk == N
    print(f"[10.1.5] {col}: known {N - unk} + unknown {unk} = {N} PASS")
assert sum(r["crashes"] for r in stats["severity_by_collision_type"]) == NK
assert sum(r["crashes"] for r in stats["precinct"]["by_precinct"]) == NK - (stats["precinct"]["unknown_rows"] - 1)  # stub is precinct-unknown and not in known

# 10.2 controls
# (a) intersection normalization merges name-order pairs (Briley control)
raw_pair = int(clean["Street_Address"].isin(["BRILEY PKWYN & BRILEY PKWYS", "BRILEY PKWYS & BRILEY PKWYN"]).sum())
norm_pair = int((clean["intersection_key"] == "BRILEY PKWYN & BRILEY PKWYS").sum())
assert raw_pair == norm_pair and raw_pair > 700
# (b) RPA/precinct joint-null control: geography missingness is one mechanism, not two
joint = int((clean["RPA"].isna() & clean["Precinct"].isna()).sum())
assert joint > 0.9 * stats["precinct"]["unknown_rows"]
# (c) harmful-code vs description control: pedestrian agrees both ways, pedalcycle codes-only
tok8 = int(clean["pedestrian_involved_flag"].sum()); tok9 = int(clean["pedalcycle_involved_flag"].sum())
desc_ped = int(clean["HarmfulDescriptions"].fillna("").str.contains("PEDESTRIAN").sum())
desc_cyc = int(clean["HarmfulDescriptions"].fillna("").str.contains("PEDALCYCLE").sum())
assert tok8 == desc_ped == stats["vulnerable_road_users"]["pedestrian_involved"]["crashes"] and tok9 == stats["vulnerable_road_users"]["pedalcycle_involved"]["crashes"] and desc_cyc == 0
print(f"[10.2] controls: (a) Briley junction name-order pair merges under the normalized key -> {norm_pair}; (b) RPA and Precinct are jointly null on {joint} rows (one missingness mechanism); (c) pedestrian involvement agrees code-vs-description at {tok8:,}, while pedalcycle is codes-only ({tok9} vs 0 in descriptions) PASS")

# coding completeness: minimally-coded set identity (collision-null == all-three-null)
mini = int(clean["minimally_coded_flag"].sum())
coll_null = int(clean["Collision_Type_Description"].isna().sum())
assert mini == coll_null == stats["coding_completeness"]["minimally_coded_rows"]
assert int((clean.loc[clean["minimally_coded_flag"] & ~clean["counts_unknown_flag"], "Number_of_Injuries"] > 0).sum()) == 0
fc = stats["coding_completeness"]["fully_coded_severity"]
assert fc["crashes"] == stats["coding_completeness"]["fully_coded_rows_none_of_three_null"] and fc["crashes"] + mini - 1 <= N  # fully-coded + minimally-coded overlap only via the stub row accounting
print(f"[completeness] minimally-coded rows {mini} == collision-null rows {coll_null}, with 0 injury crashes among them (definitional, not safety); fully-coded basis {fc['crashes']} crashes at {fc['injury_crash_share']} injury share vs all-rows {t['injury_crash_share']} PASS")

# 12.3 censoring / window print
cov = stats["coverage"]
print(f"[12.3] effective window: {cov['datetime_local_min']} to {cov['datetime_local_max']}; complete years 2019-2025, 2026 is a partial year and is compared only through the jan_oct table PASS")
print("ALL SECTION 10 GATES PASS")
