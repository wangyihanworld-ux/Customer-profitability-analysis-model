# Customer and Product Profitability

[中文](README.md) · English

Identify customers that generate revenue but contribute relatively little profit after fulfilment and service costs.

## Analytical approach and deliverables

- Reconcile list-price revenue, discounts, returns, net revenue, product cost and customer contribution.
- Compare customer and product rankings, Top-N concentration, HHI and configurable customer tiers.
- Evaluate price and cost sensitivities and export an Excel management report.

In the synthetic example, the largest customer by revenue has an 11.24% contribution margin versus 29.50% overall. This is a diagnostic prompt, not a recommendation to exit that customer.

## Reproduce

Run from the repository root with Python 3.12:

```powershell
python -m pip install -e .
python -m customer_profitability.demo
python -m unittest discover -s tests -v
```

## Interpretation and limitations

Price sensitivities hold sales volume fixed and do not estimate elasticity or churn. Customer contribution excludes unallocated corporate costs. Synthetic margins and classification thresholds are not universal benchmarks.

Business examples use synthetic data and contain no private company or customer records. Only the separately labelled World Bank case in the macro repository uses public economic observations. Refer to current source and CI for this update; older release tags and screenshots describe earlier snapshots.
