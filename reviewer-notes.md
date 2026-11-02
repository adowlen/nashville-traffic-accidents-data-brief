# Reviewer notes - Nashville traffic accidents brief (2026-11-02)

## Claims most likely to be challenged

- Headline 30.2 percent (280 of 926 people killed were in pedestrian-involved crashes). Pressure points, all printed in the brief: involvement is read from harmful-event codes (verified against the description field exactly for pedestrians, 3,330 both ways); a crash where a pedestrian was present but not assigned the code would not be counted, and the brief says so in "What this might mean." The denominator is people killed in REPORTED crashes in the served window, not a vital-statistics count.
- The darkness gradient (fatal-crash share 1.14 percent dark-not-lighted vs 0.22 percent daylight, per reported crash). The exposure caveat is the whole game here: there is no miles-driven-by-lighting denominator, darkness travels with hour and road type, and the brief prints that in the finding, the chart title, and the alternative-explanation section. A reader who quotes the 5-to-1 figure as a per-mile risk is misquoting the package, but the package cannot control that; the wording was kept as "per reported crash" in every instance, including the hero-adjacent copy (the hero itself carries only the pedestrian figure).
- Finding 1's two series (volume down after 2019, fatal counts up then back). The reporting-mix alternative is unresolved and printed. The March-June 2020 dip supports part of the COVID reading for 2020 specifically; nothing in the layer separates a reporting change in 2021-2025 from a severity change.
- Precinct shares (Finding 6) are the softest geography in the package because of the completeness break (not-recorded share falls from about 12-13 percent to 0.05 percent across the window). The brief prints the break, claims no trend, and computes no rate. The chart repeats the caveat in its footnote.

## Checks that could not be completed

- Exposure normalization (per mile, per trip, per vehicle): not computable from this layer; no VMT or volume source was fused in. Every figure is therefore a count or a per-reported-crash share, with the limit stated prominently (standards section 3 handling).
- Crash counts at the 13 NDOT signal intersections named in the October 22 Nashville Focal report: not computed. The package cites the report for timing in the Who can act section only and claims no baseline or effect for those intersections; computing them would require treating the article's intersection list as a cohort definition, which the build did not do.
- As-of-investigation-final severity: not available. Records change during investigation (metadata); the window's last days (through October 31, pulled November 2) are the least settled, and the brief says so.
- What produces the minimally-coded subpopulation: the layer does not say. The brief and verification record the signature (identical null sets, definitional zeros, 0.2 percent hit-and-run Y) and the MNPD action asks for the reporting path to be recorded; the package does not assert which path it is.
- Alcohol, speed, and road-type separation for the illumination gradient: none of those fields exist in this layer in a usable form (the vehicle-count field has its own outage, Finding 8), so the gradient cannot be decomposed here.

## Findings that surprised us

- Hit-and-run crashes are LESS often injury crashes than other reported crashes (18.0 percent vs 35.1 percent), and they are 27.1 percent of all reported crashes with the field populated - both facts sit oddly next to a severity-first intuition and are printed as recorded.
- The pedestrian share of people killed (30.2 percent) against the pedestrian share of crashes (1.5 percent) is a 20-to-1 composition gap in a single layer.
- Fatal-crash counts in 2024-2025 (103, 100) returned to the 2019 level (100) while reported volume stayed in the post-2019 band, so the Finding 1 pattern is not monotone; the brief reports the return rather than smoothing it.
- The refresh drift was small and one-directional on harm: +61 rows, +14 injury crashes, +17 people injured, and no change in fatal crashes (865) or people killed (926) against the 2026-11-01 study snapshot.

## Flags

- This brief's findings concern crash-population patterns and the coding of a public dataset. No agency, department, or official is named as a finding subject; MNPD and NDOT appear only in the Who can act section as lever owners (standards section 11.3 flag, carried from the study).
- First publication use of the Traffic Accidents layer in the Machine Readable catalog (it entered the warehouse as a verified study layer on 2026-11-01): flagged as a first-use dataset under standards section 11.3.
- The NDOT timing item rests on a secondary source (The Nashville Focal, October 22, 2026) rather than an NDOT primary release; it is cited as a report, for timing only, and no figure depends on it. The Metro Council November 5 special meeting is verified from a Nashville.gov primary source (October 2, 2026 news release, plus the November 4-5 committee schedule PDF).
- Hero: generated illustration (a Nashville arterial at night, the same crosswalk lit by amber streetlights on the left and unlit on the right, a pedestrian visible in the light and barely visible in the dark), headline composited by code/hero_composite.py over a top gradient scrim, with all hero text generated from stats.json. Viewed during QA in this build: 30.2 percent headline, sub-line, and teal source line fully legible on the scrimmed dark field; the narrative scene is unobscured. Source art: hero_source/hero-art.webp. hero-headline.txt carries the headline figure and the story description.
- Charts: all four were viewed after the final render. Two earlier renders had footnote clipping and label overlaps; code/charts.py was rewritten with figure-level titles/footnotes and fixed margins, the year chart's fatal labels were given backing boxes and its bar labels moved inside the bars, and the final renders were re-viewed clean (see verification.md, adversarial note A7).
