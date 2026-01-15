#!/usr/bin/env python3
"""
NavCity Analysis Pipeline - Efficient Implementation

This script replaces the original Jupyter notebook pipeline with a more
efficient, maintainable Python implementation.

Usage:
    cd /path/to/navcity-analysis/code
    python run_analysis.py --data-folders /path/to/YA_Data /path/to/OA_Data

    # Or with individual steps:
    python run_analysis.py --data-folders /path/to/data --steps metrics merge average
    python run_analysis.py --data-folders /path/to/data --steps trajectories plots
    python run_analysis.py --data-folders /path/to/data --steps post-process

Key improvements over original notebooks:
- Vectorized pandas operations instead of row-by-row iteration
- Single-pass data processing where possible
- Proper memory management (closing matplotlib figures)
- Command-line interface for flexibility
- Modular design for easier testing and maintenance
- No Jupyter-specific magic commands (%store, %run)
"""

import argparse
import os
from pathlib import Path
from typing import List, Optional

from metrics import (
    process_raw_data,
    calculate_all_metrics,
    merge_block_results,
    average_metrics,
)
from visualization import (
    generate_participant_movement_plots,
    extract_target_trajectories,
    plot_target_maps,
)
from post_processing import post_analysis_cleanup


def get_participant_ids(data_folder: str) -> List[str]:
    """
    Get list of participant IDs from a data folder.

    Looks for directories starting with 'BNC' or 'NAV'.

    Args:
        data_folder: Path to the data folder

    Returns:
        Sorted list of participant IDs
    """
    participant_ids = []
    for item in os.listdir(data_folder):
        item_path = os.path.join(data_folder, item)
        if os.path.isdir(item_path) and (item.startswith('BNC') or item.startswith('NAV')):
            participant_ids.append(item)
    return sorted(participant_ids)


def run_metrics_calculation(data_folder: str, participant_ids: List[str], output_dir: Optional[str] = None) -> None:
    """
    Step 1: Calculate metrics for all participants and blocks.

    Creates b1_results.csv, b2_results.csv, b3_results.csv for each participant.

    Args:
        data_folder: Path to the input data folder
        participant_ids: List of participant IDs
        output_dir: Optional output directory (defaults to data_folder)
    """
    if output_dir is None:
        output_dir = data_folder

    print(f"\n{'='*60}")
    print("Step 1: Calculating metrics for all participants...")
    print(f"{'='*60}")

    total = len(participant_ids) * 3
    count = 0

    for pid in participant_ids:
        for block_num in range(1, 4):
            count += 1
            try:
                filepath = f"{data_folder}/{pid}/Saved_data_{pid}_t{block_num}.csv"
                data = process_raw_data(filepath)
                results = calculate_all_metrics(data)

                # Create participant output directory if needed
                participant_output_dir = os.path.join(output_dir, pid)
                os.makedirs(participant_output_dir, exist_ok=True)

                output_path = f"{participant_output_dir}/b{block_num}_results.csv"
                results.to_csv(output_path)

                print(f"[{count}/{total}] Created: {output_path}")

            except FileNotFoundError:
                print(f"[{count}/{total}] Warning: Data not found for {pid} block {block_num}")
            except Exception as e:
                print(f"[{count}/{total}] Error processing {pid} block {block_num}: {e}")


def run_merge(data_folder: str, participant_ids: List[str], output_dir: Optional[str] = None) -> None:
    """
    Step 2: Merge all block results into a single file.

    Creates merged_results.csv with all participants and blocks.

    Args:
        data_folder: Path to the input data folder
        participant_ids: List of participant IDs
        output_dir: Optional output directory (defaults to data_folder)
    """
    if output_dir is None:
        output_dir = data_folder

    print(f"\n{'='*60}")
    print("Step 2: Merging block results...")
    print(f"{'='*60}")

    # Use output_dir for reading block results if they were saved there
    merged_df = merge_block_results(output_dir, participant_ids)

    if not merged_df.empty:
        output_path = f"{output_dir}/merged_results.csv"
        merged_df.to_csv(output_path, index=False)
        print(f"Created: {output_path}")
        print(f"Total rows: {len(merged_df)}")
    else:
        print("Warning: No data to merge")


def run_average(data_folder: str, participant_ids: List[str], output_dir: Optional[str] = None) -> None:
    """
    Step 3: Calculate averaged metrics per participant per block.

    Creates averaged_results.csv with one row per participant per block.

    Args:
        data_folder: Path to the input data folder
        participant_ids: List of participant IDs
        output_dir: Optional output directory (defaults to data_folder)
    """
    if output_dir is None:
        output_dir = data_folder

    print(f"\n{'='*60}")
    print("Step 3: Averaging metrics across targets...")
    print(f"{'='*60}")

    # Use output_dir for reading block results if they were saved there
    averaged_df = average_metrics(output_dir, participant_ids)

    if not averaged_df.empty:
        output_path = f"{output_dir}/averaged_results.csv"
        averaged_df.to_csv(output_path, index=False)
        print(f"Created: {output_path}")
        print(f"Total rows: {len(averaged_df)}")
    else:
        print("Warning: No data to average")


def run_trajectories(data_folder: str, participant_ids: List[str], output_dir: Optional[str] = None) -> None:
    """
    Step 4: Extract target-specific trajectory data.

    Creates Target_Data/ folder with per-target coordinate files.

    Args:
        data_folder: Path to the input data folder
        participant_ids: List of participant IDs
        output_dir: Optional output directory (defaults to data_folder)
    """
    if output_dir is None:
        output_dir = data_folder

    print(f"\n{'='*60}")
    print("Step 4: Extracting target trajectories...")
    print(f"{'='*60}")

    extract_target_trajectories(data_folder, participant_ids, output_dir)


def run_plots(data_folder: str, participant_ids: List[str], output_dir: Optional[str] = None) -> None:
    """
    Step 5: Generate visualization plots.

    Creates movement plots for each participant and target maps.

    Args:
        data_folder: Path to the input data folder
        participant_ids: List of participant IDs
        output_dir: Optional output directory (defaults to data_folder)
    """
    if output_dir is None:
        output_dir = data_folder

    print(f"\n{'='*60}")
    print("Step 5: Generating plots...")
    print(f"{'='*60}")

    print("\nGenerating participant movement plots...")
    generate_participant_movement_plots(data_folder, participant_ids, output_dir)

    print("\nGenerating target maps...")
    plot_target_maps(output_dir)


def run_post_process(base_data_folder: str, output_dir: Optional[str] = None) -> None:
    """
    Step 6: Post-processing cleanup.

    Organizes files and fixes known data errors.

    Args:
        base_data_folder: Base data folder path (parent of YA_Data, OA_Data)
        output_dir: Optional output directory (defaults to base_data_folder)
    """
    if output_dir is None:
        output_dir = base_data_folder

    print(f"\n{'='*60}")
    print("Step 6: Post-processing cleanup...")
    print(f"{'='*60}")

    post_analysis_cleanup(output_dir)


def process_data_folder(
    data_folder: str,
    steps: Optional[List[str]] = None,
    output_dir: Optional[str] = None
) -> None:
    """
    Process a single data folder through the analysis pipeline.

    Args:
        data_folder: Path to the data folder
        steps: List of steps to run (default: all except post-process)
        output_dir: Optional output directory (defaults to data_folder)
    """
    if steps is None:
        steps = ['metrics', 'merge', 'average', 'trajectories', 'plots']

    if output_dir is None:
        output_dir = data_folder

    print(f"\n{'#'*60}")
    print(f"Processing: {data_folder}")
    if output_dir != data_folder:
        print(f"Output to: {output_dir}")
    print(f"{'#'*60}")

    # Get participant IDs
    participant_ids = get_participant_ids(data_folder)
    print(f"Found {len(participant_ids)} participants: {participant_ids[:5]}...")

    if not participant_ids:
        print("Warning: No participants found in folder")
        return

    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)

    # Run requested steps
    if 'metrics' in steps:
        run_metrics_calculation(data_folder, participant_ids, output_dir)

    if 'merge' in steps:
        run_merge(data_folder, participant_ids, output_dir)

    if 'average' in steps:
        run_average(data_folder, participant_ids, output_dir)

    if 'trajectories' in steps:
        run_trajectories(data_folder, participant_ids, output_dir)

    if 'plots' in steps:
        run_plots(data_folder, participant_ids, output_dir)


def main():
    parser = argparse.ArgumentParser(
        description='NavCity Analysis Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline on multiple data folders:
  python run_analysis.py --data-folders /path/to/YA_Data /path/to/OA_Data

  # Run only specific steps:
  python run_analysis.py --data-folders /path/to/data --steps metrics merge

  # Run post-processing only (requires base folder, not subfolders):
  python run_analysis.py --base-folder /path/to/data --steps post-process

  # Save outputs to a different directory:
  python run_analysis.py --data-folders /path/to/YA_Data --output-dir /path/to/results

Available steps:
  metrics      - Calculate navigation metrics for each participant/block
  merge        - Merge all block results into single file
  average      - Average metrics across targets per participant
  trajectories - Extract target-specific trajectory data
  plots        - Generate visualization plots
  post-process - Organize files and fix data errors (runs on base folder)
        """
    )

    parser.add_argument(
        '--data-folders',
        nargs='+',
        help='Paths to data folders (e.g., YA_Data, OA_Data)'
    )

    parser.add_argument(
        '--base-folder',
        help='Base data folder (parent of YA_Data, OA_Data) for post-processing'
    )

    parser.add_argument(
        '--output-dir',
        help='Output directory for results (defaults to data folder)'
    )

    parser.add_argument(
        '--steps',
        nargs='+',
        choices=['metrics', 'merge', 'average', 'trajectories', 'plots', 'post-process'],
        default=['metrics', 'merge', 'average', 'trajectories', 'plots'],
        help='Steps to run (default: all except post-process)'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.data_folders and not args.base_folder:
        parser.error("Must specify --data-folders or --base-folder")

    # Process each data folder
    if args.data_folders:
        non_post_steps = [s for s in args.steps if s != 'post-process']
        for i, folder in enumerate(args.data_folders):
            if not os.path.exists(folder):
                print(f"Warning: Folder not found: {folder}")
                continue

            # Determine output directory for this data folder
            if args.output_dir:
                # If multiple data folders, create subdirectories
                if len(args.data_folders) > 1:
                    folder_name = os.path.basename(folder.rstrip('/'))
                    output_dir = os.path.join(args.output_dir, folder_name)
                else:
                    output_dir = args.output_dir
            else:
                output_dir = None

            process_data_folder(folder, non_post_steps, output_dir)

    # Run post-processing if requested
    if 'post-process' in args.steps:
        base_folder = args.base_folder
        if not base_folder and args.data_folders:
            # Infer base folder from first data folder
            base_folder = str(Path(args.data_folders[0]).parent)

        output_dir = args.output_dir if args.output_dir else None

        if base_folder and os.path.exists(base_folder):
            run_post_process(base_folder, output_dir)
        else:
            print("Warning: Cannot run post-process without valid base folder")

    print(f"\n{'='*60}")
    print("Analysis complete!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
