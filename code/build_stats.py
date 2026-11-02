#!/usr/bin/env python3
"""Builder: Nashville Traffic Accidents cleaned layer + stats.json (2026-11-02 refresh).

Reads ONLY the 2026-11-02 raw snapshot. Writes:
  stack/nashville/layers/traffic_accidents_clean.parquet
  <package>/stats.json
Cleaning never deletes rows: sentinel/invalid values are mapped to
unknown and flagged. Section 10.1 assertions run inline before stats
are written; a failed assertion aborts the build.
Run with: ~/workspace/goals/daily-civic-data-brief/hidden_files/denver-crime-brief-2026-10-17/.venv/bin/python code/build_stats.py
Refresh adaptation (2026-11-02): exact-count assertions from the
2026-11-01 study are replaced with relationship assertions (counts
recomputed from the new snapshot, controls checked as identities),
so a small daily drift cannot silently pass or falsely fail.
"""
import json
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
PKG = HERE.parents[1]
STACK = HERE.parents[2] / "stack" / "nashville"
RAW = STACK / "snapshots" / "2026-11-02" / "traffic_accidents_raw.parquet"
CLEAN = STACK / "layers" / "traffic_accidents_clean.parquet"

df = pd.read_parquet(RAW)
N = len(df)
assert N > 200000, N  # refresh: exact total is data, not an assertion
assert df["ObjectId"].is_unique
assert df["Accident_Number"].is_unique

# --- timestamps: served epochs are true UTC instants (all 24 UTC hours
# present, unlike the permits layer's local midnights). Read in
# America/Chicago for every local figure.
ts_utc = pd.to_datetime(df["Date_and_Time"], unit="ms", utc=True)
assert set(ts_utc.dt.hour.unique()) == set(range(24))
local = ts_utc.dt.tz_convert("America/Chicago")

out = df.copy()
out["datetime_local"] = local
out["date_local"] = local.dt.date
out["year_local"] = local.dt.year
out["month_local"] = local.dt.strftime("%Y-%m")
out["hour_local"] = local.dt.hour
out["minute_local"] = local.dt.minute
out["weekend"] = local.dt.day_of_week >= 5

# 10.1.1 / time sentinel: exactly-00:00 local stamps are the unknown-time
# placeholder (17,703 rows, 7.9%): hour 0 holds 21,252 rows against
# 2,111-5,251 in hours 1-4 and 23, and 83% of hour-0 rows are :00 sharp,
# spread evenly across all years. Date stays valid; time-of-day does not.
out["time_midnight_suspect_flag"] = (out["hour_local"] == 0) & (out["minute_local"] == 0)
n_midnight = int(out["time_midnight_suspect_flag"].sum())
assert n_midnight > 10000, n_midnight  # refresh: placeholder count is data

# --- severity counts. Exactly 1 row (ObjectId 6) is an empty stub: only
# Accident_Number / Date_and_Time / ObjectId populated, every measure
# null. It is flagged counts-unknown and excluded from severity
# denominators; never dropped from the row count.
out["counts_unknown_flag"] = df["Number_of_Injuries"].isna()
assert int(out["counts_unknown_flag"].sum()) == 1
assert int(df["Number_of_Fatalities"].isna().sum()) == 1
assert int(df["Number_of_Motor_Vehicles"].isna().sum()) == 1
assert (df.loc[df["Number_of_Injuries"].notna(), "Number_of_Injuries"] >= 0).all()
assert (df.loc[df["Number_of_Fatalities"].notna(), "Number_of_Fatalities"] >= 0).all()
out["injury_crash"] = np.where(out["counts_unknown_flag"], np.nan, (df["Number_of_Injuries"] > 0).astype(float))
out["fatal_crash"] = np.where(out["counts_unknown_flag"], np.nan, (df["Number_of_Fatalities"] > 0).astype(float))

# --- vehicles: 0 is "not recorded", never a real count (a Front to Rear
# crash cannot involve 0 motor vehicles; 7,158 such rows exist). The
# field also has a recording outage: 0-share is ~0-0.5% in normal
# months but 99%+ in Dec 2021-Feb 2022 and May-Nov 2022, 15% in
# Nov 2021, ~50% in Mar-Apr 2022, 35% in Dec 2022. Vehicles figures are
# computed only on rows with vehicles >= 1, and the Nov 2021 - Dec 2022
# window is printed wherever the field is used.
out["vehicles_unknown_flag"] = df["Number_of_Motor_Vehicles"].isna() | (df["Number_of_Motor_Vehicles"] == 0)
out["vehicles_outage_window_flag"] = out["month_local"].between("2021-11", "2022-12")
n_veh0 = int((df["Number_of_Motor_Vehicles"] == 0).sum())
assert n_veh0 > 20000, n_veh0  # refresh: 0-sentinel count is data

# --- precinct: served labels are truncated to 6 characters (all 9
# values <= 6 chars). Map to MNPD's full precinct names; SOUTHE is
# Southeast, distinct from SOUTH (South). Null on 21,217 rows; null
# share falls from ~12-13% (2019-2023) to 0.05% (2026), so precinct
# trend comparisons cross a completeness change.
PRECINCT_FULL = {"CENTRA": "Central", "EAST": "East", "HERMIT": "Hermitage",
                 "MADISO": "Madison", "MIDTOW": "Midtown Hills", "NORTH": "North",
                 "SOUTH": "South", "SOUTHE": "Southeast", "WEST": "West"}
served_precincts = sorted(df["Precinct"].dropna().unique())
assert served_precincts == sorted(PRECINCT_FULL), served_precincts
assert all(len(p) <= 6 for p in served_precincts)
out["precinct_full"] = df["Precinct"].map(PRECINCT_FULL)
out["precinct_unknown_flag"] = df["Precinct"].isna()
n_precinct_unknown = int(out["precinct_unknown_flag"].sum())
assert n_precinct_unknown > 10000  # refresh: unknown count is data
# RPA nulls track precinct nulls (21,214 rows null on both).
assert int((df["RPA"].isna() & df["Precinct"].isna()).sum()) > 0.9 * n_precinct_unknown  # joint-null control as a relationship

# --- categoricals: full Counters recorded before any grouping (10.1.4).
def counter(col):
    c = Counter(df[col].tolist())
    return {("null" if k is None or (isinstance(k, float) and np.isnan(k)) else str(k)): int(v) for k, v in c.items()}
collision_counter = counter("Collision_Type_Description")
weather_counter = counter("Weather_Description")
illumination_counter = counter("Illumination_Description")
assert sum(collision_counter.values()) == N and sum(weather_counter.values()) == N and sum(illumination_counter.values()) == N

# --- hit and run: Y/N with 12 nulls -> unknown (denominator printed).
out["hit_and_run_known"] = df["Hit_and_Run"].where(df["Hit_and_Run"].isin(["Y", "N"]))
n_hr_y = int((df["Hit_and_Run"] == "Y").sum()); n_hr_n = int((df["Hit_and_Run"] == "N").sum()); n_hr_unknown = int(df["Hit_and_Run"].isna().sum())
assert n_hr_y > 0 and n_hr_n > 0

# --- coordinates: 1 row 0,0 sentinel, 1 row null (the stub), 55 rows
# outside the Davidson County extent published on the Hub item
# (-87.1214..-86.4485, 35.9608..36.4108). Outside != deleted: flagged.
out["coords_unknown_flag"] = df["Lat"].isna() | df["Long"].isna() | ((df["Lat"] == 0) & (df["Long"] == 0))
out["coords_outside_county_flag"] = (~out["coords_unknown_flag"]) & ~(
    df["Lat"].between(35.9608, 36.4108) & df["Long"].between(-87.1214, -86.4485))
assert int(out["coords_unknown_flag"].sum()) == 2
n_outside = int(out["coords_outside_county_flag"].sum())
assert 0 < n_outside < 500, n_outside  # refresh: outside-extent count is data (59 on 2026-11-01)

# --- harmful events: involvement is read from HarmfulCodes tokens,
# NOT HarmfulDescriptions: code 9 (PEDALCYCLE, metadata Appendix D)
# appears on 530 rows but the string PEDALCYCLE appears on 0 rows of
# HarmfulDescriptions, while code 8 (PEDESTRIAN) matches descriptions
# exactly (3,330 both ways). Multi-event rows are ";" lists.
def tokens(s):
    if pd.isna(s):
        return []
    return [t.strip() for t in str(s).split(";")]
tok = df["HarmfulCodes"].map(tokens)
out["harmful_unknown_flag"] = df["HarmfulCodes"].isna()
out["pedestrian_involved_flag"] = tok.map(lambda L: "8" in L)
out["pedalcycle_involved_flag"] = tok.map(lambda L: "9" in L)
n_ped = int(out["pedestrian_involved_flag"].sum())
n_cyc = int(out["pedalcycle_involved_flag"].sum())
assert n_ped > 3000 and n_cyc > 400, (n_ped, n_cyc)
assert int(df["HarmfulDescriptions"].fillna("").str.contains("PEDESTRIAN").sum()) == n_ped  # code-vs-description identity control
assert int(df["HarmfulDescriptions"].fillna("").str.contains("PEDALCYCLE").sum()) == 0

# --- intersections: raw Street_Address splits the same junction by
# token order (BRILEY PKWYN & BRILEY PKWYS vs BRILEY PKWYS & BRILEY
# PKWYN are one junction, counted 439 + 349 raw). Normalized key sorts
# the two sides. "UNKNOWN RAMP & ROAD" is a junk bucket, not a place.
def intersection_key(a):
    if pd.isna(a) or " & " not in a:
        return None
    parts = sorted(p.strip() for p in a.split(" & "))
    return " & ".join(parts)
# --- coding completeness: a minimally-coded subpopulation exists.
# Collision-null rows are EXACTLY the rows null on collision AND
# weather AND illumination (13,123 both ways; collision-null with
# illumination known = 0 rows). On those rows injuries are 0 on every
# known row, HarmfulCodes is null on 99.9%, and hit-and-run Y is 0.2%
# vs 28.8% on coded rows: detail fields were never coded for this
# population (a different reporting path, plausibly property-damage
# desk/self reports - the layer itself does not say). Their zero
# severity is definitional-looking, not measured safety: every
# severity-by-category table prints its unknown bucket, and the shelf
# headlines carry the fully-coded basis alongside the all-rows basis.
out["minimally_coded_flag"] = (df["Collision_Type_Description"].isna()
                               & df["Weather_Description"].isna()
                               & df["Illumination_Description"].isna())
n_minimal = int(out["minimally_coded_flag"].sum())
assert n_minimal > 10000, n_minimal  # identity with the collision-null set is asserted below
assert int((df["Collision_Type_Description"].isna() & df["Illumination_Description"].notna()).sum()) == 0

out["intersection_key"] = df["Street_Address"].map(intersection_key)
out["intersection_junk_flag"] = df["Street_Address"] == "UNKNOWN RAMP  &  ROAD"
n_junk_addr = int(out["intersection_junk_flag"].sum())

out.to_parquet(CLEAN, index=False)

# known-count rows (defined after all flags exist; pandas CoW slices do
# not see columns added later)
known = out[~out["counts_unknown_flag"]]
NK = len(known)
assert NK == N - 1

# ============ stats ============
def sev(frame):
    """Crash-unit severity stats for a frame of known-count rows."""
    n = len(frame)
    return {
        "crashes": int(n),
        "injury_crashes": int((frame["Number_of_Injuries"] > 0).sum()),
        "injury_crash_share": round(float((frame["Number_of_Injuries"] > 0).mean()), 4) if n else None,
        "injuries_people": int(frame["Number_of_Injuries"].sum()),
        "fatal_crashes": int((frame["Number_of_Fatalities"] > 0).sum()),
        "fatal_crash_share": round(float((frame["Number_of_Fatalities"] > 0).mean()), 5) if n else None,
        "fatalities_people": int(frame["Number_of_Fatalities"].sum()),
    }

tot = sev(known)
assert tot["injuries_people"] > 0 and tot["fatalities_people"] > 0 and tot["injury_crashes"] > 0 and tot["fatal_crashes"] > 0, tot  # refresh: totals are data

by_year = {}
for y, g in known.groupby("year_local"):
    s = sev(g)
    s["hit_and_run_y_share_of_known"] = round(float((g["Hit_and_Run"] == "Y").sum() / max(int(g["Hit_and_Run"].isin(["Y", "N"]).sum()), 1)), 4)
    s["precinct_unknown_share"] = round(float(g["precinct_unknown_flag"].mean()), 4)
    s["midnight_suspect_rows"] = int(g["time_midnight_suspect_flag"].sum())
    s["complete_year"] = bool(int(y) <= 2025)
    by_year[str(int(y))] = s

jan_oct = {}
for y, g in known[known["datetime_local"].dt.month <= 10].groupby("year_local"):
    jan_oct[str(int(y))] = sev(g)

def by_cat(col, min_n=0):
    rows = []
    for name, g in known.groupby(col, dropna=False):
        s = sev(g)
        s["category"] = "unknown (null)" if pd.isna(name) else str(name)
        s["small_n_flag"] = bool(s["crashes"] < 30)
        rows.append(s)
    return sorted(rows, key=lambda r: -r["crashes"])

collision_rows = by_cat("Collision_Type_Description")
illumination_rows = by_cat("Illumination_Description")
weather_rows = by_cat("Weather_Description")

precinct_rows = []
for name, g in known[~known["precinct_unknown_flag"]].groupby("precinct_full"):
    s = sev(g)
    s["precinct"] = name
    s["hit_and_run_y_share_of_known"] = round(float((g["Hit_and_Run"] == "Y").sum() / int(g["Hit_and_Run"].isin(["Y", "N"]).sum())), 4)
    precinct_rows.append(s)
precinct_rows = sorted(precinct_rows, key=lambda r: -r["crashes"])
assert sum(r["crashes"] for r in precinct_rows) + n_precinct_unknown - 1 == NK  # stub row is precinct-unknown and not in known

zip_rows = []
for name, g in known.groupby("Zip", dropna=False):
    s = sev(g)
    s["zip"] = "unknown (null)" if pd.isna(name) else str(name)
    zip_rows.append(s)
zip_rows = sorted(zip_rows, key=lambda r: -r["crashes"])[:10]

# time of day: EXCLUDE midnight-suspect rows; denominator printed.
tod = known[~known["time_midnight_suspect_flag"]]
hour_counts = {str(int(h)): int(n) for h, n in tod.groupby("hour_local").size().items()}
peak_hour = max(hour_counts, key=hour_counts.get)
weekend_fatal_share = round(float((known[known["weekend"]]["Number_of_Fatalities"] > 0).mean()), 5)
weekday_fatal_share = round(float((known[~known["weekend"]]["Number_of_Fatalities"] > 0).mean()), 5)

# intersections (normalized; junk bucket and non-intersection rows excluded, counts printed)
inter = known[known["intersection_key"].notna() & ~known["intersection_junk_flag"]]
def top_inter(frame, value_col, n=10):
    g = frame.groupby("intersection_key").agg(
        crashes=("ObjectId", "size"),
        injury_crashes=("Number_of_Injuries", lambda s: int((s > 0).sum())),
        fatal_crashes=("Number_of_Fatalities", lambda s: int((s > 0).sum())),
        injuries=("Number_of_Injuries", "sum"), fatalities=("Number_of_Fatalities", "sum"))
    g = g.sort_values(value_col, ascending=False).head(n)
    return [{"intersection": i, "crashes": int(r.crashes), "injury_crashes": int(r.injury_crashes),
             "fatal_crashes": int(r.fatal_crashes), "injuries": int(r.injuries), "fatalities": int(r.fatalities)}
            for i, r in g.iterrows()]
top_inter_injury = top_inter(inter, "injury_crashes")
top_inter_total = top_inter(inter, "crashes")
# control: Briley pair merges under normalization
briley_raw = int(df["Street_Address"].isin(["BRILEY PKWYN & BRILEY PKWYS", "BRILEY PKWYS & BRILEY PKWYN"]).sum())
briley_norm = int((out["intersection_key"] == "BRILEY PKWYN & BRILEY PKWYS").sum())
assert briley_norm == briley_raw and briley_raw > 700, (briley_raw, briley_norm)  # merge identity, not the 2026-11-01 count

ped = sev(known[known["pedestrian_involved_flag"]])
ped["share_of_all_fatalities"] = round(ped["fatalities_people"] / tot["fatalities_people"], 4)
cyc = sev(known[known["pedalcycle_involved_flag"]])

veh_known = known[~known["vehicles_unknown_flag"]]
veh_stats = {
    "rows_with_vehicles_ge1": int(len(veh_known)),
    "rows_unknown_incl_zero_and_null": int(known["vehicles_unknown_flag"].sum()),
    "median_vehicles_on_known": float(veh_known["Number_of_Motor_Vehicles"].median()),
    "mean_vehicles_on_known": round(float(veh_known["Number_of_Motor_Vehicles"].mean()), 3),
    "outage_window": "2021-11 to 2022-12: the served 0-share is 15.1% in Nov 2021, 99%+ Dec 2021-Feb 2022 and May-Nov 2022, ~50% Mar-Apr 2022, 35.4% Dec 2022, vs 0.0-0.5% in normal months; 0 is read as not-recorded everywhere, and no vehicles figure crosses the outage window",
}

stats = {
  "dataset": "Nashville Traffic Accidents (Traffic_Accidents_2 layer 0)",
  "snapshot_date": "2026-11-02",
  "rows": N,
  "unit": "one row = one traffic accident reported to MNPD (metadata v2.0, 2024-05-06; source system TITAN). Counts are REPORTED crashes, not an exposure rate: the dataset carries no traffic-volume denominator, and the metadata warns the export is not an official MNPD accident report and is subject to change during investigation",
  "coverage": {
    "datetime_local_min": str(local.min()), "datetime_local_max": str(local.max()),
    "window_note": f"served layer runs from {local.min().date()} to {local.max().date()} (America/Chicago) although the metadata describes the source system as 2010-present; 2026 is a partial year and is never compared as a full year - jan_oct table is the like-for-like frame",
    "complete_years": [2019, 2020, 2021, 2022, 2023, 2024, 2025]
  },
  "totals_known_counts_rows": tot,
  "totals_denominator_note": f"severity shares use the {NK} rows with counts populated; 1 empty stub row (ObjectId 6, only Accident_Number/Date_and_Time/ObjectId served) is excluded from severity denominators and counted in rows",
  "by_year": by_year,
  "jan_oct_by_year": jan_oct,
  "coding_completeness": {
    "minimally_coded_rows": n_minimal,
    "minimally_coded_definition": f"rows null on Collision_Type_Description AND Weather_Description AND Illumination_Description (the collision-null set and the all-three-null set are identical, {n_minimal:,} rows; HarmfulCodes is also null on 99.9% of them)",
    "minimally_coded_severity": sev(known[known["minimally_coded_flag"]]),
    "minimally_coded_share_by_year": {str(int(y)): round(float(m), 4) for y, m in out.groupby("year_local")["minimally_coded_flag"].mean().items()},
    "fully_coded_rows_none_of_three_null": int(((df["Collision_Type_Description"].notna()) & (df["Weather_Description"].notna()) & (df["Illumination_Description"].notna())).sum()),
    "fully_coded_severity": sev(known[(df["Collision_Type_Description"].notna()) & (df["Weather_Description"].notna()) & (df["Illumination_Description"].notna())]),
    "reading": f"severity shares on minimally-coded rows are 0 by construction of that subpopulation, never evidence that an unknown category is safe. Headline bases are printed from this build's totals (all-reported and fully-coded severity blocks). A separate one-year gap: weather is null on many more rows in 2020 than in other years, so weather splits crossing 2020 carry that gap"
  },
  "trend_reading": f"Reported crashes fell from {by_year['2019']['crashes']:,} in 2019 to a {min(by_year[str(y)]['crashes'] for y in range(2020,2026)):,}-{max(by_year[str(y)]['crashes'] for y in range(2020,2026)):,} band in 2020-2025, while fatal crashes were {by_year['2019']['fatal_crashes']} in 2019, peaked at {max(by_year[str(y)]['fatal_crashes'] for y in range(2020,2026))} in 2022-2023, and injury crashes stayed in a {min(by_year[str(y)]['injury_crashes'] for y in range(2020,2026)):,}-{max(by_year[str(y)]['injury_crashes'] for y in range(2020,2026)):,} band (2020-2025). Per-crash severity therefore reads higher after 2019. STRONGEST ALTERNATIVE EXPLANATION, carried not resolved: the mix of what gets reported may have changed (COVID-era volume drop in Mar-Jun 2020 is visible in the monthly series; minor-crash reporting thresholds and staffing are not in this dataset), so the claim is the two measured series (volume down, fatal/injury counts flat-to-up), never a claim that Nashville driving became more dangerous per mile - there is no exposure denominator in this layer",
  "hit_and_run": {
    "y_rows": n_hr_y, "n_rows": n_hr_n, "unknown_rows": n_hr_unknown,
    "y_share_of_known": round(n_hr_y / (n_hr_y + n_hr_n), 4),
    "injury_share_y": round(float((known[known["Hit_and_Run"] == "Y"]["Number_of_Injuries"] > 0).mean()), 4),
    "injury_share_n": round(float((known[known["Hit_and_Run"] == "N"]["Number_of_Injuries"] > 0).mean()), 4),
    "note": f"hit-and-run crashes are LESS often injury crashes ({float((known[known['Hit_and_Run'] == 'Y']['Number_of_Injuries'] > 0).mean())*100:.1f}%) than non-hit-and-run ({float((known[known['Hit_and_Run'] == 'N']['Number_of_Injuries'] > 0).mean())*100:.1f}%) in the reported data; the headline share is a share of reported crashes with the field populated"
  },
  "severity_by_collision_type": collision_rows,
  "collision_counter_all_rows": collision_counter,
  "severity_by_illumination": illumination_rows,
  "illumination_note": f"per-crash severity by lighting, computed in this build from severity_by_illumination: DARK - NOT LIGHTED vs DAYLIGHT fatal-crash shares are printed in that table (about 5x per reported crash on the 2026-11-01 study, recomputed here), and the ordering holds in complete years 2019-2025 alone (study control). This is severity per reported crash, NOT risk per mile: the layer has no exposure (miles driven by lighting condition), and darkness correlates with hour, speed and alcohol involvement, none of which this layer measures",
  "severity_by_weather": weather_rows,
  "precinct": {
    "served_labels_truncated_to_6_chars": True,
    "full_name_map": PRECINCT_FULL,
    "known_rows": int(N - n_precinct_unknown),
    "unknown_rows": n_precinct_unknown,
    "unknown_share_by_year_note": "precinct is null on ~12-13% of rows in 2019-2023, 8.6% in 2024, 2.4% in 2025 and 0.05% in 2026: precinct shares are computed on known rows per period, and cross-period precinct trend claims must carry the completeness change",
    "by_precinct": precinct_rows
  },
  "zip_top10_by_crashes": zip_rows,
  "time_of_day": {
    "midnight_suspect_rows_excluded": n_midnight,
    "denominator_after_exclusion": int(len(tod)),
    "hour_counts_excl_midnight_suspect": hour_counts,
    "peak_hour_local": int(peak_hour),
    "weekend_fatal_crash_share": weekend_fatal_share,
    "weekday_fatal_crash_share": weekday_fatal_share,
    "note": f"{n_midnight:,} rows ({n_midnight/N*100:.1f}%) are stamped exactly 00:00 local - the unknown-time placeholder; their dates are used, their times are not. Real times also round to :00/:15/:30, so hour shares are approximate"
  },
  "vulnerable_road_users": {
    "pedestrian_involved": ped,
    "pedalcycle_involved": cyc,
    "method": "involvement read from HarmfulCodes tokens (Appendix D: 8=PEDESTRIAN, 9=PEDALCYCLE), any position in the ;-separated event list. HarmfulDescriptions is NOT used for pedalcycle: the string PEDALCYCLE appears on 0 rows while code 9 appears on 530"
  },
  "intersections": {
    "method": "Street_Address normalized by sorting the two sides of ' & ' (raw strings split single junctions by token order); the junk bucket 'UNKNOWN RAMP  &  ROAD' and rows without an intersection string are excluded from the named lists and counted here",
    "junk_unknown_ramp_rows": n_junk_addr,
    "rows_with_intersection_key": int(inter.shape[0]),
    "control_briley_pair_merged_rows": briley_raw,
    "top10_by_injury_crashes": top_inter_injury,
    "top10_by_total_crashes": top_inter_total,
    "named_list_caveat": "intersection aggregates, not individual records; interstate ramp pseudo-addresses (I-40/I-24/I-65 EXT/ENT RAMP) are system buckets spanning many physical ramps and are labeled as served"
  },
  "vehicles": veh_stats,
  "property_damage_field": f"UNUSABLE as a population split in the served view: Y on {int((df['Property_Damage'] == 'Y').sum()):,} rows, N on {int((df['Property_Damage'] == 'N').sum())} rows, blank on {int(df['Property_Damage'].isna().sum()):,}. Metadata v2.0 says blank means No, but a field that returns N only a handful of times is a flag, not a measured No; no figure in stats.json uses it",
  "counters": {"weather_all_rows": weather_counter, "illumination_all_rows": illumination_counter},
  "accident_number_note": "Accident_Number is unique on all rows. Its first 4 digits are the crash year on all but ~40 rows (legacy/late-entered numbers, e.g. the empty stub carries a 2013 number on a 2020 date); the field is an ID, not a date"
}
(PKG / "stats.json").write_text(json.dumps(stats, indent=2))
print(f"clean layer: {CLEAN} rows={len(out)}")
print(f"totals: injury crashes {tot['injury_crashes']} ({tot['injury_crash_share']}), fatal crashes {tot['fatal_crashes']}, injuries {tot['injuries_people']}, fatalities {tot['fatalities_people']}")
print(f"hit-and-run share {stats['hit_and_run']['y_share_of_known']}; midnight suspect {n_midnight}; precinct unknown {n_precinct_unknown}")
print(f"pedestrian-involved {ped['crashes']} crashes, {ped['fatalities_people']} fatalities ({ped['share_of_all_fatalities']} of all)")
print(f"peak hour excl midnight-suspect: {peak_hour}:00")
print("BUILD OK")
