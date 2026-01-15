"""
Post-processing functions for NavCity analysis.

Handles file organization, renaming, and data corrections.
"""

import os
import shutil
from typing import Tuple, Optional

import numpy as np
import pandas as pd


def organize_and_rename_files(
    data_folder: str,
    ya_subfolder: str = "YA_Data",
    oa_subfolder: str = "OA_Data"
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Organize analysis output files by moving and renaming them.

    Moves merged_results.csv and averaged_results.csv from YA_Data and OA_Data
    folders to the parent data folder with appropriate prefixes.

    Args:
        data_folder: Base data folder path
        ya_subfolder: Name of young adults data folder
        oa_subfolder: Name of older adults data folder

    Returns:
        Tuple of (ya_merged_path, ya_averaged_path, oa_merged_path, oa_averaged_path)
    """
    ya_folder = os.path.join(data_folder, ya_subfolder)
    oa_folder = os.path.join(data_folder, oa_subfolder)

    results = {}

    print("Organizing and renaming analysis output files...")

    # Process YA_Data folder
    for file_type, prefix in [('merged', 'ya'), ('averaged', 'ya')]:
        src = os.path.join(ya_folder, f"{file_type}_results.csv")
        dest = os.path.join(data_folder, f"{prefix}_{file_type}_results.csv")

        if os.path.exists(src):
            shutil.move(src, dest)
            print(f"Moved: {src} -> {dest}")
            results[f'ya_{file_type}'] = dest
        else:
            print(f"Warning: {src} not found")
            results[f'ya_{file_type}'] = None

    # Process OA_Data folder
    for file_type, prefix in [('merged', 'oa'), ('averaged', 'oa')]:
        src = os.path.join(oa_folder, f"{file_type}_results.csv")
        dest = os.path.join(data_folder, f"{prefix}_{file_type}_results.csv")

        if os.path.exists(src):
            shutil.move(src, dest)
            print(f"Moved: {src} -> {dest}")
            results[f'oa_{file_type}'] = dest
        else:
            print(f"Warning: {src} not found")
            results[f'oa_{file_type}'] = None

    print("File organization completed!")

    return (
        results.get('ya_merged'),
        results.get('ya_averaged'),
        results.get('oa_merged'),
        results.get('oa_averaged')
    )


def fix_erroneous_data(
    merged_csv_path: str,
    averaged_csv_path: str,
    participant: str,
    block_num: int,
    target_name: str,
    column_to_fix: str
) -> None:
    """
    Fix erroneous data for a specific participant/block/target.

    Sets the specified column value to NaN and recalculates averages.

    Args:
        merged_csv_path: Path to merged results CSV
        averaged_csv_path: Path to averaged results CSV
        participant: Participant ID to fix
        block_num: Block number where error occurred
        target_name: Target name with error
        column_to_fix: Column containing erroneous data
    """
    print(f"Fixing {participant} {target_name} {column_to_fix} error...")

    # Load merged results
    df_merged = pd.read_csv(merged_csv_path)

    # Find and fix the erroneous row
    condition = (
        (df_merged['Participant'] == participant) &
        (df_merged['Block_Num'] == block_num) &
        (df_merged['Target_Name'] == target_name)
    )

    if not condition.any():
        print(f"Entry not found for {participant} block {block_num} {target_name}")
        return

    # If fixing Orientation_Time, also adjust Total_Time
    if column_to_fix == 'Orientation_Time':
        old_orientation = df_merged.loc[condition, 'Orientation_Time'].values[0]
        df_merged.loc[condition, 'Total_Time'] -= old_orientation

    # Set erroneous value to NaN
    df_merged.loc[condition, column_to_fix] = np.nan

    # Save corrected merged results
    df_merged.to_csv(merged_csv_path, index=False)
    print(f"Corrected merged results saved to {merged_csv_path}")

    # Recalculate average for this participant
    participant_data = df_merged[df_merged['Participant'] == participant]
    valid_values = participant_data[column_to_fix].dropna()

    if len(valid_values) > 0:
        new_avg = valid_values.mean()
        print(f"New average {column_to_fix} for {participant}: {new_avg:.6f}")

        # Update averaged results
        df_averaged = pd.read_csv(averaged_csv_path)
        participant_condition = df_averaged['Participant'] == participant

        if participant_condition.any():
            df_averaged.loc[participant_condition, column_to_fix] = new_avg
            df_averaged.to_csv(averaged_csv_path, index=False)
            print(f"Updated {participant}'s averaged {column_to_fix}")
    else:
        print(f"No valid {column_to_fix} values found for {participant}")


def post_analysis_cleanup(data_folder: str) -> None:
    """
    Run post-analysis cleanup operations.

    1. Organizes and renames output files
    2. Fixes known erroneous data (BNC39 Pawn Shop Orientation_Time)

    Args:
        data_folder: Base data folder path
    """
    # Step 1: Organize files
    ya_merged, ya_avg, oa_merged, oa_avg = organize_and_rename_files(data_folder)

    # Step 2: Fix known errors
    # BNC39 has erroneous Orientation_Time for Pawn Shop in block 1
    if oa_merged and oa_avg and os.path.exists(oa_merged) and os.path.exists(oa_avg):
        fix_erroneous_data(
            merged_csv_path=oa_merged,
            averaged_csv_path=oa_avg,
            participant='BNC39',
            block_num=1,
            target_name='Pawn Shop',
            column_to_fix='Orientation_Time'
        )

    print("Post-analysis cleanup completed!")


def combine_age_group_results(data_folder: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Combine YA and OA results into single DataFrames with age group labels.

    Args:
        data_folder: Base data folder path

    Returns:
        Tuple of (combined_merged_df, combined_averaged_df)
    """
    merged_dfs = []
    averaged_dfs = []

    for prefix, age_group in [('ya', 'Young'), ('oa', 'Older')]:
        merged_path = os.path.join(data_folder, f"{prefix}_merged_results.csv")
        averaged_path = os.path.join(data_folder, f"{prefix}_averaged_results.csv")

        if os.path.exists(merged_path):
            df = pd.read_csv(merged_path)
            df.insert(0, 'Age_Group', age_group)
            merged_dfs.append(df)

        if os.path.exists(averaged_path):
            df = pd.read_csv(averaged_path)
            df.insert(0, 'Age_Group', age_group)
            averaged_dfs.append(df)

    combined_merged = pd.concat(merged_dfs, ignore_index=True) if merged_dfs else pd.DataFrame()
    combined_averaged = pd.concat(averaged_dfs, ignore_index=True) if averaged_dfs else pd.DataFrame()

    return combined_merged, combined_averaged
