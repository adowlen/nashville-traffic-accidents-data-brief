# Nashville Traffic Accidents - a Machine Readable data brief

Of the 926 people killed in Nashville reported crashes from January 1, 2019 to October 31, 2026, 280 (30.2 percent) were pedestrians, and the fatal-crash share of reported crashes coded DARK - NOT LIGHTED is 1.14 percent (143 of 12,565) against 0.22 percent in DAYLIGHT (297 of 134,199), per reported crash. The layer holds 222,903 reported crashes, pulled November 2, 2026. All figures are reported crashes; the layer carries no traffic-volume denominator, so no per-mile or per-trip rate is computed anywhere in this package.

Part of Machine Readable: https://adowlen.github.io/machine-readable/

Repository: https://github.com/adowlen/nashville-traffic-accidents-data-brief

## Contents

- brief-draft.md - the brief (publishable text)
- stats.json - every figure used in the brief, produced by code/build_stats.py from the 2026-11-02 snapshot
- verification.md - methods checklist, Section 10 pre-flight audit record (AUDIT PASSED), internal controls, independent verifier record (51 of 51 checks passed), and Section 11.3 flags
- verification-ledger-independent.md - the independent verifier's recomputation ledger (summary of data/verify_independent_output.txt)
- reviewer-notes.md - claims most likely challenged, checks not completed, flags
- sources.md - dataset citations and the per-figure source audit
- social-drafts.md - LinkedIn draft (held for a future Friday synthesis under the Friday-only rule; Machine Readable never posts to X)
- hero-headline.txt - the headline figure and story description for the hero illustration
- hero.png - hero graphic (generated illustration in hero_source/hero-art.webp, headline figure composited by code/hero_composite.py over a top gradient scrim, with all text generated from stats.json; viewed during QA in the build run: a Nashville arterial at night, the same crosswalk lit on the left and unlit on the right, headline fully legible on the scrimmed dark field)
- charts/ - chart_yearly_crashes_fatal.png, chart_illumination_fatal_share.png, chart_collision_severity.png, chart_precinct_injury_share.png
- data/ - pull_log.json, audit_output.txt, verify_independent_output.txt, verify_independent_output.json, source-metadata.pdf (Traffic Accidents Metadata v2.0), by_year_panel.csv, jan_oct_by_year_panel.csv, by_precinct_panel.csv, by_collision_panel.csv, by_illumination_panel.csv, by_weather_panel.csv, zip_top10_panel.csv, intersections_top10_by_injury_panel.csv. The raw snapshot itself is the warehouse file stack/nashville/snapshots/2026-11-02/traffic_accidents_raw.parquet in the project stack (immutable; sha256 in data/pull_log.json), and code/build_stats.py also writes the cleaned layer to stack/nashville/layers/traffic_accidents_clean.parquet
- code/ - pull_data.py, build_stats.py, audit_section10.py, verify_independent.py, charts.py, hero_composite.py

## Dependencies (match code imports)

Python standard library (collections, datetime, hashlib, json, pathlib, sys, time, urllib, zoneinfo); matplotlib; numpy; pandas; Pillow; pyarrow; requests.

## Reuse and citation

Licensed CC-BY-4.0 (see LICENSE). Cite as: Machine Readable, "Nashville traffic accidents: pedestrians are 30.2 percent of the people killed in reported crashes, 2019-October 2026" (2026), https://github.com/adowlen/nashville-traffic-accidents-data-brief
