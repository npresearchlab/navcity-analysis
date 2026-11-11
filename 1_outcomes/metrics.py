"""
NavCity outcome calculations.

Reads one NavCity block from rawdata and computes one row of outcomes per
target. Based on the NavAging paper's notebooks
(06_releases/paper_navaging/data_analysis/1_calculate_outcomes.ipynb), with
the errors described in 06_releases/paper_navaging/ERRATA.md corrected
(2026-11-11): every frame is used, Distance is measured within each target,
and Mean_Dwell is per visit and leaves out the first visit (the start).
"""

import numpy as np
import pandas as pd

# rawdata target code -> name used in all outcome files (the names the
# program saved, which the figure/stats Rmds match on, trailing space included)
TARGETS = {
    'automobile_shop': 'Automobile shop',
    'police_station': 'Police station ',
    'fire_station': 'Fire Station',
    'bank': 'Bank',
    'pawn_shop': 'Pawn Shop',
    'pizzeria': 'Pizzeria',
    'quattroki_restaurant': 'Quattroki Restaurant',
    'high_school': 'High School',
}
TARGET_ORDER = list(TARGETS.values())

OUTCOMES = ['Total_Time', 'Orientation_Time', 'Navigation_Time', 'Distance',
            'Speed', 'Mean_Dwell', 'Teleportations', 'Mean_Teleport_Distance']

# Outcomes that can be summed across targets (time, distance, counts).
# Speed, Mean_Dwell and Mean_Teleport_Distance are per-target averages/ratios;
# a sum of them has no meaning, so they are only averaged.
SUMMABLE = ['Total_Time', 'Orientation_Time', 'Navigation_Time', 'Distance',
            'Teleportations']

START_X = 0.0
START_Z = -4.1


def load_block(filepath: str) -> pd.DataFrame:
    """Load one rawdata NavCity block file and prepare it for the metrics."""
    raw = pd.read_csv(filepath)

    unknown = set(raw['target_name']) - set(TARGETS) - {'mission_complete'}
    if unknown:
        raise ValueError(f'{filepath}: unknown target codes {sorted(unknown)}')

    # Every frame is used (the paper's code skipped the first 3; ERRATA 4)
    df = pd.DataFrame({
        'Target_Name': raw['target_name'],
        'X': raw['x'].astype(float),
        'Z': raw['z'].astype(float),
        'Time': raw['lapsed_time'].astype(float),
    })
    # Time between samples; lapsed_time restarts at each new target, which
    # gives a negative difference, set to 0
    df['Time_Diff'] = df['Time'].diff().clip(lower=0).fillna(0)

    df = df[df['Target_Name'] != 'mission_complete'].copy()
    df['Target_Name'] = df['Target_Name'].map(TARGETS)
    return df


def _target_metrics(group: pd.DataFrame) -> dict:
    m = {}
    known = group['X'].notna() & group['Z'].notna()
    at_start = known & (group['X'] == START_X) & (group['Z'] == START_Z)
    if known.all():
        m['Total_Time'] = group['Time_Diff'].sum()
        # Orientation: time at the start position
        m['Orientation_Time'] = group.loc[at_start, 'Time_Diff'].sum()
        m['Navigation_Time'] = m['Total_Time'] - m['Orientation_Time']
    else:
        # Some positions are NA in rawdata: time spent there is not known to be
        # orientation or navigation, so orientation and total time are NA.
        # Navigation time is still the time at known positions away from the start.
        m['Total_Time'] = np.nan
        m['Orientation_Time'] = np.nan
        m['Navigation_Time'] = group.loc[known & ~at_start, 'Time_Diff'].sum()

    # Unique positions in order of first visit (the program moves the
    # participant in discrete "teleport" steps). Rows with NA position are skipped.
    unique_pos = group[known].drop_duplicates(subset=['X', 'Z'], keep='first')
    steps = np.sqrt(unique_pos['X'].diff() ** 2 + unique_pos['Z'].diff() ** 2).iloc[1:]

    # Distance within this target only (the paper's code also counted the jump
    # from the previous target back to the start; ERRATA 1)
    m['Distance'] = steps.sum()
    m['Speed'] = m['Distance'] / m['Navigation_Time'] if m['Navigation_Time'] > 0 else np.nan

    # Dwell per visit: a visit is an unbroken run of frames at one position;
    # its dwell is the time from its first to its last frame. A position visited
    # again later is a new visit (decided 2026-11-11). The first visit (standing
    # at the start before moving) is left out: that time is orientation. (The
    # paper's code used one dwell per position and left out the position with
    # the smallest X instead; ERRATA 2.)
    g = group[known]
    visit = ((g['X'] != g['X'].shift()) | (g['Z'] != g['Z'].shift())).cumsum()
    t = g.groupby(visit, sort=True)['Time']
    dwell = (t.last() - t.first()).iloc[1:].tolist()
    m['Mean_Dwell'] = np.mean(dwell) if dwell else np.nan

    m['Teleportations'] = len(unique_pos)
    m['Mean_Teleport_Distance'] = steps.mean() if len(steps) else 0.0
    return m


def missing_positions(data: pd.DataFrame) -> pd.DataFrame:
    """Targets with NA positions: rows and seconds affected."""
    na = data['X'].isna() | data['Z'].isna()
    g = data[na].groupby('Target_Name')
    return pd.DataFrame({'rows_with_NA_position': g.size(),
                         'seconds_with_NA_position': g['Time_Diff'].sum()}).reset_index()


def calculate_all_metrics(data: pd.DataFrame) -> pd.DataFrame:
    """One row per target (index Target_Name, in canonical order)."""
    rows = {t: _target_metrics(g) for t, g in data.groupby('Target_Name')}
    df = pd.DataFrame.from_dict(rows, orient='index')[OUTCOMES]
    df.index.name = 'Target_Name'
    return df.reindex([t for t in TARGET_ORDER if t in df.index])


def summarise_blocks(by_target: pd.DataFrame, how: str) -> pd.DataFrame:
    """
    Collapse the per-target table to one row per participant and block.

    how='mean': mean over targets; a value set to NA (see corrections) is
        left out, so that block's mean uses the remaining targets.
    how='sum': sum over targets, for SUMMABLE outcomes only; if any target is
        NA the block total is NA (a sum over fewer targets is not comparable).
    """
    keys = ['Participant', 'Block_Num']
    g = by_target.groupby(keys, sort=False)
    if how == 'mean':
        return g[OUTCOMES].mean().reset_index()
    if how == 'sum':
        return g[SUMMABLE].agg(lambda s: s.sum(min_count=len(s))).reset_index()
    raise ValueError(how)
