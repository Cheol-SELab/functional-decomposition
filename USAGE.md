# GATE-FD Usage Guide

This guide provides detailed instructions for using the Gate-Checked Functional Decomposition (GATE-FD) workflow.

## Table of Contents

1. [Basic Setup](#basic-setup)
2. [Running Single Decompositions](#running-single-decompositions)
3. [Running Experiments](#running-experiments)
4. [Analyzing Results](#analyzing-results)
5. [Advanced Usage](#advanced-usage)
6. [Troubleshooting](#troubleshooting)

## Basic Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure OpenAI API Key

```bash
cd src
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-api-key-here
```

### 3. Verify Installation

```python
from lfd import *
load_default_env()
print("Setup complete!")
```

## Running Single Decompositions

### Example 1: Basic GATE-FD Workflow

```python
from lfd import *

# Load environment
load_default_env()

# Load NGHE requirements
crs = load_nghe_customer_requirements('../example/NGHE_customer_requirements.md')

# Run GATE-FD on first requirement
run_nghe_cr_and_save(
    cr=crs[0],
    outdir='../output',
    model_name='gpt-4o-mini',
    temperature=0.0,
    max_output_tokens=2048
)
```

**Output**: JSON file in `output/` directory with complete decomposition trace.

### Example 2: Run Baseline Comparison

```python
from lfd import *

load_default_env()
crs = load_nghe_customer_requirements('../example/NGHE_customer_requirements.md')

# Compare GATE-FD vs. Baseline
compare_nghe_cr_and_save(
    cr=crs[0],
    outdir='../output',
    run_id='trial1',
    workflow_variant='ours_workflow',
    baseline_variant='baseline_single_pass',
    model_name='gpt-4o-mini'
)
```

**Output**: Two JSON files (GATE-FD and baseline) plus evaluation JSON.

### Example 3: Custom Requirement

```python
from lfd import *

# Define custom requirement
custom_cr = CustomerRequirement(
    id='CR-CUSTOM-001',
    statement='The system shall track equipment location in real-time',
    acceptance_criteria=[
        'Location accuracy within 5 meters',
        'Update frequency of 1 Hz minimum'
    ],
    stakeholder_context='Fleet management needs real-time visibility'
)

# Run decomposition
run_nghe_cr_and_save(
    cr=custom_cr,
    outdir='../output',
    model_name='gpt-4o-mini'
)
```

## Running Experiments

### Example 4: Small-Scale Experiment (2 requirements, 5 trials)

```bash
cd src
python run_experiment_suite.py \
    --cr-ids CR-NGHE-001 CR-NGHE-002 \
    --trials 5 \
    --outdir ../output \
    --model gpt-4o-mini
```

**Output**: 20 JSON files (2 CRs × 5 trials × 2 methods)

### Example 5: Full Experiment Suite (10 requirements, 30 trials)

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

**Runtime**: ~2-3 hours (depends on API latency)

### Example 6: Resume Interrupted Experiments

The experiment suite automatically skips completed trials:

```bash
# If interrupted, simply re-run the same command
python run_experiment_suite.py \
    --cr-ids CR-NGHE-001 CR-NGHE-002 \
    --trials 30 \
    --outdir ../output \
    --model gpt-4o-mini
```

Existing evaluation files are detected and skipped.

## Analyzing Results

### Example 7: Export to CSV

```bash
cd src
python export_evaluations_to_csv.py \
    --input-dir ../output \
    --output-summary ../output/evaluation_summary.csv \
    --output-by-cr ../output/evaluation_summary_by_cr.csv
```

**Output Files**:
- `evaluation_summary.csv`: Per-trial results
- `evaluation_summary_by_cr.csv`: Aggregated statistics by requirement

### Example 8: Programmatic Analysis

```python
import pandas as pd

# Load aggregated results
df = pd.read_csv('../output/evaluation_summary_by_cr.csv')

# Filter significant results (p < 0.05)
significant = df[df['sign_test_p_value'] < 0.05]
print(f"Significant improvements: {len(significant)}/{len(df)}")

# Calculate overall win rate
total_wins = df['ours_win'].sum()
total_trials = df['n'].sum()
win_rate = total_wins / total_trials * 100
print(f"Overall win rate: {win_rate:.1f}%")

# Show effect sizes
print("\nEffect sizes:")
print(df[['cr_id', 'avg_delta', 'sign_test_p_value']].to_string())
```

### Example 9: Inspect Individual Trial

```python
import json

# Load a specific trial result
with open('../output/ours_workflow_CR-NGHE-001_trial1_20241223_120000.json', 'r') as f:
    result = json.load(f)

# Examine decomposition steps
print("Refined FR:", result['step1_refine_fr']['refined_fr'])
print("Selected DP:", result['step2_select_dp']['selected_dp'])
print("Assigned IM:", result['step3_assign_im']['assigned_im'])
print("Gate Results:", result['step4_gate_review'])
print("Decision:", result['step5_decision']['decision'])
```

## Advanced Usage

### Example 10: Custom Evaluation Criteria

```python
from lfd import evaluate_two_outputs

# Load two decomposition outputs
with open('../output/ours_workflow_CR-NGHE-001_trial1.json') as f:
    ours_output = json.load(f)
    
with open('../output/baseline_single_pass_CR-NGHE-001_trial1.json') as f:
    baseline_output = json.load(f)

# Run evaluation
evaluation = evaluate_two_outputs(
    cr=crs[0],
    ours_output=ours_output,
    baseline_output=baseline_output,
    model_name='gpt-4o-mini'
)

# Access per-category scores
print("Pure FR scores:", evaluation['pure_fr'])
print("FR↔DP Bridge scores:", evaluation['fr_dp_bridge'])
```

### Example 11: Batch Processing Custom Requirements

```python
from lfd import *
import json

# Load custom requirements from JSON
with open('my_requirements.json', 'r') as f:
    custom_reqs = json.load(f)

# Convert to CustomerRequirement objects
crs = [
    CustomerRequirement(
        id=req['id'],
        statement=req['statement'],
        acceptance_criteria=req['criteria'],
        stakeholder_context=req['context']
    )
    for req in custom_reqs
]

# Run decomposition on all
for cr in crs:
    run_nghe_cr_and_save(
        cr=cr,
        outdir='../output',
        model_name='gpt-4o-mini'
    )
    print(f"Completed: {cr.id}")
```

### Example 12: Using Different LLM Models

```python
# Compare different models
models = ['gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo']

for model in models:
    run_nghe_cr_and_save(
        cr=crs[0],
        outdir=f'../output/{model}',
        model_name=model,
        temperature=0.0
    )
```

## Troubleshooting

### Issue 1: API Rate Limits

**Symptom**: `RateLimitError` from OpenAI API

**Solution**: The LLM client includes automatic retry with exponential backoff. For persistent issues:
- Reduce `--trials` count
- Add delays between trials
- Upgrade OpenAI API tier

### Issue 2: Missing Dependencies

**Symptom**: `ModuleNotFoundError`

**Solution**:
```bash
pip install -r requirements.txt
```

### Issue 3: Invalid API Key

**Symptom**: `AuthenticationError`

**Solution**:
1. Verify `.env` file exists in `src/` directory
2. Check API key format: `OPENAI_API_KEY=sk-...`
3. Ensure no extra spaces or quotes

### Issue 4: JSON Parsing Errors

**Symptom**: `JSONDecodeError` in LLM responses

**Solution**: The workflow includes automatic repair mechanisms. If persistent:
- Check LLM model supports structured outputs
- Verify `max_output_tokens` is sufficient (≥2048)
- Review prompt templates for schema hints

### Issue 5: Out of Memory

**Symptom**: `MemoryError` during CSV export

**Solution**:
```python
# Process in batches
import glob
import pandas as pd

eval_files = glob.glob('../output/evaluation_*.json')
batch_size = 100

for i in range(0, len(eval_files), batch_size):
    batch = eval_files[i:i+batch_size]
    # Process batch...
```

## Performance Tips

1. **Parallel Execution**: Run multiple experiments in parallel (different terminals/machines)
2. **Resume Capability**: Use `skip_existing=True` to resume interrupted runs
3. **Batch Size**: Process 5-10 requirements at a time for manageable runtime
4. **Model Selection**: `gpt-4o-mini` offers best cost/performance balance
5. **Output Management**: Periodically archive completed experiments to separate directories

