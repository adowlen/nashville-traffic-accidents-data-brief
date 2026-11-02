#!/usr/bin/env python
"""INDEPENDENT VERIFIER (Section 11) - Machine Readable Nashville traffic study.

Written from scratch for this verification pass. It does NOT import, read, or
reuse the builder's code. Every figure in stats.json is recomputed from
primary sources by two independent methods:

  Method A (snapshot recount): pyarrow is used ONLY to decode the raw parquet
  snapshot into plain Python lists. All aggregation is hand-rolled stdlib:
  explicit loops, collections.Counter, set cardinality, integer epoch
  arithmetic (divmod on milliseconds) and zoneinfo for America/Chicago
  local time. No pandas, no groupby, no pyarrow compute kernels.

  Method B (live service): server-side ArcGIS REST statistics / groupBy /
  count queries against the live FeatureServer layer. The live service
  rolls daily, so live figures may legitimately be >= snapshot figures;
  each live check passes on exact equality, or on live >= claimed when the
  live layer total has grown past the snapshot total (drift noted inline).
  The exactly-midnight check cannot be expressed as a pure server aggregate
  (local midnight is 05:00 UTC in CDT, 06:00 UTC in CST), so the server
  filters the exact-05:00/06:00-UTC candidate set and the local-time test
  is then applied with zoneinfo to the returned epochs - still independent
  of the builder, which used pandas tz conversion on the full snapshot.

Exit code 0 only if every check passes.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

PKG = Path(__file__).resolve().parent.parent
STATS_PATH = PKG / "stats.json"
SNAPSHOT = (PKG.parent / "stack" / "nashville" / "snapshots" / "2026-11-02"
            / "traffic_accidents_raw.parquet")
LIVE_BASE = ("https://services2.arcgis.com/HdTo6HJqh92wn4D8/arcgis/rest/"
             "services/Traffic_Accidents_2/FeatureServer/0")
CHICAGO = ZoneInfo("America/Chicago")
UTC = timezone.utc

RESULTS = []  # (ok, label, detail)


def check(ok, label, claimed, recomputed, method):
    RESULTS.append((bool(ok), label))
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {label} | claimed={claimed} recomputed={recomputed} "
          f"| {method}")


def local_from_epoch_ms(ms):
    """Epoch ms -> America/Chicago local datetime, integer arithmetic only."""
    sec, rem_ms = divmod(int(ms), 1000)
    return (datetime.fromtimestamp(sec, tz=UTC)
            + timedelta(milliseconds=rem_ms)).astimezone(CHICAGO)


# --------------------------------------------------------------------------
# Load claims
# --------------------------------------------------------------------------
stats = json.loads(STATS_PATH.read_text())
CLAIM_ROWS = stats["rows"]
TOT = stats["totals_known_counts_rows"]
HAR = stats["hit_and_run"]
COLL_ALL = stats["collision_counter_all_rows"]
MIDNIGHT_CLAIM = stats["time_of_day"]["midnight_suspect_rows_excluded"]
VRU = stats["vulnerable_road_users"]
PREC = stats["precinct"]
SOUTHEAST_CLAIM = next(e["crashes"] for e in PREC["by_precinct"]
                       if e["precinct"] == "Southeast")
VEH_ZERO_CLAIM = stats["vehicles"]["rows_unknown_incl_zero_and_null"]
BY_YEAR_CLAIM = {int(y): v["crashes"] for y, v in stats["by_year"].items()}

print("=" * 78)
print("INDEPENDENT VERIFICATION - Nashville Traffic Accidents study")
print(f"run at (UTC): {datetime.now(UTC).isoformat()}")
print(f"claims file : {STATS_PATH}")
print(f"snapshot    : {SNAPSHOT}")
print(f"live service: {LIVE_BASE}")
print("=" * 78)

# --------------------------------------------------------------------------
# Method A - snapshot recount (pyarrow decode only; stdlib aggregation)
# --------------------------------------------------------------------------
print("\n--- Method A: raw snapshot recount (stdlib aggregation) ---")
import pyarrow.parquet as pq  # decode only; no compute/groupby used

pf = pq.ParquetFile(str(SNAPSHOT))
meta_rows = pf.metadata.num_rows
tbl = pf.read()
cols = {name: tbl.column(name).to_pylist() for name in tbl.column_names}
n = len(cols["ObjectId"])

check(meta_rows == CLAIM_ROWS and n == CLAIM_ROWS,
      "A01 total rows", CLAIM_ROWS, f"parquet_meta={meta_rows}, decoded={n}",
      "snapshot")

oid = cols["ObjectId"]
acc = cols["Accident_Number"]
check(len(set(oid)) == n, "A02 ObjectId unique", n, len(set(oid)), "snapshot")
check(len(set(acc)) == n, "A03 Accident_Number unique", n, len(set(acc)),
      "snapshot")

inj = cols["Number_of_Injuries"]
fat = cols["Number_of_Fatalities"]
veh = cols["Number_of_Motor_Vehicles"]

# Empty stub: every field except Accident_Number / Date_and_Time / ObjectId null
key_fields = {"Accident_Number", "Date_and_Time", "ObjectId"}
nonkey = [c for c in cols if c not in key_fields]
stub_idx = [i for i in range(n)
            if all(cols[c][i] is None for c in nonkey)]
check(len(stub_idx) == 1, "A04 exactly 1 empty stub row", 1, len(stub_idx),
      "snapshot")
if stub_idx:
    print(f"       stub row: ObjectId={oid[stub_idx[0]]} "
          f"Accident_Number={acc[stub_idx[0]]}")

known_idx = [i for i in range(n) if inj[i] is not None]
check(len(known_idx) == TOT["crashes"], "A05 known-count rows",
      TOT["crashes"], len(known_idx), "snapshot")
check(all(fat[i] is not None and veh[i] is not None for i in known_idx)
      and len([i for i in range(n) if fat[i] is None]) == 1,
      "A05b null counts confined to the stub row", 1,
      len([i for i in range(n) if fat[i] is None]), "snapshot")

inj_crashes = sum(1 for i in known_idx if inj[i] > 0)
fat_crashes = sum(1 for i in known_idx if fat[i] > 0)
inj_people = int(sum(inj[i] for i in known_idx))
fat_people = int(sum(fat[i] for i in known_idx))
check(inj_crashes == TOT["injury_crashes"], "A06 injury crashes",
      TOT["injury_crashes"], inj_crashes, "snapshot")
check(fat_crashes == TOT["fatal_crashes"], "A07 fatal crashes",
      TOT["fatal_crashes"], fat_crashes, "snapshot")
check(inj_people == TOT["injuries_people"], "A08 injuries (people)",
      TOT["injuries_people"], inj_people, "snapshot")
check(fat_people == TOT["fatalities_people"], "A09 fatalities (people)",
      TOT["fatalities_people"], fat_people, "snapshot")

har = cols["Hit_and_Run"]
har_counter = Counter(har)
y_rows = har_counter.get("Y", 0)
n_rows_har = har_counter.get("N", 0)
har_known = y_rows + n_rows_har
har_share_pct = round(100.0 * y_rows / har_known, 2) if har_known else None
check(y_rows == HAR["y_rows"], "A10 hit-and-run Y rows", HAR["y_rows"],
      y_rows, "snapshot")
claimed_har_known = HAR["y_rows"] + HAR["n_rows"]
claimed_har_pct = round(100.0 * HAR["y_share_of_known"], 2)
check(har_known == claimed_har_known and har_share_pct == claimed_har_pct,
      "A11 hit-and-run share of known",
      f"{HAR['y_rows']}/{claimed_har_known} = {claimed_har_pct}%",
      f"{y_rows}/{har_known} = {har_share_pct}%", "snapshot")

epochs = cols["Date_and_Time"]
midnight = 0
for ms in epochs:
    loc = local_from_epoch_ms(ms)
    if (loc.hour, loc.minute, loc.second, loc.microsecond) == (0, 0, 0, 0):
        midnight += 1
check(midnight == MIDNIGHT_CLAIM,
      "A12 timestamps exactly 00:00 America/Chicago", MIDNIGHT_CLAIM,
      midnight, "snapshot (epoch divmod + zoneinfo)")

prec_counter = Counter(cols["Precinct"])
prec_labels = sorted(k for k in prec_counter if k is not None)
check(len(prec_labels) == 9, "A13 distinct served precinct labels", 9,
      f"{len(prec_labels)} {prec_labels}", "snapshot")
check(all(len(k) <= 6 for k in prec_labels),
      "A14 all precinct labels <= 6 chars", "<=6",
      f"max={max(len(k) for k in prec_labels)}", "snapshot")
check(prec_counter.get(None, 0) == PREC["unknown_rows"],
      "A15 null precinct rows", PREC["unknown_rows"],
      prec_counter.get(None, 0), "snapshot")
check(prec_counter.get("SOUTHE", 0) == SOUTHEAST_CLAIM,
      "A16 Southeast precinct (served label SOUTHE) crashes",
      SOUTHEAST_CLAIM, prec_counter.get("SOUTHE", 0), "snapshot")

coll_counter = Counter(cols["Collision_Type_Description"])
check(coll_counter.get("Front to Rear", 0) == COLL_ALL["Front to Rear"],
      "A17 collision type: Front to Rear", COLL_ALL["Front to Rear"],
      coll_counter.get("Front to Rear", 0), "snapshot")
check(coll_counter.get("ANGLE", 0) == COLL_ALL["ANGLE"],
      "A18 collision type: ANGLE", COLL_ALL["ANGLE"],
      coll_counter.get("ANGLE", 0), "snapshot")
check(coll_counter.get(None, 0) == COLL_ALL["null"],
      "A19 collision type: null (all rows)", COLL_ALL["null"],
      coll_counter.get(None, 0), "snapshot")


def has_token(code_str, token):
    if code_str is None:
        return False
    return token in [part.strip() for part in str(code_str).split(";")]


codes = cols["HarmfulCodes"]
ped_idx = [i for i in range(n) if has_token(codes[i], "8")]
ped_crashes = len(ped_idx)
ped_fatalities = int(sum(fat[i] or 0 for i in ped_idx))
pedal_crashes = sum(1 for i in range(n) if has_token(codes[i], "9"))
check(ped_crashes == VRU["pedestrian_involved"]["crashes"],
      "A20 pedestrian-involved crashes (HarmfulCodes token 8)",
      VRU["pedestrian_involved"]["crashes"], ped_crashes, "snapshot")
check(ped_fatalities == VRU["pedestrian_involved"]["fatalities_people"],
      "A21 pedestrian fatalities (people)",
      VRU["pedestrian_involved"]["fatalities_people"], ped_fatalities,
      "snapshot")
check(pedal_crashes == VRU["pedalcycle_involved"]["crashes"],
      "A22 pedalcycle-involved crashes (HarmfulCodes token 9)",
      VRU["pedalcycle_involved"]["crashes"], pedal_crashes, "snapshot")

veh_zero = sum(1 for v in veh if v == 0)
# stats vehicles.rows_unknown_incl_zero_and_null is computed on known-count
# rows in the builder, so it equals the all-rows vehicles==0 count (the stub
# row's vehicles value is null, not 0).
check(veh_zero == VEH_ZERO_CLAIM, "A23 rows with vehicles == 0",
      VEH_ZERO_CLAIM, veh_zero, "snapshot")

# Per-year local crash counts. stats.json by_year sums to the known-count
# total (stub excluded); the stub's local year is 2020, so all-rows counts
# must differ from the claims by exactly +1 in 2020 and 0 elsewhere, and
# known-only counts must match exactly.
year_all = Counter()
year_known = Counter()
for i in range(n):
    yr = local_from_epoch_ms(epochs[i]).year
    year_all[yr] += 1
    if inj[i] is not None:
        year_known[yr] += 1
for yr in sorted(BY_YEAR_CLAIM):
    check(year_known.get(yr, 0) == BY_YEAR_CLAIM[yr],
          f"A24-{yr} crashes in local year {yr} (known-count rows)",
          BY_YEAR_CLAIM[yr], year_known.get(yr, 0), "snapshot")
diff_map = {yr: year_all.get(yr, 0) - BY_YEAR_CLAIM[yr]
            for yr in BY_YEAR_CLAIM}
stub_year = (local_from_epoch_ms(epochs[stub_idx[0]]).year
             if stub_idx else None)
expected_diff = {yr: (1 if yr == stub_year else 0) for yr in BY_YEAR_CLAIM}
check(diff_map == expected_diff,
      f"A25 all-rows vs by_year difference is stub-only (+1 in {stub_year})",
      str(expected_diff), str(diff_map), "snapshot")

# --------------------------------------------------------------------------
# Method B - live ArcGIS server-side statistics / groupBy / counts
# --------------------------------------------------------------------------
print("\n--- Method B: live ArcGIS server-side queries ---")


def live_query(params):
    url = LIVE_BASE + "/query?" + urllib.parse.urlencode(params)
    last_err = None
    for _ in range(3):
        try:
            with urllib.request.urlopen(url, timeout=90) as resp:
                data = json.load(resp)
            if "error" in data:
                raise RuntimeError(str(data["error"]))
            return data
        except Exception as exc:  # retry transient transport errors only
            last_err = exc
            time.sleep(2)
    raise RuntimeError(f"live query failed: {last_err}")


def live_count(where):
    return live_query({"where": where, "returnCountOnly": "true",
                       "f": "json"})["count"]


def live_stat(where, stat_type, field, out_name):
    out_stats = json.dumps([{"statisticType": stat_type,
                             "onStatisticField": field,
                             "outStatisticFieldName": out_name}])
    data = live_query({"where": where, "outStatistics": out_stats,
                       "f": "json"})
    return data["features"][0]["attributes"][out_name]


def live_groupby(field):
    out_stats = json.dumps([{"statisticType": "count",
                             "onStatisticField": "ObjectId",
                             "outStatisticFieldName": "c"}])
    data = live_query({"where": "1=1", "groupByFieldsForStatistics": field,
                       "outStatistics": out_stats, "f": "json"})
    return {f["attributes"][field]: f["attributes"]["c"]
            for f in data["features"]}


live_total = live_count("1=1")
drift = live_total - CLAIM_ROWS
print(f"live layer total = {live_total} (snapshot {CLAIM_ROWS}, "
      f"drift {drift:+d}; live service rolls daily, drift >= 0 is "
      f"legitimate, drift < 0 is not)")


def live_ok(live_val, claimed):
    """Exact match, or live >= claimed explained by layer growth."""
    return live_val == claimed or (drift > 0 and live_val >= claimed)


def drift_note(live_val, claimed):
    if live_val == claimed:
        return "live (exact, no drift at verify time)"
    return f"live (drift-consistent: layer grew by {drift})"


check(live_total >= CLAIM_ROWS, "B01 live total rows >= snapshot rows",
      f">={CLAIM_ROWS}", live_total, "live count")

live_inj_sum = int(live_stat("1=1", "sum", "Number_of_Injuries", "s"))
live_fat_sum = int(live_stat("1=1", "sum", "Number_of_Fatalities", "s"))
check(live_ok(live_inj_sum, TOT["injuries_people"]),
      "B02 live sum of injuries (people)", TOT["injuries_people"],
      live_inj_sum, drift_note(live_inj_sum, TOT["injuries_people"]))
check(live_ok(live_fat_sum, TOT["fatalities_people"]),
      "B03 live sum of fatalities (people)", TOT["fatalities_people"],
      live_fat_sum, drift_note(live_fat_sum, TOT["fatalities_people"]))

live_inj_cr = live_count("Number_of_Injuries > 0")
live_fat_cr = live_count("Number_of_Fatalities > 0")
live_null_counts = live_count("Number_of_Injuries IS NULL")
check(live_ok(live_inj_cr, TOT["injury_crashes"]),
      "B04 live injury crashes (Number_of_Injuries > 0)",
      TOT["injury_crashes"], live_inj_cr,
      drift_note(live_inj_cr, TOT["injury_crashes"]))
check(live_ok(live_fat_cr, TOT["fatal_crashes"]),
      "B05 live fatal crashes (Number_of_Fatalities > 0)",
      TOT["fatal_crashes"], live_fat_cr,
      drift_note(live_fat_cr, TOT["fatal_crashes"]))
check(live_null_counts == 1,
      "B06 live rows with null counts (the stub)", 1, live_null_counts,
      "live count")

live_har = live_groupby("Hit_and_Run")
live_y = live_har.get("Y", 0)
live_har_known = live_y + live_har.get("N", 0)
live_share = round(100.0 * live_y / live_har_known, 2) if live_har_known else None
check(live_ok(live_y, HAR["y_rows"])
      and (live_share == claimed_har_pct or drift > 0),
      "B07 live hit-and-run Y rows and share of known",
      f"{HAR['y_rows']} = {claimed_har_pct}%",
      f"{live_y}/{live_har_known} = {live_share}%",
      drift_note(live_y, HAR["y_rows"]))

live_prec = live_groupby("Precinct")
live_prec_labels = sorted(k for k in live_prec if k is not None)
check(len(live_prec_labels) == 9
      and all(len(k) <= 6 for k in live_prec_labels),
      "B08 live precinct labels: 9 values, all <= 6 chars", "9, max 6",
      f"{len(live_prec_labels)} {live_prec_labels}, "
      f"max={max(len(k) for k in live_prec_labels)}", "live groupBy")
check(live_ok(live_prec.get(None, 0), PREC["unknown_rows"]),
      "B09 live null precinct rows", PREC["unknown_rows"],
      live_prec.get(None, 0),
      drift_note(live_prec.get(None, 0), PREC["unknown_rows"]))
check(live_ok(live_prec.get("SOUTHE", 0), SOUTHEAST_CLAIM),
      "B10 live Southeast (SOUTHE) crashes", SOUTHEAST_CLAIM,
      live_prec.get("SOUTHE", 0),
      drift_note(live_prec.get("SOUTHE", 0), SOUTHEAST_CLAIM))

live_coll = live_groupby("Collision_Type_Description")
check(live_ok(live_coll.get("Front to Rear", 0), COLL_ALL["Front to Rear"]),
      "B11 live collision type: Front to Rear", COLL_ALL["Front to Rear"],
      live_coll.get("Front to Rear", 0),
      drift_note(live_coll.get("Front to Rear", 0),
                 COLL_ALL["Front to Rear"]))
check(live_ok(live_coll.get("ANGLE", 0), COLL_ALL["ANGLE"]),
      "B12 live collision type: ANGLE", COLL_ALL["ANGLE"],
      live_coll.get("ANGLE", 0),
      drift_note(live_coll.get("ANGLE", 0), COLL_ALL["ANGLE"]))
check(live_ok(live_coll.get(None, 0), COLL_ALL["null"]),
      "B13 live collision type: null", COLL_ALL["null"],
      live_coll.get(None, 0),
      drift_note(live_coll.get(None, 0), COLL_ALL["null"]))

TOKEN_WHERE = ("{f} = '{t}' OR {f} LIKE '{t};%' OR {f} LIKE '%;{t};%' "
               "OR {f} LIKE '%;{t}'")
w8 = TOKEN_WHERE.format(f="HarmfulCodes", t="8")
w9 = TOKEN_WHERE.format(f="HarmfulCodes", t="9")
live_ped = live_count(w8)
live_ped_fat = int(live_stat(w8, "sum", "Number_of_Fatalities", "s"))
live_pedal = live_count(w9)
check(live_ok(live_ped, VRU["pedestrian_involved"]["crashes"]),
      "B14 live pedestrian-involved crashes (token 8, LIKE pattern)",
      VRU["pedestrian_involved"]["crashes"], live_ped,
      drift_note(live_ped, VRU["pedestrian_involved"]["crashes"]))
check(live_ok(live_ped_fat, VRU["pedestrian_involved"]["fatalities_people"]),
      "B15 live pedestrian fatalities (people)",
      VRU["pedestrian_involved"]["fatalities_people"], live_ped_fat,
      drift_note(live_ped_fat,
                 VRU["pedestrian_involved"]["fatalities_people"]))
check(live_ok(live_pedal, VRU["pedalcycle_involved"]["crashes"]),
      "B16 live pedalcycle-involved crashes (token 9, LIKE pattern)",
      VRU["pedalcycle_involved"]["crashes"], live_pedal,
      drift_note(live_pedal, VRU["pedalcycle_involved"]["crashes"]))

live_veh0 = live_count("Number_of_Motor_Vehicles = 0")
check(live_ok(live_veh0, VEH_ZERO_CLAIM), "B17 live rows with vehicles == 0",
      VEH_ZERO_CLAIM, live_veh0, drift_note(live_veh0, VEH_ZERO_CLAIM))

# Exactly-midnight, live: server filters the candidate set (timestamps whose
# UTC wall time is exactly 05:00:00 or 06:00:00 - the only UTC times that can
# be 00:00 in Chicago), then zoneinfo decides true local midnights among the
# returned epochs. New live rows dated after the snapshot window could add
# legitimate midnights, hence the drift rule.
cand_where = ("(EXTRACT(HOUR FROM Date_and_Time) = 5 OR "
              "EXTRACT(HOUR FROM Date_and_Time) = 6) AND "
              "EXTRACT(MINUTE FROM Date_and_Time) = 0 AND "
              "EXTRACT(SECOND FROM Date_and_Time) = 0")
cand_total = live_count(cand_where)
cand_epochs = []
offset = 0
while len(cand_epochs) < cand_total:
    page = live_query({"where": cand_where, "outFields": "Date_and_Time",
                       "orderByFields": "ObjectId", "resultOffset": offset,
                       "resultRecordCount": 2000, "f": "json"})
    feats = page.get("features", [])
    if not feats:
        break
    cand_epochs.extend(f["attributes"]["Date_and_Time"] for f in feats)
    offset += len(feats)
live_midnight = 0
for ms in cand_epochs:
    loc = local_from_epoch_ms(ms)
    if (loc.hour, loc.minute, loc.second, loc.microsecond) == (0, 0, 0, 0):
        live_midnight += 1
check(len(cand_epochs) == cand_total
      and live_ok(live_midnight, MIDNIGHT_CLAIM),
      "B18 live timestamps exactly 00:00 America/Chicago",
      MIDNIGHT_CLAIM,
      f"{live_midnight} (of {len(cand_epochs)} server-filtered "
      f"05:00/06:00-UTC candidates)",
      drift_note(live_midnight, MIDNIGHT_CLAIM))

print("\nNOTE on per-year live check: ArcGIS EXTRACT(YEAR FROM Date_and_Time) "
      "is a UTC year, not an America/Chicago local year, so a server-side "
      "groupBy cannot reproduce the local-year table without the candidate-"
      "fetch pattern used in B18. Per-year figures are verified strictly "
      "against the snapshot in A24/A25; the live total (B01) bounds any "
      "drift.")

# --------------------------------------------------------------------------
passed = sum(1 for ok, _ in RESULTS if ok)
total = len(RESULTS)
print("\n" + "=" * 78)
for ok, label in RESULTS:
    if not ok:
        print(f"FAILED: {label}")
print(f"RESULT: {passed}/{total} checks passed")
print("=" * 78)
sys.exit(0 if passed == total else 1)
