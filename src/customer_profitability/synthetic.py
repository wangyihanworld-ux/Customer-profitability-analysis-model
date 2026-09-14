"""Generate deterministic, fully synthetic customer profitability data."""
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd

KEY_COLUMNS = ["order_id", "customer", "product"]

@dataclass(frozen=True)
class SyntheticDataset:
    transactions: pd.DataFrame
    scenarios: pd.DataFrame

CUSTOMERS = (("客户甲", "战略型", 1.35, 0.16, 6.00), ("客户乙", "成长型", 1.10, 0.07, 1.05), ("客户丙", "稳定型", 0.95, 0.04, 0.90), ("客户丁", "成长型", 0.78, 0.03, 0.85), ("客户戊", "观察型", 0.62, 0.11, 1.65))
PRODUCTS = (("基础方案", 120.0, 66.0), ("专业方案", 220.0, 118.0), ("数据服务", 360.0, 150.0), ("定制服务", 520.0, 245.0))

def build_synthetic_dataset() -> SyntheticDataset:
    rows = []
    order_number = 1
    for month in range(1, 13):
        for customer_index, (customer, segment, scale, discount_rate, service_factor) in enumerate(CUSTOMERS):
            for product_index, (product, price, unit_cost) in enumerate(PRODUCTS):
                quantity = round((18 + month * 1.4 + product_index * 5) * scale)
                list_revenue = quantity * price
                discount = list_revenue * (discount_rate + 0.005 * ((month + product_index) % 3))
                return_rate = 0.025 if (month + customer_index + product_index) % 7 == 0 else 0.008
                returns = (list_revenue - discount) * return_rate
                product_cost = quantity * unit_cost * (1 + 0.006 * month)
                fulfillment_cost = 260 + quantity * (3.8 + product_index * 0.7)
                service_cost = (340 + 55 * product_index + 18 * month) * service_factor
                rows.append({"order_id": f"ORD-{order_number:04d}", "month": pd.Timestamp(2026, month, 1), "customer": customer, "segment": segment, "product": product, "quantity": float(quantity), "list_revenue": list_revenue, "discount": discount, "returns": returns, "product_cost": product_cost, "fulfillment_cost": fulfillment_cost, "service_cost": service_cost})
                order_number += 1
    scenarios = pd.DataFrame([["降价承压", -0.03, 0.00, 0.00, 0.00], ["基准", 0.00, 0.00, 0.00, 0.00], ["提价优化", 0.02, -0.02, -0.03, -0.05]], columns=["scenario", "price_change", "product_cost_change", "fulfillment_cost_change", "service_cost_change"])
    return SyntheticDataset(pd.DataFrame(rows), scenarios)
