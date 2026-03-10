#!/usr/bin/env python3
"""
Analyze cross-evaluation experiment results and calculate p-values.
"""
import csv
from collections import defaultdict
from pathlib import Path
from scipy import stats
import numpy as np


def load_results(csv_path):
    """Load results from CSV file."""
    results = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results


def analyze_by_cr(results):
    """Analyze results grouped by customer requirement."""
    cr_stats = defaultdict(lambda: {'ours_wins': 0, 'baseline_wins': 0, 'ties': 0, 'total': 0})
    
    for row in results:
        cr_id = row['cr_id']
        winner = row['winner']
        
        cr_stats[cr_id]['total'] += 1
        if winner == 'OURS':
            cr_stats[cr_id]['ours_wins'] += 1
        elif winner == 'BASELINE':
            cr_stats[cr_id]['baseline_wins'] += 1
        elif winner == 'TIE':
            cr_stats[cr_id]['ties'] += 1
    
    return cr_stats


def analyze_by_producer(results):
    """Analyze results grouped by producer model."""
    producer_stats = defaultdict(lambda: {'ours_wins': 0, 'baseline_wins': 0, 'ties': 0, 'total': 0})
    
    for row in results:
        producer = row['producer_model']
        winner = row['winner']
        
        producer_stats[producer]['total'] += 1
        if winner == 'OURS':
            producer_stats[producer]['ours_wins'] += 1
        elif winner == 'BASELINE':
            producer_stats[producer]['baseline_wins'] += 1
        elif winner == 'TIE':
            producer_stats[producer]['ties'] += 1
    
    return producer_stats


def analyze_overall(results):
    """Analyze overall results."""
    stats_dict = {'ours_wins': 0, 'baseline_wins': 0, 'ties': 0, 'total': 0}
    
    for row in results:
        winner = row['winner']
        stats_dict['total'] += 1
        if winner == 'OURS':
            stats_dict['ours_wins'] += 1
        elif winner == 'BASELINE':
            stats_dict['baseline_wins'] += 1
        elif winner == 'TIE':
            stats_dict['ties'] += 1
    
    return stats_dict


def calculate_binomial_test(ours_wins, baseline_wins, ties):
    """
    Calculate binomial test p-value.
    H0: GATE-FD and baseline are equally good (p=0.5)
    H1: GATE-FD is better than baseline (p>0.5)
    
    We exclude ties and test if ours_wins / (ours_wins + baseline_wins) > 0.5
    """
    total_decisive = ours_wins + baseline_wins
    if total_decisive == 0:
        return None, None
    
    # One-tailed binomial test (alternative='greater')
    result = stats.binomtest(ours_wins, total_decisive, 0.5, alternative='greater')
    p_value = result.pvalue
    win_rate = ours_wins / total_decisive
    
    return win_rate, p_value


def print_section(title):
    """Print section header."""
    print(f"\n{'='*80}")
    print(f"{title:^80}")
    print(f"{'='*80}\n")


def print_stats_table(stats_dict, label):
    """Print statistics table."""
    ours = stats_dict['ours_wins']
    baseline = stats_dict['baseline_wins']
    ties = stats_dict['ties']
    total = stats_dict['total']
    
    win_rate, p_value = calculate_binomial_test(ours, baseline, ties)
    
    print(f"{label:30} | Ours: {ours:4} | Baseline: {baseline:4} | Ties: {ties:4} | Total: {total:4}")
    if win_rate is not None:
        significance = ""
        if p_value < 0.001:
            significance = "***"
        elif p_value < 0.01:
            significance = "**"
        elif p_value < 0.05:
            significance = "*"
        
        print(f"{'':30} | Win Rate: {win_rate:.3f} | p-value: {p_value:.6f} {significance}")
    else:
        print(f"{'':30} | No decisive comparisons")
    print()


def main():
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == "--csv":
        csv_path = Path(sys.argv[2])
    else:
        csv_path = Path(__file__).parent.parent / "output" / "full_experiment" / "cross_eval_results.csv"
    
    print(f"Loading results from: {csv_path}")
    results = load_results(csv_path)
    print(f"Loaded {len(results)} evaluation results")
    
    # Overall analysis
    print_section("OVERALL RESULTS")
    overall_stats = analyze_overall(results)
    print_stats_table(overall_stats, "Overall")
    
    # By customer requirement
    print_section("RESULTS BY CUSTOMER REQUIREMENT")
    cr_stats = analyze_by_cr(results)
    for cr_id in sorted(cr_stats.keys()):
        print_stats_table(cr_stats[cr_id], cr_id)
    
    # By producer model
    print_section("RESULTS BY PRODUCER MODEL")
    producer_stats = analyze_by_producer(results)
    for producer in sorted(producer_stats.keys()):
        print_stats_table(producer_stats[producer], producer)
    
    # Summary
    print_section("SUMMARY")
    print("Significance levels:")
    print("  *** p < 0.001 (highly significant)")
    print("  **  p < 0.01  (very significant)")
    print("  *   p < 0.05  (significant)")
    print()
    print("Interpretation:")
    print("  - Win Rate > 0.5 indicates GATE-FD (ours) performs better than baseline")
    print("  - p-value < 0.05 indicates statistically significant difference")
    print("  - Lower p-value = stronger evidence that GATE-FD is better")
    print()
    
    # Check if overall result is significant
    ours = overall_stats['ours_wins']
    baseline = overall_stats['baseline_wins']
    ties = overall_stats['ties']
    win_rate, p_value = calculate_binomial_test(ours, baseline, ties)
    
    if p_value is not None and p_value < 0.05:
        print(f"[+] GATE-FD significantly outperforms baseline (p={p_value:.6f})")
    elif p_value is not None:
        print(f"[-] No significant difference found (p={p_value:.6f})")
    else:
        print("[-] Insufficient data for statistical test")


if __name__ == "__main__":
    main()
