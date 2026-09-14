"""Input contract for customer profitability analysis."""
from __future__ import annotations
import pandas as pd
from .synthetic import KEY_COLUMNS

VALUE_COLUMNS = ["quantity", "list_revenue", "discount", "returns", "product_cost", "fulfillment_cost", "service_cost"]
REQUIRED_COLUMNS = KEY_COLUMNS + ["month", "segment"] + VALUE_COLUMNS

class DataValidationError(ValueError):
    pass

def normalize_and_validate(frame: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise DataValidationError(f"交易表缺少字段：{', '.join(missing)}")
    if frame.empty:
        raise DataValidationError("交易表不能为空")
    result = frame.copy()
    for column in ["order_id", "customer", "segment", "product"]:
        invalid = result[column].isna() | result[column].astype("string").str.strip().eq("")
        if invalid.any():
            raise DataValidationError(f"字段 {column} 不能为空")
    result["month"] = pd.to_datetime(result["month"], errors="coerce")
    if result["month"].isna().any():
        raise DataValidationError("月份必须是有效日期")
    result["month"] = result["month"].dt.to_period("M").dt.to_timestamp()
    result[VALUE_COLUMNS] = result[VALUE_COLUMNS].apply(pd.to_numeric, errors="coerce")
    if (result[VALUE_COLUMNS].isna() | (result[VALUE_COLUMNS] < 0)).any().any():
        raise DataValidationError("数量和金额必须是非负数字")
    if result.duplicated(KEY_COLUMNS).any():
        raise DataValidationError("订单、客户和产品组合不能重复")
    if ((result["discount"] + result["returns"]) > result["list_revenue"]).any():
        raise DataValidationError("折扣与退货合计不能超过标价收入")
    return result
