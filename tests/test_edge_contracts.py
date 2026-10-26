import unittest
import pandas as pd
from openpyxl import Workbook
from customer_profitability.synthetic import build_synthetic_dataset
from customer_profitability.analysis import analyze_profitability
from customer_profitability.reporting import _summary
from customer_profitability.validation import DataValidationError
from customer_profitability.sensitivity import run_sensitivity

class EdgeContracts(unittest.TestCase):
    def setUp(self): self.x=build_synthetic_dataset().transactions.copy()
    def test_zero_revenue_ratios_are_undefined(self):
        for c in ['list_revenue','discount','returns']: self.x[c]=0.
        r=analyze_profitability(self.x)
        self.assertTrue(pd.isna(r.metrics['contribution_margin']))
        self.assertTrue(pd.isna(r.metrics['revenue_hhi']))
        self.assertTrue(r.customer_summary.revenue_share.isna().all())
    def test_infinity_is_rejected(self):
        self.x.loc[0,'service_cost']=float('inf')
        with self.assertRaises(DataValidationError): analyze_profitability(self.x)
    def test_conflicting_customer_segment_is_rejected(self):
        self.x.loc[0,'segment']='different'
        with self.assertRaisesRegex(DataValidationError,'客户类型'): analyze_profitability(self.x)
    def test_no_flagged_customer_summary_is_valid(self):
        r=analyze_profitability(self.x,low_margin_threshold=0)
        wb=Workbook(); _summary(wb.active,r)
        self.assertIn('无高收入低利润',wb.active['D6'].value)
    def test_zero_revenue_sensitivity_stays_undefined(self):
        for c in ['list_revenue','discount','returns']: self.x[c]=0.
        r=analyze_profitability(self.x)
        s=run_sensitivity(r,build_synthetic_dataset().scenarios)
        self.assertTrue(s.contribution_margin.isna().all())
    def test_infinite_sensitivity_rejected(self):
        d=build_synthetic_dataset(); s=d.scenarios.copy(); s.loc[0,'price_change']=float('inf')
        with self.assertRaises(ValueError): run_sensitivity(analyze_profitability(self.x),s)
