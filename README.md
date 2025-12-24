# Gate-Checked Functional Decomposition (GATE-FD)

**LLM-Assisted Quality Gates for Functional Decomposition in Systems Engineering**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Overview

This repository contains the implementation and experimental validation of **GATE-FD (Gate-Checked Functional Decomposition)**, a structured five-step workflow for LLM-assisted functional decomposition in systems engineering. The approach enforces explicit quality gates at FR→DP→IM domain transitions to prevent architectural drift and improve decomposition quality.

### Key Features

- **Five-Step Iterative Workflow**: Define/Refine FR → Select DP → Assign IM → Gate Review → Decision
- **Domain Separation Enforcement**: Prevents premature solution commitment through structured prompts
- **Quality Gate Validation**: FR↔DP, DP↔IM, and FR↔IM bridge checks based on Axiomatic Design principles
- **Automated Evaluation**: LLM-based evaluator using stopping-method taxonomy criteria
- **Experimental Validation**: N=30 trials across 10 NGHE requirements demonstrating 74% win rate vs. baseline
 
## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Usage](#usage)
  - [Running Single Decomposition](#running-single-decomposition)
  - [Running Experiments](#running-experiments)
  - [Exporting Results](#exporting-results)
- [Methodology](#methodology)
- [Experimental Results](#experimental-results)
- [Reproducibility](#reproducibility)
- [Citation](#citation)
- [License](#license)
- [Contact](#contact)

## Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key (for GPT-4 access)

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Cheol-SELab/functional-decomposition.git
   cd functional-decomposition
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API credentials**:
   ```bash
   cd src
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

## Quick Start

### Run a Single Decomposition

```bash
cd src
python -c "
from lfd import *
load_default_env()

# Load NGHE requirements
crs = load_nghe_customer_requirements('../example/NGHE_customer_requirements.md')

# Run GATE-FD workflow on first requirement
run_nghe_cr_and_save(
    cr=crs[0],
    outdir='../output',
    model_name='gpt-4o-mini'
)
"
```

### Run Full Experiment Suite

```bash
cd src
python run_experiment_suite.py \
    --cr-ids CR-NGHE-001 CR-NGHE-002 \
    --trials 30 \
    --outdir ../output \
    --model gpt-4o-mini
```

### Export Results to CSV

```bash
cd src
python export_evaluations_to_csv.py \
    --input-dir ../output \
    --output-summary ../output/evaluation_summary.csv \
    --output-by-cr ../output/evaluation_summary_by_cr.csv
```

## Project Structure

```
functional-decomposition/
├── README.md                          # This file
├── LICENSE                            # MIT License
├── requirements.txt                   # Python dependencies
├── src/                               # Source code
│   ├── .env.example                   # Environment template
│   ├── run_experiment_suite.py        # Main experiment runner
│   ├── export_evaluations_to_csv.py   # Results aggregation
│   └── lfd/                           # Core library
│       ├── __init__.py                # Package exports
│       ├── workflow.py                # GATE-FD workflow implementation
│       ├── baseline.py                # Single-pass baseline
│       ├── evaluator.py               # LLM-based evaluator
│       ├── experiment.py              # Comparison experiments
│       ├── experiment_suite.py        # Batch experiment runner
│       ├── llm.py                     # LLM client with retry logic
│       ├── nghe.py                    # NGHE dataset parser
│       ├── output.py                  # JSON output utilities
│       ├── runners.py                 # High-level runners
│       └── env.py                     # Environment loader
├── example/                           # Example inputs
│   └── NGHE_customer_requirements.md  # 10 NGHE requirements
├── output/                            # Experimental outputs
│   ├── *.json                         # Individual trial results
│   ├── evaluation_*.json              # Evaluation results
│   └── *.csv                          # Aggregated statistics
└── doc/                               # Documentation (if present)
```

## Usage

### Running Single Decomposition

The GATE-FD workflow decomposes a customer requirement through five iterative steps:

```python
from lfd import *

# Load environment and requirements
load_default_env()
crs = load_nghe_customer_requirements('example/NGHE_customer_requirements.md')

# Run GATE-FD workflow
run_nghe_cr_and_save(
    cr=crs[0],                    # Customer requirement
    outdir='output',              # Output directory
    model_name='gpt-4o-mini',     # LLM model
    temperature=0.0,              # Deterministic sampling
    max_output_tokens=2048        # Token limit
)
```

### Running Experiments

Compare GATE-FD against baseline across multiple trials:

```python
from lfd import *

# Configure experiment
config = ExperimentSuiteConfig(
    cr_ids=['CR-NGHE-001', 'CR-NGHE-002'],
    trials_per_cr=30,
    outdir='output',
    model_name='gpt-4o-mini'
)

# Run experiment suite
run_nghe_experiment_suite_to_csv(
    config=config,
    csv_path='output/results.csv',
    skip_existing=True  # Resume interrupted runs
)
```

### Exporting Results

Aggregate individual trial JSONs into statistical summaries:

```bash
python export_evaluations_to_csv.py \
    --input-dir output \
    --output-summary output/evaluation_summary.csv \
    --output-by-cr output/evaluation_summary_by_cr.csv
```

Output CSV includes:
- Win/Loss/Tie counts
- Mean ± standard deviation of total scores
- Paired sign-test p-values
- Per-category breakdowns

## Methodology

### GATE-FD Workflow

The five-step iterative workflow enforces domain separation and validation:

1. **Define/Refine FR**: Ensure functional requirements are atomic, solution-neutral, and testable
2. **Select DP**: Choose design parameters that satisfy FRs while maintaining independence
3. **Assign IM**: Map DPs to implementation modules with clear containment boundaries
4. **Gate Review**: Validate FR↔DP, DP↔IM, and FR↔IM mappings against quality criteria
5. **Decision**: Stop, zigzag down to next level, or revise current level

### Baseline Comparison

The baseline approach produces all five artifacts in a single LLM call without iterative validation.

### Evaluation Criteria

Decomposition quality is assessed across five dimensions:
- **Pure FR**: Atomicity, solution-neutrality, testability
- **FR↔DP Bridge**: Independence Axiom, coupling awareness, complexity minimization
- **DP↔IM Bridge**: Containment quality, diffusion risk management
- **Pure IM**: Structural modularity evidence
- **FR↔IM Bridge**: Verifiability, allocation boundary clarity

Each dimension is scored 1-5 (or N/A) by an independent LLM evaluator.

## Experimental Results

### Dataset

10 customer requirements from Next Generation Heavy Equipment (NGHE) case study:
- Productivity metrics (CR-NGHE-001, 002)
- Worksite analysis (CR-NGHE-006, 007)
- Autonomy and teleoperation (CR-NGHE-009, 010, 012, 014)
- Security/logging (CR-NGHE-021, 024)

### Key Findings (N=30 trials per requirement)

| Metric | GATE-FD | BASELINE |
|--------|---------|----------|
| **Win Rate** | 74% (254/345) | 19% (66/345) |
| **Mean Score** | 20.1 ± 1.1 | 17.9 ± 2.3 |
| **Significant Improvements** | 7/10 requirements (p < 0.05) | — |
| **Very Strong Significance** | 5/10 requirements (p < 0.001) | — |

**Effect Sizes**: +1.3 to +4.9 points across significant requirements

**Statistical Power**: Increased sample size (N=30 vs. initial N=10) strengthened confidence, with previously borderline cases (CR-NGHE-006, CR-NGHE-010) achieving significance.

## Reproducibility

All experimental outputs are deterministic (temperature=0.0) and timestamped. To reproduce results:

1. **Set up environment**:
   ```bash
   pip install -r requirements.txt
   cp src/.env.example src/.env
   # Add your OpenAI API key to .env
   ```

2. **Run experiments**:
   ```bash
   cd src
   python run_experiment_suite.py \
       --cr-ids CR-NGHE-001 CR-NGHE-002 CR-NGHE-006 CR-NGHE-007 \
                CR-NGHE-009 CR-NGHE-010 CR-NGHE-012 CR-NGHE-014 \
                CR-NGHE-021 CR-NGHE-024 \
       --trials 30 \
       --outdir ../output \
       --model gpt-4o-mini
   ```

3. **Generate statistics**:
   ```bash
   python export_evaluations_to_csv.py \
       --input-dir ../output \
       --output-by-cr ../output/evaluation_summary_by_cr_n30.csv
   ```

**Note**: LLM outputs may vary slightly due to model updates, tokenization changes, or non-deterministic floating-point operations, even with temperature=0.0.
 
## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
