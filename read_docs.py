import pandas as pd
import sys

# 读取产品集技术参数
print("="*80)
print("产品集技术参数V3.xlsx")
print("="*80)
try:
    df1 = pd.read_excel('docs/产品集技术参数V3.xlsx', sheet_name=None)
    print(f"工作表列表: {list(df1.keys())}\n")
    for sheet_name, data in df1.items():
        print(f"\n{'='*60}")
        print(f"工作表: {sheet_name}")
        print(f"{'='*60}")
        print(data.to_string(index=False, max_rows=100))
        print(f"\n总行数: {len(data)}, 总列数: {len(data.columns)}")
except Exception as e:
    print(f"读取错误: {e}")
    import traceback
    traceback.print_exc()

print("\n\n")
print("="*80)
print("软件需求规格书RFP -v1.6.xlsx")
print("="*80)
try:
    df2 = pd.read_excel('docs/软件需求规格书RFP -v1.6.xlsx', sheet_name=None)
    print(f"工作表列表: {list(df2.keys())}\n")
    for sheet_name, data in df2.items():
        print(f"\n{'='*60}")
        print(f"工作表: {sheet_name}")
        print(f"{'='*60}")
        print(data.to_string(index=False, max_rows=100))
        print(f"\n总行数: {len(data)}, 总列数: {len(data.columns)}")
except Exception as e:
    print(f"读取错误: {e}")
    import traceback
    traceback.print_exc()
