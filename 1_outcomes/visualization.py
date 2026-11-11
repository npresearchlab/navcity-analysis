"""
Visualization functions for NavCity analysis.

This module handles trajectory plotting and map generation with proper
memory management (closing figures after saving).
"""

import os
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd

from metrics import TARGET_ORDER


# Color scheme for targets
TARGET_COLORS = {
    'Automobile shop': '#000000',
    'Police station ': '#ff0010',
    'Fire Station': '#ff55c2',
    'Bank': '#9250fb',
    'Pawn Shop': '#00b9ff',
    'Pizzeria': '#034cb4',
    'Quattroki Restaurant': '#00c359',
    'High School': '#ff8a33'
}

# Plot boundaries
X_LIMITS = (-80, 80)
Z_LIMITS = (-60, 80)


def plot_participant_movement(
    data: pd.DataFrame,
    output_path: str,
    title: Optional[str] = None
) -> None:
    """
    Plot movement trajectories for a single participant/block.

    Args:
        data: DataFrame from metrics.load_block()
        output_path: Path to save the figure
        title: Optional plot title
    """
    fig, ax = plt.subplots(figsize=(10, 8))

    for target_name, group in data.groupby('Target_Name'):
        color = TARGET_COLORS.get(target_name, '#000000')
        ax.plot(group['X'], group['Z'], color=color, label=target_name, alpha=0.7)

    ax.set_xlim(X_LIMITS)
    ax.set_ylim(Z_LIMITS)
    ax.set_xlabel('X Position')
    ax.set_ylabel('Z Position')

    if title:
        ax.set_title(title)

    ax.legend(loc='upper right', fontsize=8)

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def extract_target_trajectories(blocks: dict, output_dir) -> None:
    """
    Write per-target position files to <output_dir>/Target_Data/:
    b{1,2,3}_{target}_results.csv and all_{target}_results.csv.

    Args:
        blocks: {(participant_id, block_num): DataFrame from metrics.load_block}
        output_dir: outcomes output folder
    """
    target_data_dir = f"{output_dir}/Target_Data"
    os.makedirs(target_data_dir, exist_ok=True)

    block_data = {b: {t: [] for t in TARGET_ORDER} for b in range(1, 4)}
    all_data = {t: [] for t in TARGET_ORDER}

    for (pid, block_num), data in sorted(blocks.items()):
        for target in TARGET_ORDER:
            target_df = data[data['Target_Name'] == target]
            if target_df.empty:
                continue
            # Keep only unique positions (last occurrence)
            target_df = target_df.drop_duplicates(subset=['X', 'Z', 'Target_Name'], keep='last')
            result_df = target_df[['X', 'Z', 'Target_Name']].copy()
            result_df.insert(0, 'Participant', pid)
            result_df.insert(1, 'Block_num', block_num)
            block_data[block_num][target].append(result_df)
            all_data[target].append(result_df)

    for block_num in range(1, 4):
        for target in TARGET_ORDER:
            if block_data[block_num][target]:
                pd.concat(block_data[block_num][target], ignore_index=True).to_csv(
                    f"{target_data_dir}/b{block_num}_{target}_results.csv", index=False)
    for target in TARGET_ORDER:
        if all_data[target]:
            pd.concat(all_data[target], ignore_index=True).to_csv(
                f"{target_data_dir}/all_{target}_results.csv", index=False)
    print(f"Wrote trajectory files to {target_data_dir}")


def plot_target_maps(data_folder: str, blocks: list = None) -> None:
    """
    Generate overhead maps showing all participant trajectories for each target.

    Args:
        data_folder: Base data folder path
        blocks: List of blocks to plot (e.g., ['all', 'b1', 'b2', 'b3'])
    """
    if blocks is None:
        blocks = ['all', 'b1', 'b2', 'b3']

    target_data_dir = f"{data_folder}/Target_Data"
    maps_dir = f"{target_data_dir}/maps"

    for block in blocks:
        block_maps_dir = f"{maps_dir}/{block}"
        os.makedirs(block_maps_dir, exist_ok=True)

        for target in TARGET_ORDER:
            filepath = f"{target_data_dir}/{block}_{target}_results.csv"

            if not os.path.exists(filepath):
                print(f"Warning: {filepath} not found")
                continue

            df = pd.read_csv(filepath)

            if df.empty:
                continue

            fig, ax = plt.subplots(figsize=(10, 8))

            # Plot each participant's trajectory
            for (pid, block_num), group in df.groupby(['Participant', 'Block_num']):
                ax.plot(group['X'], group['Z'], alpha=0.5, linewidth=0.8)

            ax.set_xlim(X_LIMITS)
            ax.set_ylim(Z_LIMITS)
            ax.set_xlabel('X Position')
            ax.set_ylabel('Z Position')
            ax.set_title(f"{target} - {block}")

            output_path = f"{block_maps_dir}/{block}_{target}.png"
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close(fig)

