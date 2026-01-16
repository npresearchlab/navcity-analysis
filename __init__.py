"""
NavCity Analysis - Efficient Implementation

A refactored, more efficient version of the NavCity navigation analysis pipeline.

Modules:
    metrics: Navigation metric calculations (vectorized)
    visualization: Trajectory plotting and map generation
    post_processing: File organization and data corrections

Usage:
    # As a script:
    python -m efficient.run_analysis --data-folders /path/to/YA_Data /path/to/OA_Data

    # As a library:
    from efficient.metrics import process_raw_data, calculate_all_metrics
    from efficient.visualization import plot_participant_movement
"""

__version__ = "1.0.0"
