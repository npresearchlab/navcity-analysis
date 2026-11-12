# navcity_analysis

Code for the NavCity analyses: outcome measures from the recordings (time, distance, speed, …;
`1_outcomes/`, Python), figures (`2_figures/`) and statistics (`3_stats/`, R Markdown). The code
lives here; what it produces goes to `03_data/derivatives/navcity/` (outcome tables) and to an
analysis folder in `05_analyses/` (figures and statistics). Part of the nav_study project of the
Neural Plasticity Research Lab.
GitHub: https://github.com/npresearchlab/navcity-analysis

- [What NavCity is and what the code measures](#what-navcity-is)
- [Quick start](#quick-start)
- [Where this fits in nav_study](#where-this-fits-in-nav_study)
- [1_outcomes: how it works](#1_outcomes-how-it-works)
- [Output files](#output-files)
- [Outcome definitions](#outcome-definitions)
- [Common tasks](#common-tasks)
- [2_figures and 3_stats: figures and statistics](#2_figures-and-3_stats-figures-and-statistics)
- [Troubleshooting](#troubleshooting)
- [The NavAging paper and what changed](#the-navaging-paper-and-what-changed)
- [Code files](#code-files)

---

## What NavCity is

NavCity is a virtual city. In each **block** the participant is asked to find **8 targets**, always
in this order: Automobile shop, Police station, Fire Station, Bank, Pawn Shop, Pizzeria, Quattroki
Restaurant, High School. There are **3 blocks** (the same city and targets each time), so the
change across blocks shows learning.

For every target the participant starts at the same **start position**, (x, z) = (0, −4.1). They
first look around (orientation), then move to the target. Movement is in discrete jumps
("teleportations"), so the recording is a list of positions that changes every time they move.

The program saves one CSV per block with one row per frame (about 140 frames per second):
position (x, z), head angles, time since the block started and since the current target started,
and which target they are looking for.

From that, this code calculates, **per target**: how long it took (and how much of that was
orientation vs navigation), how far they moved, how fast, how long they paused at each spot, and
how many jumps they made. It then averages (or sums) these over the 8 targets of each block.

---

## Quick start

```
cd <nav_study>/04_code/navcity_analysis/1_outcomes
python3 run_outcomes.py
```

That is all for the usual case. It takes about 7 minutes on the lab server (it reads ~300 large
files) and writes the tables to `<nav_study>/03_data/derivatives/navcity/`. Run it again whenever
rawdata or `participants.tsv` changes; it always rebuilds everything from scratch.

Options:

| Command | What it does |
|---|---|
| `python3 run_outcomes.py` | Outcome tables |
| `python3 run_outcomes.py --plots` | Also per-target trajectory files and maps in `Target_Data/` (slower) |
| `python3 run_outcomes.py --output-dir /some/folder` | Write somewhere else (e.g. to try something without overwriting the real tables) |
| `python3 run_outcomes.py --study-root /path/to/nav_study` | If the code is not inside nav_study |
| `python3 compare_to_frozen.py` | Compare the tables with the data the NavAging paper used (see [below](#the-navaging-paper-and-what-changed)) |

**Requirements:** Python 3 with `pandas` and `numpy` (`matplotlib` for `--plots`):
`python3 -m pip install pandas numpy matplotlib`. Nothing else needs installing or configuring;
all paths are worked out from where the code sits in nav_study.

---

## Where this fits in nav_study

```
03_data/sourcedata/      files exactly as the NavCity program saved them (never changed)
        │   04_code/build_rawdata/build_rawdata.py
        ▼   (+ decisions in 02_participants/rawdata_corrections.tsv)
03_data/rawdata/         cleaned copies: standard names, columns, IDs; bad data set to NA
        │   04_code/navcity_analysis/1_outcomes/run_outcomes.py      ← this repository
        ▼   (+ age group and inclusion from 02_participants/participants.tsv)
03_data/derivatives/navcity/   outcome tables
        │   04_code/navcity_analysis/2_figures/, 3_stats/  (R Markdown, run_analysis.R)
        ▼   (+ who to analyse: sample.tsv in the analysis folder)
05_analyses/<analysis>/output/   figures and statistics, e.g. navcity_60subs
```

Rules that keep this working:

- **Never edit rawdata or the outcome tables by hand.** Both are rebuilt by scripts. To fix data,
  add a row to `02_participants/rawdata_corrections.tsv` and rebuild rawdata (see
  [Common tasks](#common-tasks)).
- **Data cleaning happens in rawdata, not in this code.** This code only calculates. Anyone
  using rawdata directly then gets the cleaned data too.
- **Who is included is decided in `02_participants`**, not in this code (see below).

| Folder here | What | Writes to |
|---|---|---|
| `1_outcomes/` | Python: outcome tables from rawdata | `03_data/derivatives/navcity/` |
| `2_figures/` | R Markdown: the figures | `05_analyses/<analysis>/output/figures/` |
| `3_stats/` | R Markdown: the statistics, one folder per analysis type | `05_analyses/<analysis>/output/stats/<folder>/` |
| `setup.R`, `run_analysis.R` | Shared R setup, and the script that runs 2_figures and 3_stats for one analysis | |

The code is here (one copy, in git); each folder in `05_analyses/` only holds who is analysed
(`sample.tsv`), its notes and results, and the outputs.

---

## 1_outcomes: how it works

`run_outcomes.py` does this, in order:

1. **Find the data.** Every file
   `03_data/rawdata/sub-<ID>/ses-beh/navcity/sub-<ID>_ses-beh_task-navcity_block-{1,2,3}.csv`.
   Only the behavioral session (`ses-beh`) is used; year-1 follow-ups (`ses-y1`) are not.
   Participants who do not have all 3 blocks are skipped and listed at the end of the run.
2. **Load each block** (`metrics.load_block`). Keeps target, x, z and `lapsed_time` (seconds
   since the current target started). Drops the `mission_complete` rows at the end. For every
   frame, the time since the previous frame is `Time_Diff` (0 at the first frame of each target).
   Target codes (`police_station`) are turned back into the names the program saved
   (`"Police station "`), because the R scripts use those names.
3. **Calculate the outcomes per target** (`metrics.calculate_all_metrics`); see
   [Outcome definitions](#outcome-definitions).
4. **Collect** all participants × blocks × targets into one table.
5. **Write the tables** (see [Output files](#output-files)):
   - participants with `incl_navcity_nara == 1` in `participants.tsv` → `all_merged_results.csv`
     and `per_participant/`, and, split by `age_group` (YA / OA), the `ya_` and `oa_` files plus
     their block means and block sums (`metrics.summarise_blocks`);
   - everyone else with 3 blocks (excluded) → `excluded/excluded_merged_results.csv` and
     `excluded/per_participant/`. This is the study's default for derived outputs
     (`01_methods/analysis_decisions.md`): the code rebuilds both sets from `participants.tsv`
     on every run, so never move files between them by hand.
6. **List** any targets with missing (NA) positions in `targets_with_NA_positions.tsv`.
7. With `--plots`: write per-target position files and maps (`visualization.py`).

### Missing data (NA)

Some frames in rawdata have NA position on purpose: data judged unusable (see
`03_data/rawdata/README.md` for every case). For a target with any NA position:

- `Orientation_Time` and `Total_Time` are **NA** (it is unknown whether that time was orientation
  or navigation);
- `Navigation_Time` is the time at known positions away from the start;
- Distance, Speed, dwell and teleportations use the known positions only.

In block means a NA target is left out (the mean of the other targets); in block sums it makes
the sum NA (a sum over 7 targets is not comparable with a sum over 8).

---

## Output files

All in `03_data/derivatives/navcity/`, rewritten on every run.

| File | One row per | Who |
|---|---|---|
| `ya_merged_results.csv`, `oa_merged_results.csv` | participant × block × target | included YA / OA |
| `ya_averaged_results.csv`, `oa_averaged_results.csv` | participant × block: **mean** of the 8 targets | included YA / OA |
| `ya_summed_results.csv`, `oa_summed_results.csv` | participant × block: **sum** of the 8 targets (Total_Time, Orientation_Time, Navigation_Time, Distance, Teleportations only) | included YA / OA |
| `all_merged_results.csv` | participant × block × target, with `Age_Group` and `incl_navcity_nara` columns | included YA and OA together |
| `per_participant/<ID>/b{1,2,3}_results.csv` | target | included |
| `excluded/excluded_merged_results.csv` | same as `all_merged_results.csv` | excluded participants with 3 blocks (`incl_navcity_nara` says why: excluded / unusable) |
| `excluded/per_participant/<ID>/b{1,2,3}_results.csv` | target | excluded participants with 3 blocks |
| `targets_with_NA_positions.tsv` | target with NA positions: how many frames and seconds | |
| `Target_Data/` (only with `--plots`) | position files per target and block, and map images | included participants |

"Included" = `incl_navcity_nara` is `1` in `02_participants/participants.tsv`. To change who is
included, change `02_participants/exclusions.tsv` and rebuild `participants.tsv` (see
`02_participants/README.md`), then rerun this code.

**Columns** in the `ya_`/`oa_` files: an unnamed row-number column first, then `Participant`,
`Block_Num` (1–3), `Target_Name` (merged files only), and the 8 outcomes below. The unnamed first
column, the file names and the target names (including the space at the end of
`"Police station "`) are exactly what the lab's R scripts expect; the R scripts drop the first
column with `select(-1)`. **Do not change these** without updating every R script.

---

## Outcome definitions

Per target. Times are in seconds; distances in NavCity (Unity) units.

| Column | Meaning |
|---|---|
| `Total_Time` | Time from the start of the target until it was reached (sum of `Time_Diff`) = Orientation_Time + Navigation_Time |
| `Orientation_Time` | Time at the start position (0, −4.1), including any later return to it |
| `Navigation_Time` | Total_Time − Orientation_Time (time away from the start) |
| `Distance` | Path length: take the positions in the order they were first visited, and add up the straight-line distances between consecutive ones |
| `Speed` | Distance / Navigation_Time (NA if Navigation_Time is 0) |
| `Mean_Dwell` | Average time per stop. A stop ("visit") is an unbroken run of frames at one position; its length is from its first to its last frame. Stopping again at a position visited earlier is a new visit. The first visit (standing at the start before moving) is left out, because that is orientation. |
| `Teleportations` | Number of different positions visited (including the start) |
| `Mean_Teleport_Distance` | Average distance between consecutive positions (Distance / (Teleportations − 1)) |

In the averaged files each column is the mean over the 8 targets of the block (so
`Total_Time` there is the average time per target, not the block's total; the summed files have
the totals).

---

## Common tasks

**A new participant was tested.** Add them to `02_participants` and put their files in
`03_data/sourcedata` (see `00_admin/adding_a_new_participant.md`), rebuild rawdata
(`python3 04_code/build_rawdata/build_rawdata.py`, then `python3 04_code/build_rawdata/check_rawdata.py`),
then run `python3 run_outcomes.py` here.

**Some NavCity data is bad and should not be used** (e.g. the participant stopped, the program
glitched). Do not delete it or edit files. Add a `set_na` row to
`02_participants/rawdata_corrections.tsv` (tab-separated), for example:

| participant_id | session | task | action | detail | reason |
|---|---|---|---|---|---|
| BNC39 | ses-beh | navcity | set_na | `block=1; frames=94340-156265; columns=x,z,x_euler,y_euler,z_euler` | what happened, who decided, date |

`frames` = the `frame` numbers in the rawdata file; `columns` can be any of x, z, x_euler,
y_euler, z_euler. Then rebuild rawdata for that person
(`python3 04_code/build_rawdata/build_rawdata.py --task navcity --participants BNC39`), run
`python3 04_code/build_rawdata/check_rawdata.py` (without `--participants`, so its report stays
complete), and rerun `run_outcomes.py`. The change is listed automatically in
`03_data/rawdata/changes_from_sourcedata.tsv`. Other kinds of fixes (wrong ID, restarted block,
which file to use) are other actions in the same file; see `02_participants/README.md`.

**Exclude a participant from analyses.** Do it in `02_participants/exclusions.tsv` (with the
reason), not here, then rebuild `participants.tsv` and re-run `run_outcomes.py`: their outcomes
move to `excluded/`. People with fewer than 3 blocks get no outcomes (listed at the end of the run).

**Try a change without touching the real tables.** Use `--output-dir` to write somewhere else.

**Add a new outcome.** Add it to `_target_metrics()` and to `OUTCOMES` in `metrics.py` (and to
`SUMMABLE` if a sum over targets makes sense), describe it in the table above, rerun.

---

## 2_figures and 3_stats: figures and statistics

```
cd <nav_study>/04_code/navcity_analysis
Rscript run_analysis.R ../../05_analyses/navcity_60subs              # everything (about 10 minutes)
Rscript run_analysis.R ../../05_analyses/navcity_60subs figures      # only the figures
Rscript run_analysis.R ../../05_analyses/navcity_60subs main_lmm     # only one 3_stats folder
Rscript run_analysis.R ../../05_analyses/navcity_60subs figures/1_average_plots.Rmd main_lmm   # single Rmds and folders
```

The argument is an analysis folder in `05_analyses/`. It must contain `sample.tsv` (columns
`participant_id`, `age_group`): the participants analysed. Everything the Rmds make goes into
that folder's `output/`, and `output/run_log.tsv` lists which Rmds ran and why any failed. Each
Rmd runs in its own fresh R session.

**Data** (`setup.R`, loaded by every Rmd): NavCity outcomes from `03_data/derivatives/navcity/`
(only the participants in `sample.tsv` are kept as each table is read); NARA, cognitive scores and
demographics from the NavAging paper's data, `06_releases/paper_navaging/data/` (read only).

| Folder | Rmds | What |
|---|---|---|
| `2_figures/` | `1_`…`8_*.Rmd` | Raincloud, by-block and by-target plots; NavCity–NARA correlations; NARA plots; OA high/low NARA cohort plots |
| `3_stats/main_lmm/` | `main_lmm_try.Rmd`, then `extract_pvalues_main.Rmd` | Age × block linear mixed models for each outcome; the p-value table for the figures (template: `pval_template_main.xlsx`) |
| `3_stats/cohorts_lmm/` | `cohorts_lmm.Rmd`, then `extract_pvalues_cohorts.Rmd` | Same with three groups: YA, OA high NARA, OA low NARA |
| `3_stats/corrs/` | `two_grp_corr_stats.Rmd` | Correlations between NavCity outcomes and NARA |
| `3_stats/sensitivity/` | `sensitivity_analysis_teleport_dist_FINAL.Rmd` | Teleport distance with outliers removed |
| `3_stats/nara/` | `1_` to `5_*.Rmd` | NARA scores: group statistics, the OA high/low cutoff (largest-gap method), age, young adults with low NARA |
| `3_stats/demographics/` | `1_` to `5_*.Rmd` | Sample description and group comparisons |

**These Rmds are the NavAging paper's** (copied from `06_releases/paper_navaging/`, 2026-11-11),
changed only where needed to run here; every change is marked `# FIX` in the Rmd:

- paths: data and outputs through `setup.R` / `run_analysis.R` instead of fixed drive paths;
- ggplot2 4: the gghalves half-point layer (figures 1, 6, 7) replaced by `geom_point()` with
  `position_jitter_left()` (in `setup.R`); gghalves is no longer maintained;
- figure 3: the composite figure asked for `p_teleport_dt`, which did not exist (the paper's
  composite failed; the single plots were fine);
- figures 5–7, `nara/3_nara_age_stats.Rmd`, `demographics/1_gender_age_stats.Rmd`: they expected
  `Group` as "YA"/"OA" and an `Age` (years) column, which the paper's frozen files do not have
  (`Group` is 0 = YA / 1 = OA there); `label_paper_groups()` in `setup.R` adds both.

**Still specific to the paper's 60 participants** (change before using them for another sample,
e.g. `05_analyses/navcity_allsubs`):

- the OA high / low NARA cutoff **3.5** is written into the Rmds (about 60 places; 3_stats/nara,
  cohorts_lmm, sensitivity, demographics, figures 5–8). For another sample, calculate it with
  `3_stats/nara/2_determine_nara_cohorts.Rmd` (largest gap between consecutive OA NARA scores)
  and make it a setting of the analysis;
- `3_stats/nara/4_ya_low_nara_nav_analysis.Rmd` and `5_low_nara_nonnav_analysis.Rmd` are about
  two named young adults (BNC01, BNC037) with low NARA;
- NARA and demographics come from the paper's files, which only cover these 60.

Analyses that use this code:

| Folder | What |
|---|---|
| `05_analyses/navcity_60subs` | The paper's 60 participants with the corrected outcomes; `RESULTS.md` compares with the paper |
| `05_analyses/navcity_allsubs` | Planned: everyone tested so far |

The paper's original R scripts, unchanged, are in `06_releases/paper_navaging/` (frozen: never
edit or save results there). To run them as they were, use ggplot2 3.5 (see
`06_releases/paper_navaging/REPRODUCE.md`).

---

## Troubleshooting

| Problem | Cause / fix |
|---|---|
| A participant is missing from the `ya_`/`oa_` files | Not all 3 blocks in rawdata (listed at the end of the run), or `incl_navcity_nara` is not 1, or no `age_group` in `participants.tsv`. Check `all_merged_results.csv` and the end of the run output. |
| `unknown target codes` error | rawdata has a target this code does not know. Check the rawdata file; if it is a real target, add it to `TARGETS` in `metrics.py`. |
| A participant was tested but has no rawdata | Rebuild rawdata (`04_code/build_rawdata/build_rawdata.py`); it prints what needs a decision. |
| `Resource busy` (from these or other scripts) | The lab server refuses to replace a file that is open somewhere (another computer, an open window). The rawdata scripts work around it; for anything else, close the file elsewhere and try again. |
| Numbers differ from the NavAging paper | Expected: errors in the paper's calculations were corrected (next section). |
| Very slow | Normal on the network drive (large files). Running from a computer on the lab network is faster than over VPN. |

---

## The NavAging paper and what changed

The NavAging paper's code and the exact data it used are frozen in `06_releases/paper_navaging`
(data in its `data/` folder). Use that to reproduce the paper, not this code.

On 2026-11-11 errors were found in the paper's outcome calculations and corrected here. Details,
sizes and which paper results they affect: `06_releases/paper_navaging/ERRATA.md`. In short:

| Outcome | Paper | This code |
|---|---|---|
| `Distance`, `Speed` | Also counted the jump from the previous target back to the start, at every target after the first | Only movement within the target (block means 10–28 % lower; Speed 24–35 % lower) |
| `Mean_Dwell` | One value per position; left out the position with the smallest X (usually not the start) | Per visit; leaves out the first visit (the start). Mostly lower, sometimes slightly higher |
| `Orientation_Time`, `Total_Time` (first target of each block) | First 3 frames of each block skipped | All frames used (at most 0.37 s more) |
| BNC39, block 1, Pawn Shop | 430 s pause at the start handled wrongly | Pause set to NA in rawdata; orientation and completion time NA |

`Navigation_Time`, `Teleportations` and `Mean_Teleport_Distance` are the same as in the paper
(except BNC39). `python3 compare_to_frozen.py` shows, per outcome, how many values differ from
the paper's data and by how much (`--details` lists every value). It writes nothing.

---

## Code files

| File | What is in it |
|---|---|
| `1_outcomes/run_outcomes.py` | The script to run: finds the data, calls `metrics.py`, writes the tables |
| `1_outcomes/metrics.py` | All calculations: `load_block` (read one rawdata file), `_target_metrics` (the outcomes of one target), `calculate_all_metrics` (all targets of a block), `summarise_blocks` (block means/sums), `missing_positions`. Also the target list (`TARGETS`), the start position and the outcome lists. |
| `1_outcomes/visualization.py` | `--plots`: per-target position files and maps |
| `1_outcomes/compare_to_frozen.py` | Comparison with the NavAging paper's data |
| `run_analysis.R` | Runs `2_figures/` and `3_stats/` for one analysis folder |
| `setup.R` | Loaded by every Rmd: data paths, the sample filter, and the fixes listed above |
| `2_figures/*.Rmd`, `3_stats/*/*.Rmd` | Figures and statistics (see the table above) |

### History

- 2025: original Jupyter notebooks, used for the NavAging paper (now in
  `06_releases/paper_navaging/data_analysis`).
- Jan 2026: rewritten as Python scripts.
- Nov 2026: moved into nav_study; reads the cleaned rawdata; the paper's calculation errors
  corrected; BNC39 cleaned in rawdata. The old copy in `YB/projects/2-beh-nav/code/navcity/` is
  no longer used.
