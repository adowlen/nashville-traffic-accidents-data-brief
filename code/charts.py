"""Data-drawn charts for the Nashville traffic accidents brief (2026-11-02).
Brand palette: dark charcoal, amber, teal. Every chart prints its
population, measure, and scope labels on the graphic itself (framing
standard): no figures from different scopes are juxtaposed without
their labels printed on the graphic.

Layout: titles and footnotes are figure-level text with fixed axes
margins (no tight_layout), so no footnote can clip or overlap an axis.
"""
import json
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parent.parent
stats = json.loads((ROOT / "stats.json").read_text())
CH = ROOT / "charts"
CH.mkdir(exist_ok=True)
CHARCOAL = "#23272b"; AMBER = "#f5a800"; TEAL = "#2a9d8f"; GREY = "#8a8f98"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": CHARCOAL,
                     "axes.edgecolor": CHARCOAL, "axes.labelcolor": CHARCOAL,
                     "xtick.color": CHARCOAL, "ytick.color": CHARCOAL})
SNAP = stats["snapshot_date"]
ROWS = stats["rows"]
MAXD = stats["coverage"]["datetime_local_max"][:10]
FOOT = (f"Source: Nashville Traffic Accidents layer (MNPD reported crashes, TITAN export), pulled {SNAP}. "
        f"All figures are reported crashes;\nthe layer carries no traffic-volume denominator, so no per-mile or per-trip rate is shown.")
FOOT_YEAR = (f"Bars sum to the 222,902 rows with counts populated; the 1 empty stub row (in 2020) is in the layer total of {ROWS:,} but in no bar.\n" + FOOT)


def frame(fig, title, foot, top=0.80, bottom=0.17, left=0.09, right=0.985):
    fig.text(0.012, 0.975, title, fontsize=10.5, va="top", ha="left")
    fig.text(0.012, 0.012, foot, fontsize=7.5, color=GREY, va="bottom", ha="left")
    fig.subplots_adjust(top=top, bottom=bottom, left=left, right=right)


def save(fig, name):
    fig.savefig(CH / name, dpi=200, facecolor="white")
    plt.close(fig)
    print(name)


# (a) Yearly reported crashes (bars) + fatal crashes (line, second axis)
by = stats["by_year"]
years = sorted(by.keys(), key=int)
complete = [y for y in years if by[y]["complete_year"]]
fig, ax = plt.subplots(figsize=(9.5, 5.4))
x = list(range(len(years)))
ax.bar(x, [by[y]["crashes"] for y in years],
       color=[TEAL if y in complete else GREY for y in years])
for xi, y in zip(x, years):
    lab = f"{by[y]['crashes']:,}" + ("\n(partial)" if y not in complete else "")
    ax.text(xi, by[y]["crashes"] - 3500, lab, ha="center", va="top", fontsize=8.5,
            color="white", fontweight="bold")
ax.set_xticks(x); ax.set_xticklabels(years)
ax.set_ylabel("Reported crashes per year")
ax.set_ylim(0, max(by[y]["crashes"] for y in years) * 1.20)
ax2 = ax.twinx()
ax2.plot(x, [by[y]["fatal_crashes"] for y in years], color=AMBER, marker="o", linewidth=2.5)
for xi, y in zip(x, years):
    ax2.annotate(f"{by[y]['fatal_crashes']}", (xi, by[y]["fatal_crashes"]),
                 textcoords="offset points", xytext=(0, 10), ha="center", fontsize=9,
                 color="#9a6d00", bbox=dict(facecolor="white", alpha=0.85, edgecolor="none", pad=1.2))
ax2.set_ylabel("Fatal crashes per year (line, amber)", color="#9a6d00")
ax2.tick_params(axis="y", labelcolor="#9a6d00")
ax2.set_ylim(0, max(by[y]["fatal_crashes"] for y in years) * 1.5)
ax.spines[["top"]].set_visible(False); ax2.spines[["top"]].set_visible(False)
frame(fig,
      "Reported crashes by year, with fatal crashes on a second axis\n"
      f"Population: all {ROWS:,} reported crashes, 2019-01-01 to {MAXD} (America/Chicago)\n"
      "Teal bars are complete years 2019-2025; the grey bar is the partial year (Jan-Oct frame) and is not a full year",
      FOOT_YEAR, top=0.79, bottom=0.15, left=0.075, right=0.915)
save(fig, "chart_yearly_crashes_fatal.png")

# (b) Fatal-crash share by illumination, counts printed on the graphic
ill = {r["category"]: r for r in stats["severity_by_illumination"]}
order = ["DAYLIGHT", "DUSK", "DAWN", "DARK - LIGHTED", "DARK - NOT LIGHTED"]
rows_b = [ill[k] for k in order if k in ill]
excluded = [r for r in stats["severity_by_illumination"] if r["category"] not in order]
excl_txt = "; ".join(f"{r['category']} {r['crashes']:,}" for r in excluded)
fig, ax = plt.subplots(figsize=(9.5, 5.2))
vals = [r["fatal_crash_share"] * 100 for r in rows_b]
ax.bar([r["category"] for r in rows_b], vals,
       color=[TEAL if r["category"] == "DAYLIGHT" else (AMBER if r["category"] == "DARK - NOT LIGHTED" else CHARCOAL) for r in rows_b])
for b, r in zip(ax.patches, rows_b):
    ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.05,
            f"{r['fatal_crash_share']*100:.2f}%\n{r['fatal_crashes']} fatal of {r['crashes']:,}",
            ha="center", fontsize=8.5)
ax.set_ylim(0, max(vals) * 1.5)
ax.set_ylabel("Fatal-crash share (%)")
ax.spines[["top", "right"]].set_visible(False)
frame(fig,
      "Fatal-crash share by lighting condition (Illumination_Description)\n"
      f"Population: reported crashes with a coded lighting condition, 2019-01-01 to {MAXD}; share = fatal crashes per reported crash in that condition\n"
      "A per-reported-crash severity share, NOT a risk per mile driven (no exposure denominator in this layer)",
      f"Not charted (printed here so no bucket is hidden; counts are crashes): {excl_txt}.\n"
      f"The unknown (null) bucket is largely the minimally-coded subpopulation, whose severity reads 0 by construction;\n"
      f"it is never a measured safe category.\n" + FOOT,
      top=0.79, bottom=0.20, left=0.055, right=0.99)
save(fig, "chart_illumination_fatal_share.png")

# (c) Injury / fatal shares by collision type; unknown bucket excluded and labeled
coll = [r for r in stats["severity_by_collision_type"]
        if r["category"] != "unknown (null)" and not r["small_n_flag"]]
unknown_bucket = next(r for r in stats["severity_by_collision_type"] if r["category"] == "unknown (null)")
small_rows = [r for r in stats["severity_by_collision_type"] if r["small_n_flag"]]
coll_sorted = sorted(coll, key=lambda r: r["injury_crash_share"])
labels = [r["category"].replace("NOT COLLISION W/MOTOR VEHICLE-TRANSPORT",
                                 "NOT COLLISION W/MOTOR\nVEHICLE-TRANSPORT") for r in coll_sorted]
fig, ax = plt.subplots(figsize=(9.5, 5.6))
ax.barh(labels, [r["injury_crash_share"] * 100 for r in coll_sorted], color=TEAL)
for i, r in enumerate(coll_sorted):
    ax.text(r["injury_crash_share"] * 100 + 1.2, i,
            f"{r['injury_crash_share']*100:.1f}% injury | {r['fatal_crash_share']*100:.2f}% fatal-crash (n = {r['crashes']:,})",
            va="center", fontsize=8.5)
ax.set_xlim(0, 118)
ax.tick_params(axis="y", labelsize=9)
ax.set_xlabel("Injury crashes as a share of reported crashes of that type (%)")
ax.spines[["top", "right"]].set_visible(False)
small_txt = "; ".join(f"{r['category']} (n = {r['crashes']})" for r in small_rows) or "none"
frame(fig,
      "Severity by collision type (Collision_Type_Description), coded categories only\n"
      f"Population: reported crashes with a coded collision type, 2019-01-01 to {MAXD}\n"
      "Bars are the injury share per reported crash of that type; the fatal-crash share and the crash count are printed beside each bar",
      f"EXCLUDED from the bars: the unknown (null) collision bucket ({unknown_bucket['crashes']:,} crashes) - a minimally-coded subpopulation whose 0% injury / 0% fatal\n"
      f"figures are definitional (detail fields never coded), not evidence that an unknown type is safe. Small-n category not charted: {small_txt}.\n" + FOOT,
      top=0.80, bottom=0.19, left=0.265, right=0.99)
save(fig, "chart_collision_severity.png")

# (d) Precinct panel: injury-crash share by precinct, known rows only
prec = sorted(stats["precinct"]["by_precinct"], key=lambda r: r["injury_crash_share"])
unk_rows = stats["precinct"]["unknown_rows"]
fig, ax = plt.subplots(figsize=(9.5, 5.2))
ax.barh([r["precinct"] for r in prec], [r["injury_crash_share"] * 100 for r in prec],
        color=[AMBER if r["precinct"] in ("Madison", "Southeast") else TEAL for r in prec])
for i, r in enumerate(prec):
    ax.text(r["injury_crash_share"] * 100 + 0.5, i,
            f"{r['injury_crash_share']*100:.1f}% injury (n = {r['crashes']:,}; {r['fatal_crashes']} fatal crashes)",
            va="center", fontsize=8.5)
ax.set_xlim(0, 52)
ax.set_xlabel("Injury crashes as a share of reported crashes in that precinct (%)")
ax.spines[["top", "right"]].set_visible(False)
frame(fig,
      "Injury-crash share by MNPD precinct - KNOWN-precinct rows only\n"
      f"Population: {stats['precinct']['known_rows']:,} reported crashes with a precinct recorded, 2019-01-01 to {MAXD}\n"
      "Cross-sectional all-window shares; no per-capita or per-mile rate (no precinct exposure denominator in this layer)",
      f"Completeness caveat: precinct is not recorded on {unk_rows:,} rows ({unk_rows/ROWS*100:.1f}% of all rows). The not-recorded share was about 12-13% of rows in 2019-2023,\n"
      f"8.6% in 2024, 2.4% in 2025 and 0.05% in 2026, so precinct figures are cross-sectional only; no precinct trend is claimed.\n" + FOOT,
      top=0.79, bottom=0.20, left=0.115, right=0.99)
save(fig, "chart_precinct_injury_share.png")
print("charts done")
