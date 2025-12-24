# GATE-FD Project Structure

This document provides a detailed overview of the project organization for the Gate-Checked Functional Decomposition (GATE-FD) research implementation.

## Directory Structure

```
functional-decomposition/
│
├── README.md                          # Main project documentation
├── LICENSE                            # MIT License
├── CHANGELOG.md                       # Version history and updates
├── CONTRIBUTING.md                    # Contribution guidelines
├── USAGE.md                           # Detailed usage examples
├── PROJECT_STRUCTURE.md               # This file
├── requirements.txt                   # Python dependencies
├── .gitignore                         # Git ignore rules
│
├── src/                               # Source code
│   ├── .env.example                   # Environment template
│   ├── .env                           # API keys (gitignored)
│   │
│   ├── run_experiment_suite.py        # CLI: Run experiments
│   ├── export_evaluations_to_csv.py   # CLI: Export results
│   │
│   └── lfd/                           # Core library package
│       ├── __init__.py                # Package exports
│       ├── workflow.py                # GATE-FD workflow (5 steps)
│       ├── baseline.py                # Single-pass baseline
│       ├── evaluator.py               # LLM-based evaluator
│       ├── experiment.py              # Comparison experiments
│       ├── experiment_suite.py        # Batch experiment runner
│       ├── llm.py                     # LLM client with retry
│       ├── nghe.py                    # NGHE dataset parser
│       ├── output.py                  # JSON output utilities
│       ├── runners.py                 # High-level runners
│       └── env.py                     # Environment loader
│
├── example/                           # Example inputs
│   └── NGHE_customer_requirements.md  # 10 NGHE requirements
│
├── output/                            # Experimental outputs (gitignored)
│   ├── ours_workflow_*.json           # GATE-FD decompositions
│   ├── baseline_single_pass_*.json    # Baseline decompositions
│   ├── evaluation_*.json              # Evaluation results
│   ├── evaluation_summary.csv         # Per-trial statistics
│   └── evaluation_summary_by_cr.csv   # Aggregated by requirement
│
└── doc/                               # Additional documentation (optional)
    └── (LaTeX paper files if included)
```

## Core Modules

### 1. `workflow.py` - GATE-FD Implementation

**Purpose**: Implements the five-step iterative decomposition workflow.

**Key Classes**:
- `DecompositionInputs`: Input data structure (mission, stakeholders, constraints, FR)
- `DecompositionRun`: Output data structure (refined FR, DP, IM, gates, decision)
- `DecompositionWorkflow`: Main workflow orchestrator

**Key Methods**:
- `run_one_level()`: Execute complete 5-step workflow
- `_repair_json()`: Automatic JSON repair for malformed LLM outputs
- `_step1_refine_fr()`: Define/refine functional requirements
- `_step2_select_dp()`: Select design parameters
- `_step3_assign_im()`: Assign implementation modules
- `_step4_gate_review()`: Validate FR↔DP↔IM mappings
- `_step5_decision()`: Decide stop/zigzag/revise

### 2. `baseline.py` - Single-Pass Baseline

**Purpose**: Single LLM call producing all artifacts without iterative validation.

**Key Functions**:
- `run_plain_single_agent()`: Execute baseline decomposition
- `run_plain_single_agent_and_save()`: Run and save to JSON

### 3. `evaluator.py` - Quality Assessment

**Purpose**: Independent LLM-based evaluation using stopping-method taxonomy.

**Key Functions**:
- `evaluate_two_outputs()`: Compare GATE-FD vs. baseline
- `evaluate_two_output_files_and_save()`: Load, evaluate, save

**Evaluation Dimensions**:
1. Pure FR (atomicity, solution-neutrality, testability)
2. FR↔DP Bridge (Independence Axiom, coupling, complexity)
3. DP↔IM Bridge (containment, diffusion risk)
4. Pure IM (structural modularity)
5. FR↔IM Bridge (verifiability, allocation boundaries)

### 4. `experiment_suite.py` - Batch Experiments

**Purpose**: Run multiple trials across requirements with resume capability.

**Key Classes**:
- `ExperimentSuiteConfig`: Experiment configuration
  - `cr_ids`: List of requirement IDs
  - `trials_per_cr`: Number of trials per requirement
  - `available_modules`: Candidate modules for IM assignment
  - `known_interfaces`: Available interfaces

**Key Functions**:
- `run_nghe_experiment_suite_to_csv()`: Run full experiment suite
  - Supports `skip_existing=True` for resuming interrupted runs
  - Generates timestamped JSON outputs
  - Produces consolidated CSV with statistics

### 5. `llm.py` - LLM Client

**Purpose**: OpenAI API client with retry logic and error handling.

**Key Classes**:
- `LLMClient`: Abstract base class
- `OpenAIResponsesClient`: OpenAI implementation with retry
- `MockLLMClient`: Testing mock

**Features**:
- Automatic retry with exponential backoff (3 attempts)
- Handles rate limits (429) and server errors (5xx)
- Structured output support with JSON schema hints
- Temperature and token limit configuration

### 6. `nghe.py` - Dataset Management

**Purpose**: Parse and manage NGHE customer requirements.

**Key Classes**:
- `CustomerRequirement`: Data structure for requirements
  - `id`: Unique identifier (e.g., CR-NGHE-001)
  - `statement`: Requirement statement
  - `acceptance_criteria`: List of criteria
  - `stakeholder_context`: Stakeholder information

**Key Functions**:
- `load_nghe_customer_requirements()`: Load from markdown file
- `parse_nghe_customer_requirements()`: Parse markdown format
- `find_cr()`: Find requirement by ID

## CLI Tools

### 1. `run_experiment_suite.py`

**Purpose**: Command-line interface for running experiments.

**Usage**:
```bash
python run_experiment_suite.py \
    --cr-ids CR-NGHE-001,CR-NGHE-002 \
    --trials 30 \
    --outdir ../output \
    --model-ours gpt-4o-mini \
    --model-baseline gpt-4o-mini \
    --model-eval gpt-4o-mini
```

**Arguments**:
- `--requirements-file`: Path to requirements markdown
- `--outdir`: Output directory for JSON files
- `--csv`: Output CSV path
- `--cr-ids`: Comma-separated requirement IDs
- `--trials`: Number of trials per requirement
- `--available-modules`: Comma-separated module names
- `--known-interfaces`: Comma-separated interface names
- `--model-ours`: LLM model for GATE-FD
- `--model-baseline`: LLM model for baseline
- `--model-eval`: LLM model for evaluator

### 2. `export_evaluations_to_csv.py`

**Purpose**: Aggregate JSON evaluation files into CSV summaries.

**Usage**:
```bash
python export_evaluations_to_csv.py \
    --input-dir ../output \
    --output-summary ../output/evaluation_summary.csv \
    --output-by-cr ../output/evaluation_summary_by_cr.csv
```

**Output Columns** (by CR):
- `cr_id`: Requirement identifier
- `n`: Number of trials
- `ours_win`, `baseline_win`, `tie`: Win/loss/tie counts
- `ours_avg_total`, `baseline_avg_total`: Mean total scores
- `avg_delta`: Mean score difference (GATE-FD - baseline)
- `ours_std_total`, `baseline_std_total`: Standard deviations
- `delta_std`: Standard deviation of deltas
- `n_non_ties`: Number of non-tie trials
- `sign_test_p_value`: Paired sign test p-value

## Data Flow

### Single Decomposition Flow

```
1. Load CustomerRequirement
   ↓
2. Create DecompositionInputs
   ↓
3. Run DecompositionWorkflow.run_one_level()
   ├─ Step 1: Refine FR
   ├─ Step 2: Select DP
   ├─ Step 3: Assign IM
   ├─ Step 4: Gate Review
   └─ Step 5: Decision
   ↓
4. Save DecompositionRun to JSON
```

### Experiment Flow

```
1. Configure ExperimentSuiteConfig
   ↓
2. For each CR × Trial:
   ├─ Run GATE-FD → JSON
   ├─ Run Baseline → JSON
   └─ Evaluate → JSON
   ↓
3. Aggregate evaluations → CSV
   ↓
4. Statistical analysis (win rate, p-values, effect sizes)
```

## Output File Naming Convention

### Decomposition Outputs
- **GATE-FD**: `ours_workflow_{CR_ID}_trial{N}_{TIMESTAMP}.json`
- **Baseline**: `baseline_single_pass_{CR_ID}_trial{N}_{TIMESTAMP}.json`

### Evaluation Outputs
- **Per-trial**: `evaluation_{CR_ID}_trial{N}_{TIMESTAMP}.json`
- **Summary**: `evaluation_summary.csv`
- **By requirement**: `evaluation_summary_by_cr.csv`

### Timestamp Format
- `YYYYMMDD_HHMMSS` (e.g., `20241223_143022`)

## Configuration Files

### `.env` (API Keys)
```
OPENAI_API_KEY=sk-your-api-key-here
```

### `requirements.txt` (Dependencies)
```
openai>=1.0.0
python-dotenv>=1.0.0
pydantic>=2.0.0
pandas>=2.0.0
numpy>=1.24.0
tqdm>=4.65.0
```

## Best Practices

### For Reproducibility
1. Use `temperature=0.0` for deterministic sampling
2. Record model name and version in outputs
3. Timestamp all outputs
4. Save complete LLM responses (not just parsed results)
5. Document API configuration (max_tokens, retry policy)

### For Scalability
1. Use `skip_existing=True` to resume interrupted experiments
2. Process requirements in batches (5-10 at a time)
3. Monitor API rate limits and costs
4. Archive completed experiments periodically

### For Maintainability
1. Keep prompts in separate functions for easy modification
2. Use dataclasses for structured data
3. Validate JSON outputs with schema hints
4. Log errors and retry attempts
5. Write unit tests for core functions

## Testing Strategy

### Unit Tests (Recommended)
- `test_workflow.py`: Test individual workflow steps
- `test_evaluator.py`: Test evaluation logic
- `test_nghe.py`: Test requirement parsing
- `test_llm.py`: Test LLM client with mocks

### Integration Tests
- End-to-end decomposition on sample requirements
- Experiment suite with small trial count (N=2)
- CSV export with synthetic data

### Validation Tests
- Compare against human expert evaluations
- Cross-validate with different LLM models
- Verify statistical calculations

## Future Extensions

### Planned Features
1. **Multi-level decomposition**: Recursive zigzagging to deeper levels
2. **Human-in-the-loop**: Interactive validation interface
3. **Alternative backends**: Support for Claude, Gemini, local models
4. **Visualization**: Web dashboard for results exploration
5. **MBSE integration**: Export to SysML, Cameo, Capella

### Research Directions
1. Domain generalization (aerospace, medical, financial)
2. Prompt optimization and ablation studies
3. Evaluator calibration with human experts
4. Scalability to large system architectures
5. Real-time decomposition assistance
