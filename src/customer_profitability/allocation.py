"""Separate hypothetical shared overhead; never reallocate direct costs."""
import math
from pathlib import Path
import pandas as pd
from .analysis import analyze_profitability
from .synthetic import build_synthetic_dataset


def compare_allocations(transactions, pool):
    if isinstance(pool, bool) or not math.isfinite(pool) or pool < 0:
        raise ValueError('Shared pool must be finite and nonnegative')
    result = analyze_profitability(transactions)
    customers = result.customer_summary.set_index('customer')
    drivers = {'net_revenue': customers.net_revenue,
               'order_count': result.detail.groupby('customer').order_id.nunique().reindex(customers.index)}
    outputs = []
    for name, weights in drivers.items():
        if (weights < 0).any() or weights.sum() <= 0:
            raise ValueError('Allocation requires nonnegative drivers and a positive total')
        part = customers[['net_revenue', 'contribution_profit', 'profit_rank']].copy()
        part['allocation_driver'] = name
        part['allocated_shared_cost'] = pool * weights / weights.sum()
        part['after_shared_cost_profit'] = part.contribution_profit-part.allocated_shared_cost
        part['after_shared_cost_rank'] = part.after_shared_cost_profit.rank(method='min', ascending=False)
        outputs.append(part.reset_index())
    return pd.concat(outputs, ignore_index=True)


def threshold_comparison(transactions):
    rows = []
    for low, high in ((.10, .20), (.15, .25), (.20, .30)):
        part = analyze_profitability(transactions, low_margin_threshold=low, high_value_threshold=high).customer_summary
        part = part[['customer', 'profit_rank', 'contribution_margin', 'profitability_flag']].copy()
        part['low_threshold'] = low; part['high_threshold'] = high
        rows.append(part)
    detail = pd.concat(rows, ignore_index=True)
    stability = detail.groupby('customer').agg(classifications=('profitability_flag', 'nunique'),
                                               distinct_profit_ranks=('profit_rank', 'nunique')).reset_index()
    return detail, stability


def main():
    data = build_synthetic_dataset().transactions
    out = Path('docs/allocation-evidence'); out.mkdir(parents=True, exist_ok=True)
    compare_allocations(data, 50000).to_csv(out/'shared_pool_comparison.csv', index=False)
    detail, stability = threshold_comparison(data)
    detail.to_csv(out/'threshold_comparison.csv', index=False)
    stability.to_csv(out/'classification_stability.csv', index=False)
    print(stability.to_string(index=False))


if __name__ == '__main__':
    main()
