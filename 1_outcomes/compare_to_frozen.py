#!/usr/bin/env python3
"""
Compare new NavCity outcomes with the files the NavAging paper used
(03_data/derivatives/frozen/navaging_paper), value by value.

    python compare_to_frozen.py [--new DIR] [--frozen DIR]

Prints the participants present in only one of the two and, per outcome, how
many values differ and by how much (--details: every differing value).
Writes nothing.

Since the corrections of 2026-11-11 (see 06_releases/paper_navaging/ERRATA.md)
Distance, Speed and Mean_Dwell differ for nearly everyone, and Orientation_Time
and Total_Time slightly for the first target of each block. Navigation_Time,
Teleportations and Mean_Teleport_Distance should match except for BNC39.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from metrics import OUTCOMES

STUDY = Path(__file__).resolve().parents[3]
TOL = 1e-6   # relative

# Where the NavAging paper's data has lived (it moved during the Nov 2026 reorganization)
FROZEN_CANDIDATES = [STUDY / '06_releases/paper_navaging/data',
                     STUDY / '03_data/derivatives/frozen/navaging_paper']


def load(path):
    df = pd.read_csv(path)
    return df.drop(columns=[c for c in df.columns if c.startswith('Unnamed')])


def compare(new, old, keys, label, details=False):
    print(f'\n=== {label}')
    np_, op = set(new['Participant']), set(old['Participant'])
    if np_ - op:
        print(f'  only in new: {sorted(np_ - op)}')
    if op - np_:
        print(f'  only in frozen: {sorted(op - np_)}')
    m = new.merge(old, on=keys, how='outer', suffixes=('_new', '_old'), indicator=True)
    m = m[m['Participant'].isin(np_ & op)]
    unmatched = m[m['_merge'] != 'both']
    if len(unmatched):
        print(f'  {len(unmatched)} rows without a match:')
        print(unmatched[keys + ['_merge']].to_string(index=False))
    m = m[m['_merge'] == 'both']
    print(f'  {len(m)} rows compared')
    for c in OUTCOMES:
        a, b = m[f'{c}_new'], m[f'{c}_old']
        same = (np.isclose(a, b, rtol=TOL, atol=1e-9)) | (a.isna() & b.isna())
        rel = ((a - b) / b.where(b != 0)).abs()[~same]
        print(f'  {c:24s} {int((~same).sum()):5d} differ'
              + (f'   median |change| {rel.median()*100:6.1f}%   max {rel.max()*100:7.1f}%' if (~same).any() and rel.notna().any() else ''))
        if details:
            for _, r in m[~same].iterrows():
                print(f'      {" ".join(str(r[k]) for k in keys):40s} '
                      f'frozen={r[f"{c}_old"]!s:>22} new={r[f"{c}_new"]!s:>22}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--new', type=Path, default=STUDY / '03_data/derivatives/navcity')
    ap.add_argument('--frozen', type=Path, default=None,
                    help='folder with the paper\'s ya_/oa_ files (default: the first of '
                         + ', '.join(str(c.relative_to(STUDY)) for c in FROZEN_CANDIDATES)
                         + ' that exists)')
    ap.add_argument('--details', action='store_true', help='list every differing value')
    a = ap.parse_args()
    if a.frozen is None:
        a.frozen = next((c for c in FROZEN_CANDIDATES if (c / 'ya_merged_results.csv').exists()), None)
        if a.frozen is None:
            ap.error('paper data not found; pass --frozen')
    print(f'new:    {a.new}\nfrozen: {a.frozen}')
    for g in ['ya', 'oa']:
        compare(load(a.new / f'{g}_merged_results.csv'), load(a.frozen / f'{g}_merged_results.csv'),
                ['Participant', 'Block_Num', 'Target_Name'], f'{g}_merged_results.csv', a.details)
        compare(load(a.new / f'{g}_averaged_results.csv'), load(a.frozen / f'{g}_averaged_results.csv'),
                ['Participant', 'Block_Num'], f'{g}_averaged_results.csv', a.details)


if __name__ == '__main__':
    main()
