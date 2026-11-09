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
    output_folder: str,
    ya_subfolder: str = "YA_Data",
    oa_subfolder: str = "OA_Data"
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Organize analysis output files by moving and renaming them.

    Moves by_target_results.csv, by_block_total_results.csv, and
    by_block_mean_results.csv from YA_Data and OA_Data subfolders to the
    parent output folder with appropriate prefixes.

    Args:
        output_folder: Base output folder path (where results were saved)
        ya_subfolder: Name of young adults output folder
        oa_subfolder: Name of older adults output folder

    Returns:
        Tuple of (ya_target_path, ya_total_path, ya_mean_path,
                  oa_target_path, oa_total_path, oa_mean_path)
    """
    ya_folder = os.path.join(output_folder, ya_subfolder)
    oa_folder = os.path.join(output_folder, oa_subfolder)

    file_types = ['by_target_results', 'by_block_total_results', 'by_block_mean_results']
    results = {}

    print("Organizing and renaming analysis output files...")

    for age_prefix, folder in [('ya', ya_folder), ('oa', oa_folder)]:
        for file_type in file_types:
            src = os.path.join(folder, f"{file_type}.csv")
            dest = os.path.join(output_folder, f"{age_prefix}_{file_type}.csv")

            if os.path.exists(src):
                shutil.move(src, dest)
                print(f"Moved: {src} -> {dest}")
                results[f'{age_prefix}_{file_type}'] = dest
            else:
                print(f"Warning: {src} not found")
                results[f'{age_prefix}_{file_type}'] = None

    print("File organization completed!")

    return (
        results.get('ya_by_target_results'),
        results.get('ya_by_block_total_results'),
        results.get('ya_by_block_mean_results'),
        results.get('oa_by_target_results'),
        results.get('oa_by_block_total_results'),
        results.get('oa_by_block_mean_results'),
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


def post_analysis_cleanup(output_folder: str) -> None:
    """
    Run post-analysis cleanup operations.

    1. Organizes and renames output files
    2. Fixes known erroneous data (BNC39 Pawn Shop Orientation_Time)

    Args:
        output_folder: Base output folder path (where results were saved)
    """
    # Step 1: Organize files
    (ya_target, ya_total, ya_mean,
     oa_target, oa_total, oa_mean) = organize_and_rename_files(output_folder)

    # Step 2: Fix known errors
    # BNC39 has erroneous Orientation_Time for Pawn Shop in block 1
    if oa_target and oa_mean and os.path.exists(oa_target) and os.path.exists(oa_mean):
        fix_erroneous_data(
            merged_csv_path=oa_target,
            averaged_csv_path=oa_mean,
            participant='BNC39',
            block_num=1,
            target_name='Pawn Shop',
            column_to_fix='Orientation_Time'
        )

    print("Post-analysis cleanup completed!")


def combine_age_group_results(output_folder: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Combine YA and OA results into single DataFrames with age group labels.

    Args:
        output_folder: Base output folder path (where results were saved)

    Returns:
        Tuple of (combined_target_df, combined_total_df, combined_mean_df)
    """
    target_dfs = []
    total_dfs = []
    mean_dfs = []

    for prefix, age_group in [('ya', 'Young'), ('oa', 'Older')]:
        target_path = os.path.join(output_folder, f"{prefix}_by_target_results.csv")
        total_path = os.path.join(output_folder, f"{prefix}_by_block_total_results.csv")
        mean_path = os.path.join(output_folder, f"{prefix}_by_block_mean_results.csv")

        if os.path.exists(target_path):
            df = pd.read_csv(target_path)
            df.insert(0, 'Age_Group', age_group)
            target_dfs.append(df)

        if os.path.exists(total_path):
            df = pd.read_csv(total_path)
            df.insert(0, 'Age_Group', age_group)
            total_dfs.append(df)

        if os.path.exists(mean_path):
            df = pd.read_csv(mean_path)
            df.insert(0, 'Age_Group', age_group)
            mean_dfs.append(df)

    combined_target = pd.concat(target_dfs, ignore_index=True) if target_dfs else pd.DataFrame()
    combined_total = pd.concat(total_dfs, ignore_index=True) if total_dfs else pd.DataFrame()
    combined_mean = pd.concat(mean_dfs, ignore_index=True) if mean_dfs else pd.DataFrame()

    return combined_target, combined_total, combined_mean
