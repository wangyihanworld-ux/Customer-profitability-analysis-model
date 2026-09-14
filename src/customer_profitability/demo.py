"""Run the fully sanitized customer profitability demo."""
import argparse
from .reporting import generate_demo_artifacts

def main():
    parser=argparse.ArgumentParser(description="生成完全脱敏的客户盈利能力演示"); parser.add_argument("--output-dir",default="demo_output"); args=parser.parse_args()
    a=generate_demo_artifacts(args.output_dir); m=a.result.metrics
    print("客户与产品盈利能力演示（全部数据均为合成数据）")
    print(f"交易记录：{len(a.dataset.transactions)}"); print(f"净收入：{m['net_revenue']:,.2f}"); print(f"贡献利润：{m['contribution_profit']:,.2f}"); print(f"贡献利润率：{m['contribution_margin']:.2%}"); print(f"收入HHI：{m['revenue_hhi']:.4f}")
    print(a.result.customer_summary[["customer","net_revenue","contribution_profit","contribution_margin","profitability_flag"]].to_string(index=False))
    print(f"合成输入：{a.input_path.resolve()}"); print(f"管理报告：{a.report_path.resolve()}")

if __name__ == "__main__": main()
