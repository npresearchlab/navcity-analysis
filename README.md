# NavCity Analysis

Tools for analyzing data from *NavCity*, a city-like naturalistic navigation task in virtual reality.

## What's Here?

This repository contains the **data analysis pipeline** for processing raw *NavCity* task data and generating outcome measures. These scripts calculate navigation performance metrics from participant trajectory and task completion data.

> **📌 Active Development Repository**  
> This is the actively maintained version of the *NavCity* analysis code. For frozen, publication-specific snapshots, see the paper repositories linked in [Related Publications](#related-publications).

Feel free to reach out to the Neural Plasticity Research Lab via our [website](https://npresearchlab.com) or contact Yasmine Bassil at [ybassil@emory.edu](mailto:ybassil@emory.edu) with any questions.

---

## Table of Contents

- [Overview](#overview)
- [Repository Structure](#repository-structure)
- [Code](#code)
- [Requirements](#requirements)
- [Usage](#usage)
- [Related Publications](#related-publications)
- [Related Resources](#related-resources)
- [License](#license)

---

## Overview

*NavCity* is an immersive, naturalistic, city-like virtual reality environment designed to study spatial navigation and allocentric (world-centered) spatial representation. This repository provides the data processing pipeline to extract meaningful navigation outcome measures from raw task data.

**Key Features:**

- Complete analysis pipeline from raw data to outcome measures
- Block-level and session-averaged metrics
- Path visualization tools
- Distance-based navigation metrics

---

## Repository Structure

```
navcity-analysis/
│
├── code/                             # Data processing and analysis scripts
│   ├── 0_runall.ipynb                # Master script to process all raw data
│   ├── 1_calculate_outcomes.ipynb    # Calculates outcome measures from raw NavCity data
│   ├── 2_merge_data.ipynb            # Merges outcome measures per block per participant
│   ├── 3_average_data.ipynb          # Averages outcome measures over blocks per participant
│   ├── 4_target_data.ipynb           # Creates dataframes for target paths per block
│   ├── 5_graph_data.ipynb            # Generates overhead path map visualizations
│   └── 6_distance_calc.ipynb         # Calculates distance-based navigation metrics
│
├── .gitignore
├── LICENSE
└── README.md
```

---

## Code

### `code/`

Contains Jupyter notebooks for processing and analyzing raw data from the *NavCity* task. These scripts generate the outcome variables and performance metrics used in downstream analyses.

| Script | Description |
|--------|-------------|
| `0_runall.ipynb` | Master orchestration script that runs all analysis scripts in sequence |
| `1_calculate_outcomes.ipynb` | Calculates outcome measures from raw *NavCity* data files |
| `2_merge_data.ipynb` | Collects outcome measures per block per participant into one dataframe |
| `3_average_data.ipynb` | Averages outcome measures over blocks per participant |
| `4_target_data.ipynb` | Creates dataframes for target paths per block across participants |
| `5_graph_data.ipynb` | Creates overhead path map visualizations per block across participants |
| `6_distance_calc.ipynb` | Calculates distance-based navigation metrics |

**⚠️ Important**: The `0_runall.ipynb` file contains hardcoded file paths. You must update file paths before running on your local machine. To get started, update the following variables:

- Set your local data directory path
- Set your local code directory path (for scripts 0 through 6)

Outputs from analysis scripts will be located in the *parent directory* of your data folder.

---

## Requirements

### Software Dependencies

**Python 3.8+** with the following packages:

```
numpy>=1.20.0
pandas>=1.3.0
matplotlib>=3.4.0
seaborn>=0.11.0
scipy>=1.7.0
jupyter>=1.0.0
```

### Hardware Requirements

- Minimum 8GB RAM recommended
- Standard computing hardware sufficient

---

## Usage

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/npresearchlab/navcity-analysis.git
   cd navcity-analysis
   ```

2. **Install dependencies:**
   ```bash
   pip install numpy pandas matplotlib seaborn scipy jupyter
   ```

3. **Run the analysis pipeline:**
   - Open `code/0_runall.ipynb` in your preferred IDE
   - Update file paths in the configuration section
   - Run all cells to process your data

---

## Related Publications

This analysis code has been used in the following publications. Each paper repository contains a frozen snapshot of the code used for that specific study:

- **CogMap Paper** (Bassil et al., 2026): [cogmap-paper](https://github.com/npresearchlab/cogmap-paper)  
  *Formation of allocentric representations after exposure to a novel, naturalistic, city-like, virtual reality environment*

- **NavAging Paper** (Bassil et al., 2025): [navaging-paper](https://github.com/npresearchlab/navaging-paper)  
  *Distinct aging-related profiles of allocentric knowledge recall following navigation in an immersive, naturalistic, city-like environment*

---

## Related Resources

- **NavCity Toolkit**: [NavCity_Toolkit](https://github.com/npresearchlab/NavCity_Toolkit) — Task source code, executable files, and implementation details
- **Lab Website**: [npresearchlab.com](https://npresearchlab.com)

---

## Lab Information

**Affiliation**: Neural Plasticity Research Lab, Emory University  
**Contact**: Dr. Michael Borich, PhD, DPT, PT ([mborich@emory.edu](mailto:mborich@emory.edu))  
**Lab Website**: [npresearchlab.com](https://npresearchlab.com)

---

## License

**Code**: [MIT License](LICENSE) — Code is freely available for reuse and modification

---

## Contributing

We welcome questions, bug reports, and suggestions for improvements. Please:

1. Check existing [Issues](https://github.com/npresearchlab/navcity-analysis/issues)
2. Open a new issue with detailed description
3. For questions, contact Dr. Michael Borich at mborich [at] emory.edu

---

**Last Updated**: December 2025  
**Repository Maintainer**: Yasmine Bassil, Neuroscience PhD Candidate, Neural Plasticity Research Lab, Emory University