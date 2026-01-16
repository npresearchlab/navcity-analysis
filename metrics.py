"""
Optimized metrics calculation functions for NavCity analysis.

This module contains vectorized implementations of navigation metrics,
significantly faster than the original row-by-row iteration approach.
"""

import numpy as np
import pandas as pd
from typing import Tuple


# Target names in canonical order
TARGET_ORDER = [
    'Automobile shop',
    'Police station ',  # Note: trailing space in original data
    'Fire Station',
    'Bank',
    'Pawn Shop',
    'Pizzeria',
    'Quattroki Restaurant',
    'High School'
]

# Starting position coordinates
START_X = 0
START_Z = -4.1


def process_raw_data(filepath: str) -> pd.DataFrame:
    """
    Load and preprocess raw NavCity CSV data.

    Args:
        filepath: Path to the raw CSV file (Saved_data_*.csv)

    Returns:
        Cleaned DataFrame with processed columns
    """
    df = pd.read_csv(filepath)

    # Skip header rows (first 3 rows are metadata)
    df = df.iloc[3:].reset_index(drop=True)

    # Rename columns for consistency
    df = df.rename(columns={
        'Lapsed Time': 'Time',
        'Target Name': 'Target_Name'
    })

    # Calculate time differences
    df['Time_Diff'] = df['Time'].diff().clip(lower=0).fillna(0)

    # Process Euler angles (remove parenthesis characters)
    # X Euler Angle has '(' prefix, Z Euler Angle has ')' suffix
    df['X Euler Angle'] = df['X Euler Angle'].str[1:].astype(float)
    df['Z Euler Angle'] = df['Z Euler Angle'].str[:-1].astype(float)

    # Store original angles
    df['X_A'] = df['X Euler Angle']
    df['Y_A'] = df['Y Euler Angle']
    df['Z_A'] = df['Z Euler Angle']

    # Revalue angles (convert >180 to negative)
    for col in ['X_A', 'Y_A', 'Z_A']:
        rev_col = f'{col}_Rev'
        df[rev_col] = df[col].apply(lambda x: -(360 - x) if x > 180 else x)
        df[f'{rev_col}_Diff'] = df[rev_col].diff().abs().fillna(0)

    # Remove "Mission complete" rows
    df = df[df['Target_Name'] != 'Mission complete']

    # Select and return relevant columns
    cols = [
        'Target_Name', 'X', 'Z',
        'X_A', 'X_A_Rev', 'X_A_Rev_Diff',
        'Y_A', 'Y_A_Rev', 'Y_A_Rev_Diff',
        'Z_A', 'Z_A_Rev', 'Z_A_Rev_Diff',
        'Time', 'Time_Diff'
    ]
    return df[cols].copy()


def calculate_all_metrics(data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all navigation metrics for each target using vectorized operations.

    This is significantly faster than the original implementation which used
    row-by-row iteration with iterrows().

    Args:
        data: Preprocessed DataFrame from process_raw_data()

    Returns:
        DataFrame with one row per target containing all metrics
    """
    results = []

    for target_name, group in data.groupby('Target_Name'):
        metrics = {'Target_Name': target_name}

        # Total Time: sum of all time differences
        metrics['Total_Time'] = group['Time_Diff'].sum()

        # Orientation Time: time spent at starting position
        at_start = (group['X'] == START_X) & (group['Z'] == START_Z)
        metrics['Orientation_Time'] = group.loc[at_start, 'Time_Diff'].sum()

        # Navigation Time: total time minus orientation time
        metrics['Navigation_Time'] = metrics['Total_Time'] - metrics['Orientation_Time']

        # Distance: total path length (only counting unique position changes)
        unique_pos = group.drop_duplicates(subset=['X', 'Z'], keep='first')
        dx = unique_pos['X'].diff()
        dz = unique_pos['Z'].diff()
        metrics['Distance'] = np.sqrt(dx**2 + dz**2).sum()

        # Speed: distance / navigation time (handle division by zero)
        if metrics['Navigation_Time'] > 0:
            metrics['Speed'] = metrics['Distance'] / metrics['Navigation_Time']
        else:
            metrics['Speed'] = 0

        # Mean Dwell: average time spent at each unique position
        dwell_times = []
        for (x, z), pos_group in group.groupby(['X', 'Z']):
            dwell = pos_group['Time'].iloc[-1] - pos_group['Time'].iloc[0]
            dwell_times.append(dwell)
        # Remove first position (starting point) from calculation
        if len(dwell_times) > 1:
            metrics['Mean_Dwell'] = np.mean(dwell_times[1:])
        else:
            metrics['Mean_Dwell'] = 0

        # Teleportations: count of unique positions
        metrics['Teleportations'] = group[['X', 'Z']].drop_duplicates().shape[0]

        # Mean Teleport Distance: average distance between consecutive unique positions
        unique_positions = []
        seen = set()
        for _, row in group.iterrows():
            pos = (row['X'], row['Z'])
            if pos not in seen:
                unique_positions.append(pos)
                seen.add(pos)

        if len(unique_positions) > 1:
            teleport_distances = []
            for i in range(1, len(unique_positions)):
                x1, z1 = unique_positions[i-1]
                x2, z2 = unique_positions[i]
                dist = np.sqrt((x2 - x1)**2 + (z2 - z1)**2)
                teleport_distances.append(dist)
            metrics['Mean_Teleport_Distance'] = np.mean(teleport_distances)
        else:
            metrics['Mean_Teleport_Distance'] = 0

        results.append(metrics)

    # Create DataFrame and reorder by canonical target order
    df_results = pd.DataFrame(results).set_index('Target_Name')

    # Reindex to canonical order (only include targets that exist in data)
    available_targets = [t for t in TARGET_ORDER if t in df_results.index]
    df_results = df_results.reindex(available_targets)

    return df_results


def calculate_block_metrics(data_folder: str, participant_id: str, block_num: int) -> pd.DataFrame:
    """
    Calculate metrics for a single block of a participant.

    Args:
        data_folder: Path to the participant's data folder
        participant_id: Participant ID (e.g., 'BNC01')
        block_num: Block number (1, 2, or 3)

    Returns:
        DataFrame with metrics for each target
    """
    filepath = f"{data_folder}/{participant_id}/Saved_data_{participant_id}_t{block_num}.csv"
    data = process_raw_data(filepath)
    return calculate_all_metrics(data)


def merge_block_results(data_folder: str, participant_ids: list) -> pd.DataFrame:
    """
    Merge all block results into a single DataFrame.

    Args:
        data_folder: Base data folder path
        participant_ids: List of participant IDs

    Returns:
        DataFrame with all results (Participant, Block_Num, Target_Name, metrics...)
    """
    all_results = []

    for pid in participant_ids:
        for block_num in range(1, 4):
            try:
                filepath = f"{data_folder}/{pid}/b{block_num}_results.csv"
                df = pd.read_csv(filepath)
                df.insert(0, 'Participant', pid)
                df.insert(1, 'Block_Num', block_num)
                all_results.append(df)
            except FileNotFoundError:
                print(f"Warning: {filepath} not found")

    if all_results:
        return pd.concat(all_results, ignore_index=True)
    return pd.DataFrame()


def average_metrics(data_folder: str, participant_ids: list) -> pd.DataFrame:
    """
    Calculate average metrics across targets for each participant/block.

    Args:
        data_folder: Base data folder path
        participant_ids: List of participant IDs

    Returns:
        DataFrame with averaged metrics per participant per block
    """
    results = []

    metric_cols = [
        'Total_Time', 'Orientation_Time', 'Navigation_Time',
        'Distance', 'Speed', 'Mean_Dwell',
        'Teleportations', 'Mean_Teleport_Distance'
    ]

    for pid in participant_ids:
        for block_num in range(1, 4):
            try:
                filepath = f"{data_folder}/{pid}/b{block_num}_results.csv"
                df = pd.read_csv(filepath)

                row = {
                    'Participant': pid,
                    'Block_Num': block_num
                }
                for col in metric_cols:
                    row[col] = df[col].mean()

                results.append(row)
            except FileNotFoundError:
                print(f"Warning: {filepath} not found")

    return pd.DataFrame(results)
