# navcity_analysis

NavCity analysis for nav_study: outcomes from rawdata, then figures, then stats.

| Folder | What | Reads | Writes |
|---|---|---|---|
| `1_outcomes/` | Per-target and per-block NavCity outcomes (Python) | `03_data/rawdata`, `02_participants` | `03_data/derivatives/navcity/` |
| `2_figures/` | Figure scripts (R Markdown) | `03_data/derivatives/navcity/` | figures |
| `3_stats/` | Statistics scripts (R Markdown) | `03_data/derivatives/navcity/` | stats tables |

The NavAging paper's code is frozen in `06_releases/paper_navaging` (with the data it used in its
`data/` folder; until 2026-11-11 that data was in `03_data/derivatives/frozen/navaging_paper`).
Do not edit it; copy its Rmds into `2_figures/` or
`3_stats/` as a starting point and set `data_path` to `03_data/derivatives/navcity`.

---

## 1_outcomes

```
cd 04_code/navcity_analysis/1_outcomes
python3 run_outcomes.py            # tables (about 7 minutes on the server)
python3 run_outcomes.py --plots    # also Target_Data/ trajectory files and maps
python3 compare_to_frozen.py       # how much the outcomes differ from the NavAging paper's
```

Needs Python 3 with pandas, numpy (and matplotlib for `--plots`). All paths come from the
folder layout; `--study-root` / `--output-dir` override them.

### Input

- `03_data/rawdata/sub-*/ses-beh/navcity/sub-*_ses-beh_task-navcity_block-{1,2,3}.csv`.
  Participants without all 3 blocks are skipped (listed when the script runs). Year-1
  (`ses-y1`) sessions are not used.
- `02_participants/participants.tsv`: `age_group` (YA / OA) and `incl_navcity_nara`.
- Data cleaning is done in rawdata, not here. Positions that rawdata has as `NA` (see
  `03_data/rawdata/README.md`) are skipped: a target with any NA position gets NA
  `Orientation_Time` and `Total_Time` (it is unknown where that time was spent);
  `Navigation_Time` is the time at known positions away from the start, and the other
  outcomes use the known positions.

### Output (`03_data/derivatives/navcity/`)

| File | Rows | Who |
|---|---|---|
| `ya_merged_results.csv`, `oa_merged_results.csv` | one per participant, block, target | `incl_navcity_nara == 1` |
| `ya_averaged_results.csv`, `oa_averaged_results.csv` | one per participant, block: **mean over the 8 targets** | same |
| `ya_summed_results.csv`, `oa_summed_results.csv` | one per participant, block: **sum over the 8 targets** (time, distance, count outcomes only) | same |
| `all_merged_results.csv` | per target, with `Age_Group` and `incl_navcity_nara` columns | everyone with 3 blocks |
| `per_participant/<ID>/b{1,2,3}_results.csv` | per target | everyone with 3 blocks |
| `targets_with_NA_positions.tsv` | targets whose rawdata has NA positions: rows and seconds affected | |
| `Target_Data/` (with `--plots`) | unique positions per target; maps | `incl_navcity_nara == 1` |

The `ya_/oa_` files have the same names, columns and target names (`"Police station "` with
its trailing space) as the files the NavAging paper's Rmds read, including the leading unnamed
index column that those Rmds remove with `select(-1)`. Keep it that way, or update every Rmd.

`NA` = not available. In `*_averaged_results.csv` a NA target is left out of that block's mean;
in `*_summed_results.csv` it makes that block's sum NA (a sum over fewer targets is not
comparable).

### Outcomes (per target)

| Column | Meaning |
|---|---|
| `Total_Time` | Seconds from target start to reaching it (= Orientation_Time + Navigation_Time) |
| `Orientation_Time` | Seconds at the start position (0, −4.1), including any later return to it |
| `Navigation_Time` | Total_Time − Orientation_Time |
| `Distance` | Path length within the target: sum of the distances between consecutive unique positions, in visiting order |
| `Speed` | Distance / Navigation_Time (NA if Navigation_Time is 0) |
| `Mean_Dwell` | Mean seconds per visit. A visit is an unbroken run of frames at one position (first to last frame); a position visited again later is a new visit. The first visit (standing at the start before moving) is left out. |
| `Teleportations` | Number of unique positions |
| `Mean_Teleport_Distance` | Mean distance between consecutive unique positions |

All frames of each block file are used.

### Cleaned data in use

| Participant | Block / target | In rawdata | Effect on outcomes |
|---|---|---|---|
| BNC39 | 1 / Pawn Shop | Positions NA for the 430 s at the start before moving | Orientation_Time, Total_Time = NA; Mean_Dwell no longer includes the 430 s |

### Differences from the NavAging paper

Corrected on 2026-11-11; details and sizes in `06_releases/paper_navaging/ERRATA.md`. Results
from this code are **not** directly comparable with the paper's for these outcomes:

| Outcome | Paper | Now |
|---|---|---|
| `Distance`, `Speed` | Included the jump from the previous target back to the start at every target after the first | Within the target only (block means 10 to 28 % lower; Speed 24 to 35 % lower) |
| `Mean_Dwell` | One dwell per position; left out the position with the smallest X (usually not the start) | Per visit; leaves out the first visit (the start) |
| `Orientation_Time`, `Total_Time` of the first target | First 3 frames of each block skipped | All frames used (at most 0.37 s more) |
| BNC39 | See ERRATA 3 | Cleaned in rawdata (above) |

`Navigation_Time`, `Teleportations` and `Mean_Teleport_Distance` are unchanged except for BNC39.
To reproduce the paper, use the release (`06_releases/paper_navaging`), not this code.

### History

Refactored from the paper's notebooks (`06_releases/paper_navaging/data_analysis`) in
Jan 2026; rewritten to read rawdata and moved here, and the paper's outcome errors corrected,
on 2026-11-11. The previous copy at
`projects/2-beh-nav/code/navcity/get_navcity_outcomes` is superseded by this one.
