#!/usr/bin/env python3
"""
NavCity outcomes: rawdata -> per-target and per-block tables.

    python run_outcomes.py               # outcomes tables only
    python run_outcomes.py --plots       # also trajectory files and maps (slow)

Reads   03_data/rawdata/sub-*/ses-beh/navcity/*_task-navcity_block-{1,2,3}.csv
        02_participants/participants.tsv        (age group, inclusion)
Writes  03_data/derivatives/navcity/            (see README for every file)
        included participants (incl_navcity_nara == 1) at the top level, excluded
        participants in excluded/ (built from participants.tsv on every run; the
        study's default for derived outputs, 01_methods/analysis_decisions.md)

Paths are found from this file's location inside nav_study; use
--study-root or --output-dir to point elsewhere.
"""

import argparse
import glob
import os
import re
import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from metrics import (TARGETS, calculate_all_metrics, load_block,  # noqa: E402
                     missing_positions, summarise_blocks)

STUDY_ROOT = Path(__file__).resolve().parents[3]   # .../nav_study
SESSION = 'ses-beh'
BLOCKS = (1, 2, 3)
AGE_GROUPS = {'YA': ('ya', 'Young'), 'OA': ('oa', 'Older')}


# ------------------------------------------------------------------ inputs
def read_participants(study: Path) -> pd.DataFrame:
    p = pd.read_csv(study / '02_participants' / 'participants.tsv', sep='\t', dtype=str)
    return p.set_index('participant_id')


def find_blocks(study: Path) -> dict:
    """{participant_id: {block: path}} for every rawdata NavCity block file."""
    out = {}
    pattern = str(study / '03_data' / 'rawdata' / 'sub-*' / SESSION / 'navcity' /
                  f'sub-*_{SESSION}_task-navcity_block-*.csv')
    for f in glob.glob(pattern):
        m = re.search(r'sub-([A-Z]+\d+)_.*_block-(\d)\.csv$', f)
        out.setdefault(m.group(1), {})[int(m.group(2))] = f
    return out


# ------------------------------------------------------------------ outputs
def write_csv(df: pd.DataFrame, path: Path, index_col: bool = True) -> None:
    """
    index_col=True writes a leading unnamed 0..n-1 column, as the paper's
    files had: the figure/stats Rmds drop it with select(-1).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    df.reset_index(drop=True).to_csv(path, index=index_col, na_rep='NA')
    print(f'Wrote {path.relative_to(path.parents[2])}  ({len(df)} rows)')


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--study-root', type=Path, default=STUDY_ROOT)
    ap.add_argument('--output-dir', type=Path, default=None,
                    help='default: <study-root>/03_data/derivatives/navcity')
    ap.add_argument('--plots', action='store_true',
                    help='also write per-target trajectory files and maps')
    args = ap.parse_args()

    study = args.study_root
    out = args.output_dir or study / '03_data' / 'derivatives' / 'navcity'

    participants = read_participants(study)
    blocks = find_blocks(study)
    rows, skipped, loaded, missing = [], [], {}, []
    for pid in sorted(blocks):
        have = blocks[pid]
        if sorted(have) != list(BLOCKS):
            skipped.append((pid, f'blocks present: {sorted(have)}'))
            continue
        for b in BLOCKS:
            data = load_block(have[b])
            if args.plots:
                loaded[(pid, b)] = data
            res = calculate_all_metrics(data).reset_index()
            mp = missing_positions(data)
            if len(mp):
                mp.insert(0, 'Participant', pid)
                mp.insert(1, 'Block_Num', b)
                missing.append(mp)
            if len(res) != len(TARGETS):
                print(f'Note: {pid} block {b} has {len(res)} of {len(TARGETS)} targets')
            res.insert(0, 'Participant', pid)
            res.insert(1, 'Block_Num', b)
            rows.append(res)
        print(f'{pid}: done')

    by_target = pd.concat(rows, ignore_index=True)
    info = participants.reindex(by_target['Participant'])
    incl = info['incl_navcity_nara'].eq('1').values
    included = set(by_target['Participant'][incl])
    excl_dir = out / 'excluded'

    # Per participant, per block (same files as the original pipeline wrote).
    # Included -> per_participant/, excluded -> excluded/per_participant/; a person whose
    # inclusion changed is removed from the other folder.
    for (pid, b), df in by_target.groupby(['Participant', 'Block_Num']):
        home, other = (out, excl_dir) if pid in included else (excl_dir, out)
        p = home / 'per_participant' / pid / f'b{b}_results.csv'
        p.parent.mkdir(parents=True, exist_ok=True)
        df.drop(columns=['Participant', 'Block_Num']).to_csv(p, index=False, na_rep='NA')
        stale = other / 'per_participant' / pid
        if stale.exists():
            try:
                shutil.rmtree(stale)
                print(f'Moved {pid} out of {stale.parent.relative_to(out.parent)}')
            except OSError as e:
                print(f'WARNING: could not remove {stale} ({e}); delete it by hand')

    # One table per set, labelled with age group and inclusion status
    labelled = by_target.copy()
    labelled.insert(1, 'Age_Group', info['age_group'].values)
    labelled.insert(2, 'incl_navcity_nara', info['incl_navcity_nara'].values)
    write_csv(labelled[incl], out / 'all_merged_results.csv', index_col=False)        # YA + OA
    write_csv(labelled[~incl], excl_dir / 'excluded_merged_results.csv', index_col=False)

    # Analysis set: incl_navcity_nara == 1, split by age group
    for age, (prefix, _) in AGE_GROUPS.items():
        sel = by_target[incl & (info['age_group'] == age).values]
        write_csv(sel, out / f'{prefix}_merged_results.csv')
        write_csv(summarise_blocks(sel, 'mean'), out / f'{prefix}_averaged_results.csv')
        write_csv(summarise_blocks(sel, 'sum'), out / f'{prefix}_summed_results.csv')

    not_in_set = sorted(set(by_target['Participant'][~incl]))
    # Targets where rawdata has NA positions (see rawdata_corrections.tsv set_na rows):
    # Orientation_Time and Total_Time are NA there
    log = pd.concat(missing, ignore_index=True) if missing else pd.DataFrame(
        columns=['Participant', 'Block_Num', 'Target_Name', 'rows_with_NA_position', 'seconds_with_NA_position'])
    log['outcomes_set_to_NA'] = 'Orientation_Time, Total_Time'
    log_path = out / 'targets_with_NA_positions.tsv'
    log.to_csv(log_path, sep='\t', index=False)
    print(f'Wrote {log_path.name} ({len(log)} targets)')
    old_log = out / 'corrections_applied.tsv'
    if old_log.exists():
        old_log.unlink()   # replaced by targets_with_NA_positions.tsv (2026-11-11)
    if skipped:
        print('Skipped (not all 3 blocks in rawdata):')
        for pid, why in skipped:
            print(f'  {pid}: {why}')
    print(f'Excluded (incl_navcity_nara != 1), written to excluded/: '
          f'{", ".join(not_in_set) or "none"}')

    if args.plots:
        from visualization import extract_target_trajectories, plot_target_maps
        keep = {k: v for k, v in loaded.items()
                if participants.loc[k[0], 'incl_navcity_nara'] == '1'}
        extract_target_trajectories(keep, out)
        plot_target_maps(out)


if __name__ == '__main__':
    main()
