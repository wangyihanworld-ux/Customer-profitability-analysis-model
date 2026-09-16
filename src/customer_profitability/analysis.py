"""Contribution-profit, portfolio and concentration analysis."""
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from .validation import normalize_and_validate

@dataclass(frozen=True)
class ProfitabilityResult:
    detail: pd.DataFrame
    customer_summary: pd.DataFrame
    product_summary: pd.DataFrame
    monthly_summary: pd.DataFrame
    metrics: dict[str, float]

def analyze_profitability(
    transactions: pd.DataFrame,
    *,
    low_margin_threshold: float = 0.15,
    high_value_threshold: float = 0.25,
    top_revenue_count: int = 2,
) -> ProfitabilityResult:
    if not 0 <= low_margin_threshold <= 1 or not 0 <= high_value_threshold <= 1:
        raise ValueError("利润率阈值必须在 0 到 1 之间")
    if top_revenue_count < 1:
        raise ValueError("高收入客户数量必须至少为 1")
    detail = normalize_and_validate(transactions)
    detail["net_revenue"] = detail["list_revenue"] - detail["discount"] - detail["returns"]
    detail["gross_profit"] = detail["net_revenue"] - detail["product_cost"]
    detail["contribution_profit"] = detail["gross_profit"] - detail["fulfillment_cost"] - detail["service_cost"]
    detail["contribution_margin"] = _ratio(detail["contribution_profit"], detail["net_revenue"])
    customer = _summarize(detail, ["customer", "segment"]).sort_values("net_revenue", ascending=False).reset_index(drop=True)
    customer["revenue_rank"] = range(1, len(customer) + 1)
    customer["profit_rank"] = customer["contribution_profit"].rank(method="min", ascending=False).astype(int)
    customer["revenue_share"] = customer["net_revenue"] / customer["net_revenue"].sum()
    customer["cumulative_revenue_share"] = customer["revenue_share"].cumsum()
    customer["profitability_flag"] = customer.apply(
        _flag,
        axis=1,
        low_margin_threshold=low_margin_threshold,
        high_value_threshold=high_value_threshold,
        top_revenue_count=top_revenue_count,
    )
    product = _summarize(detail, ["product"]).sort_values("contribution_profit", ascending=False).reset_index(drop=True)
    monthly = _summarize(detail, ["month"])
    profit_total = float(customer["contribution_profit"].sum())
    metrics = {"list_revenue": float(detail["list_revenue"].sum()), "net_revenue": float(detail["net_revenue"].sum()), "gross_profit": float(detail["gross_profit"].sum()), "contribution_profit": profit_total, "contribution_margin": profit_total / float(detail["net_revenue"].sum()), "top_customer_revenue_share": float(customer.iloc[0]["revenue_share"]), "revenue_hhi": float((customer["revenue_share"] ** 2).sum()), "negative_customer_count": int((customer["contribution_profit"] < 0).sum())}
    return ProfitabilityResult(detail, customer, product, monthly, metrics)

def _summarize(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    columns = ["quantity", "list_revenue", "discount", "returns", "net_revenue", "product_cost", "gross_profit", "fulfillment_cost", "service_cost", "contribution_profit"]
    result = frame.groupby(keys, observed=True, as_index=False)[columns].sum()
    result["gross_margin"] = _ratio(result["gross_profit"], result["net_revenue"])
    result["contribution_margin"] = _ratio(result["contribution_profit"], result["net_revenue"])
    return result

def _ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator.div(denominator.where(denominator.ne(0))).fillna(0.0)

def _flag(
    row: pd.Series,
    *,
    low_margin_threshold: float,
    high_value_threshold: float,
    top_revenue_count: int,
) -> str:
    if row["contribution_profit"] < 0:
        return "负贡献"
    if row["revenue_rank"] <= top_revenue_count and row["contribution_margin"] < low_margin_threshold:
        return "高收入低利润"
    if row["contribution_margin"] >= high_value_threshold:
        return "高价值"
    return "正常"
