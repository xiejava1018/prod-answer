import pandas as pd
import json
import sys

def extract_excel_to_dict(filepath, output_file):
    """提取Excel所有工作表到字典并保存为JSON"""
    try:
        # 读取所有工作表
        excel_data = pd.read_excel(filepath, sheet_name=None)

        # 转换为可序列化的格式
        output_dict = {}
        for sheet_name, df in excel_data.items():
            # 将DataFrame转换为列表字典，处理NaN值
            output_dict[sheet_name] = df.where(pd.notna(df), None).to_dict('records')

        # 保存为JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_dict, f, ensure_ascii=False, indent=2)

        print(f"✅ 成功提取: {filepath}")
        print(f"   工作表数量: {len(excel_data)}")
        print(f"   工作表列表: {list(excel_data.keys())}")
        for sheet_name, df in excel_data.items():
            print(f"   - {sheet_name}: {len(df)} 行")
        print(f"   输出文件: {output_file}")
        return True
    except Exception as e:
        print(f"❌ 读取失败: {filepath}")
        print(f"   错误: {e}")
        import traceback
        traceback.print_exc()
        return False

# 提取两个文档
print("="*80)
print("提取Excel文档内容")
print("="*80)

success1 = extract_excel_to_dict(
    '/Users/xiejava/AIproject/prod-answer/docs/产品集技术参数V3.xlsx',
    '/Users/xiejava/AIproject/prod-answer/docs/产品集技术参数V3.json'
)

print()

success2 = extract_excel_to_dict(
    '/Users/xiejava/AIproject/prod-answer/docs/软件需求规格书RFP -v1.6.xlsx',
    '/Users/xiejava/AIproject/prod-answer/docs/软件需求规格书RFP_v1.6.json'
)

if success1 and success2:
    print("\n✅ 所有文档提取完成")
else:
    print("\n❌ 部分文档提取失败")
    sys.exit(1)
