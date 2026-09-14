"""Create sanitized Excel input and management-report workbooks."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from numbers import Real
import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
from .analysis import ProfitabilityResult, analyze_profitability
from .sensitivity import run_sensitivity
from .synthetic import SyntheticDataset, build_synthetic_dataset

REPORT_SHEETS = ["管理摘要", "客户盈利", "产品盈利", "月度趋势", "利润瀑布", "客户集中度", "敏感性", "数据质量"]
INPUT_SHEETS = ["演示说明", "交易明细", "情景假设"]
NAVY, BLUE, WHITE = "17365D", "4472C4", "FFFFFF"

@dataclass(frozen=True)
class DemoArtifacts:
    input_path: Path
    report_path: Path
    dataset: SyntheticDataset
    result: ProfitabilityResult
    sensitivity: pd.DataFrame

def generate_demo_artifacts(output_dir: str | Path = "demo_output") -> DemoArtifacts:
    directory = Path(output_dir); directory.mkdir(parents=True, exist_ok=True)
    dataset = build_synthetic_dataset(); result = analyze_profitability(dataset.transactions); sensitivity = run_sensitivity(result, dataset.scenarios)
    input_path = directory / "合成客户盈利输入.xlsx"; report_path = directory / "客户与产品盈利能力管理报告.xlsx"
    _write_input(input_path, dataset); _write_report(report_path, result, sensitivity)
    return DemoArtifacts(input_path, report_path, dataset, result, sensitivity)

def _write_input(path: Path, dataset: SyntheticDataset) -> None:
    wb = Workbook(); wb.remove(wb.active)
    ws = wb.create_sheet("演示说明"); ws.append(["说明"])
    for text in ["本文件全部为程序生成的合成数据，不对应任何真实公司、客户或交易。", "分析期间为2026年1月至12月，金额单位为人民币元。", "客户、产品、价格、折扣、退货及成本均为虚构。"]: ws.append([text])
    _write_frame(wb.create_sheet("交易明细"), dataset.transactions); _write_frame(wb.create_sheet("情景假设"), dataset.scenarios)
    _finish(wb); wb.save(path)

def _write_report(path: Path, result: ProfitabilityResult, sensitivity: pd.DataFrame) -> None:
    wb = Workbook(); wb.remove(wb.active); sheets = {name: wb.create_sheet(name) for name in REPORT_SHEETS}
    _summary(sheets["管理摘要"], result)
    labels={"customer":"客户","segment":"客户类型","product":"产品","month":"月份","quantity":"数量","list_revenue":"标价收入","discount":"折扣","returns":"退货","net_revenue":"净收入","product_cost":"产品成本","gross_profit":"毛利","fulfillment_cost":"履约成本","service_cost":"服务成本","contribution_profit":"贡献利润","gross_margin":"毛利率","contribution_margin":"贡献利润率","revenue_rank":"收入排名","profit_rank":"利润排名","revenue_share":"收入占比","cumulative_revenue_share":"累计收入占比","profitability_flag":"客户标签"}
    _write_frame(sheets["客户盈利"], result.customer_summary.rename(columns=labels), 5, "CustomerProfit")
    _write_frame(sheets["产品盈利"], result.product_summary.rename(columns=labels), 5, "ProductProfit")
    _write_frame(sheets["月度趋势"], result.monthly_summary.rename(columns=labels), 5, "MonthlyProfit")
    waterfall = pd.DataFrame([["标价收入", result.metrics["list_revenue"]], ["折扣及退货", result.metrics["net_revenue"]-result.metrics["list_revenue"]], ["产品成本", result.metrics["gross_profit"]-result.metrics["net_revenue"]], ["履约及服务成本", result.metrics["contribution_profit"]-result.metrics["gross_profit"]], ["贡献利润", result.metrics["contribution_profit"]]], columns=["项目", "金额"])
    _write_frame(sheets["利润瀑布"], waterfall, 5, "ProfitWaterfall")
    concentration = result.customer_summary[["customer", "net_revenue", "revenue_share", "cumulative_revenue_share", "contribution_profit", "profitability_flag"]].rename(columns=labels)
    _write_frame(sheets["客户集中度"], concentration, 5, "Concentration")
    _write_frame(sheets["敏感性"], sensitivity.rename(columns={"scenario":"情景","net_revenue":"净收入","contribution_profit":"贡献利润","contribution_margin":"贡献利润率","change_vs_base":"较基准变化"}), 5, "Sensitivity")
    checks = pd.DataFrame([["交易行数", len(result.detail), 240, "通过" if len(result.detail)==240 else "异常"], ["客户汇总勾稽", result.customer_summary["contribution_profit"].sum()-result.metrics["contribution_profit"], 0, "通过"], ["产品汇总勾稽", result.product_summary["contribution_profit"].sum()-result.metrics["contribution_profit"], 0, "通过"], ["收入HHI范围", result.metrics["revenue_hhi"], "0至1", "通过" if 0 <= result.metrics["revenue_hhi"] <= 1 else "异常"]], columns=["检查项", "结果", "预期", "状态"])
    _write_frame(sheets["数据质量"], checks, 5, "QualityChecks")
    for name in REPORT_SHEETS[1:]: _title(sheets[name], name, "全部结果均基于完全合成数据")
    _add_charts(sheets); _finish(wb); wb.save(path)

def _summary(ws, result: ProfitabilityResult) -> None:
    _title(ws, "客户与产品盈利能力管理摘要", "2026年度｜全部数据均为合成演示数据")
    m=result.metrics; rows=[["净收入",m["net_revenue"]],["毛利",m["gross_profit"]],["贡献利润",m["contribution_profit"]],["贡献利润率",m["contribution_margin"]],["最大客户收入占比",m["top_customer_revenue_share"]],["收入HHI",m["revenue_hhi"]],["高收入低利润客户数",int((result.customer_summary["profitability_flag"]=="高收入低利润").sum())]]
    ws.append([]); ws.append(["指标","结果"])
    for row in rows: ws.append(row)
    for row in range(6,9): ws.cell(row,2).number_format='¥#,##0;[Red](¥#,##0);-'
    for row in (9,10): ws.cell(row,2).number_format='0.0%'
    ws.cell(11,2).number_format='0.0000'
    ws["D5"]="管理判断"; ws["D5"].fill=PatternFill("solid",fgColor=NAVY); ws["D5"].font=Font(color=WHITE,bold=True)
    flagged=result.customer_summary.query("profitability_flag == '高收入低利润'").iloc[0]
    notes=[f"{flagged['customer']}收入排名靠前，但贡献利润率仅为{flagged['contribution_margin']:.1%}。","客户价值判断应同时考虑折扣、退货、履约与服务成本。","敏感性结果是条件模拟，不是因果推断或业绩承诺。"]
    for i,note in enumerate(notes,6): ws.cell(i,4,note)

def _write_frame(ws, frame: pd.DataFrame, start_row: int=1, table_name: str|None=None) -> None:
    export=frame.copy()
    export.columns=[str(c) for c in export.columns]
    for c,h in enumerate(export.columns,1): ws.cell(start_row,c,h)
    for r,row in enumerate(export.itertuples(index=False,name=None),start_row+1):
        for c,value in enumerate(row,1):
            if isinstance(value,pd.Timestamp): value=value.to_pydatetime()
            elif isinstance(value,Real) and not isinstance(value,bool): value=round(float(value),4)
            ws.cell(r,c,value)
            header=str(export.columns[c-1])
            if "率" in header or "占比" in header: ws.cell(r,c).number_format="0.0%"
            elif any(word in header for word in ("收入","成本","利润","折扣","退货","金额","变化")): ws.cell(r,c).number_format='¥#,##0;[Red](¥#,##0);-'
            elif "数量" in header: ws.cell(r,c).number_format="#,#00"
    if len(export) and table_name:
        ref=f"A{start_row}:{get_column_letter(len(export.columns))}{start_row+len(export)}"; table=Table(displayName=table_name,ref=ref); table.tableStyleInfo=TableStyleInfo(name="TableStyleMedium2",showRowStripes=True); ws.add_table(table)
    for cell in ws[start_row]:
        if cell.column<=len(export.columns): cell.fill=PatternFill("solid",fgColor=BLUE); cell.font=Font(color=WHITE,bold=True)
    ws.freeze_panes=f"A{start_row+1}"

def _title(ws,title,subtitle): ws["A2"]=title; ws["A2"].font=Font(name="Microsoft YaHei",size=15,bold=True,color=NAVY); ws["A3"]=subtitle

def _add_charts(sheets):
    ws=sheets["客户盈利"]; chart=BarChart(); chart.title="客户贡献利润"; chart.add_data(Reference(ws,min_col=10,min_row=5,max_row=10),titles_from_data=True); chart.set_categories(Reference(ws,min_col=1,min_row=6,max_row=10)); chart.legend=None; ws.add_chart(chart,"Q5")
    ws=sheets["月度趋势"]; chart=LineChart(); chart.title="月度净收入与贡献利润"; chart.add_data(Reference(ws,min_col=6,min_row=5,max_row=17),titles_from_data=True); chart.add_data(Reference(ws,min_col=10,min_row=5,max_row=17),titles_from_data=True); chart.set_categories(Reference(ws,min_col=1,min_row=6,max_row=17)); ws.add_chart(chart,"N5")
    ws=sheets["敏感性"]; chart=BarChart(); chart.title="情景贡献利润"; chart.add_data(Reference(ws,min_col=3,min_row=5,max_row=8),titles_from_data=True); chart.set_categories(Reference(ws,min_col=1,min_row=6,max_row=8)); chart.legend=None; ws.add_chart(chart,"G5")

def _finish(wb):
    for ws in wb.worksheets:
        ws.sheet_view.showGridLines=False
        for cells in ws.columns:
            letter=get_column_letter(cells[0].column); width=max(len(str(c.value or "")) for c in cells)+3; ws.column_dimensions[letter].width=min(max(width,12),28)
        for row in ws.iter_rows():
            for cell in row:
                if cell.value is not None: cell.font=Font(name="Microsoft YaHei",size=cell.font.sz or 10,bold=cell.font.bold,color=cell.font.color); cell.alignment=Alignment(vertical="center")
