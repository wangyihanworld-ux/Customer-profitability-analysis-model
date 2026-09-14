"""Scenario sensitivity for contribution profit."""
from __future__ import annotations
import pandas as pd
from .analysis import ProfitabilityResult

SCENARIO_COLUMNS = ["scenario", "price_change", "product_cost_change", "fulfillment_cost_change", "service_cost_change"]

def run_sensitivity(result: ProfitabilityResult, scenarios: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in SCENARIO_COLUMNS if column not in scenarios.columns]
    if missing:
        raise ValueError(f"情景表缺少字段：{', '.join(missing)}")
    if scenarios.empty or scenarios["scenario"].isna().any() or scenarios["scenario"].duplicated().any():
        raise ValueError("情景名称不能为空或重复")
    frame = scenarios.copy()
    factors = frame[SCENARIO_COLUMNS[1:]].apply(pd.to_numeric, errors="coerce")
    if factors.isna().any().any() or (factors <= -1).any().any():
        raise ValueError("情景变化率必须是大于 -100% 的数字")
    frame[SCENARIO_COLUMNS[1:]] = factors
    rows = []
    detail = result.detail
    for scenario in frame.itertuples(index=False):
        net_revenue = detail["net_revenue"] * (1 + scenario.price_change)
        product_cost = detail["product_cost"] * (1 + scenario.product_cost_change)
        fulfillment = detail["fulfillment_cost"] * (1 + scenario.fulfillment_cost_change)
        service = detail["service_cost"] * (1 + scenario.service_cost_change)
        contribution = float((net_revenue - product_cost - fulfillment - service).sum())
        rows.append({"scenario": scenario.scenario, "net_revenue": float(net_revenue.sum()), "contribution_profit": contribution, "contribution_margin": contribution / float(net_revenue.sum()), "change_vs_base": contribution - result.metrics["contribution_profit"]})
    return pd.DataFrame(rows)
