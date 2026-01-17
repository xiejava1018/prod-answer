"""
Import product data from Excel file with multiple sheets
Each sheet represents a product
"""
import os
import django
import sys

# Set UTF-8 encoding for output
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.supabase')
django.setup()

from apps.products.models import Product, Feature
import pandas as pd


def clear_all_existing_data():
    """清除所有现有产品数据"""
    print("[INFO] 正在清除现有产品数据...")
    Feature.objects.all().delete()
    Product.objects.all().delete()
    print("[OK] 已清除所有产品数据\n")


def import_product_from_sheet(excel_file_path, sheet_name):
    """
    从单个 sheet 导入产品数据

    Sheet structure:
    - 序号 (Sequence Number)
    - 指标项 (Indicator Category)
    - 一级功能 (Level 1 Function)
    - 二级功能 (Level 2 Function)
    - 技术要求 (Technical Requirements)
    """

    # Read sheet
    df = pd.read_excel(excel_file_path, sheet_name=sheet_name)

    # Skip empty sheets
    if len(df) == 0:
        print(f"[SKIP] Sheet '{sheet_name}' 为空，跳过")
        return None, 0

    print(f"\n{'='*60}")
    print(f"正在处理: {sheet_name}")
    print(f"{'='*60}")
    print(f"数据行数: {len(df)}")

    # Create product
    product_name = sheet_name
    product_description = f"{sheet_name}产品功能清单"

    # Determine product category based on name
    if '资产' in sheet_name:
        category = 'asset_management'
    elif '漏洞' in sheet_name:
        category = 'vulnerability_scanner'
    elif '日志' in sheet_name or '审计' in sheet_name:
        category = 'log_audit'
    elif '威胁' in sheet_name:
        category = 'threat_detection'
    else:
        category = 'security'

    product = Product.objects.create(
        name=product_name,
        description=product_description,
        category=category,
        subsystem_type=category,
        version='V3.0'
    )

    print(f"[OK] 创建产品: {product_name}")

    # Initialize variables for hierarchical structure
    current_indicator = None
    current_level1 = None
    current_level2 = None

    success_count = 0
    error_count = 0

    # Iterate through rows
    for idx, row in df.iterrows():
        try:
            sequence = row.get('序号', idx + 1)
            indicator = row.get('指标项') if pd.notna(row.get('指标项')) else None
            level1 = row.get('一级功能') if pd.notna(row.get('一级功能')) else None
            level2 = row.get('二级功能') if pd.notna(row.get('二级功能')) else None
            technical_req = row.get('技术要求', '')

            # Skip rows without any meaningful data
            if pd.isna(sequence) and not indicator and not level1 and not level2 and not technical_req:
                continue

            # Update current hierarchy levels
            if indicator:
                current_indicator = indicator
            if level1:
                current_level1 = level1
            if level2:
                current_level2 = level2

            # Build feature name with hierarchy
            feature_parts = []
            if current_indicator:
                feature_parts.append(current_indicator)
            if current_level1:
                feature_parts.append(current_level1)
            if current_level2:
                feature_parts.append(current_level2)

            feature_name = ' > '.join(feature_parts) if feature_parts else f'功能 {sequence}'

            # If still no technical requirement, skip this row
            if not technical_req or pd.isna(technical_req):
                continue

            # Create feature
            feature = Feature.objects.create(
                product=product,
                feature_name=feature_name,
                description=technical_req,
                category=current_indicator or '产品功能',
                subcategory=current_level2 or '',
                level1_function=current_level1 or '',
                level2_function=current_level2 or '',
                indicator_type=current_indicator or '产品功能',
                is_active=True
            )

            success_count += 1

            if success_count <= 3 or success_count % 10 == 0:
                print(f"  [{success_count}] {feature_name[:60]}...")

        except Exception as e:
            error_count += 1
            print(f"  [ERROR] 导入失败 (行 {idx}): {e}")

    # Print summary for this product
    print(f"\n产品 '{sheet_name}' 导入完成:")
    print(f"  成功: {success_count} 个特征")
    print(f"  失败: {error_count} 个")

    return product, success_count


def import_all_products(excel_file_path):
    """导入 Excel 文件中的所有产品"""

    # Get all sheet names
    xl = pd.ExcelFile(excel_file_path)
    sheet_names = xl.sheet_names

    print(f"发现 {len(sheet_names)} 个产品")
    print(f"产品列表: {', '.join(sheet_names)}\n")

    # Clear existing data
    clear_all_existing_data()

    # Import each product
    total_products = 0
    total_features = 0

    for sheet_name in sheet_names:
        try:
            product, feature_count = import_product_from_sheet(excel_file_path, sheet_name)
            if product:
                total_products += 1
                total_features += feature_count
        except Exception as e:
            print(f"[ERROR] 导入产品 '{sheet_name}' 失败: {e}")
            import traceback
            traceback.print_exc()

    # Print final summary
    print("\n" + "="*60)
    print("全部导入完成!")
    print("="*60)
    print(f"导入产品总数: {total_products}")
    print(f"导入特征总数: {total_features}")
    print(f"\n数据库统计:")
    print(f"  Product 表: {Product.objects.count()} 条记录")
    print(f"  Feature 表: {Feature.objects.count()} 条记录")
    print("="*60)


if __name__ == '__main__':
    excel_file = '../docs/产品集技术参数V3.xlsx'

    print("="*60)
    print("产品功能数据批量导入工具")
    print("="*60)
    print(f"Excel文件: {excel_file}")
    print()

    import_all_products(excel_file)

    print("\n下一步:")
    print("1. 访问 Django Admin: http://127.0.0.1:8000/admin/")
    print("2. 查看 Products 和 Features")
    print("3. 配置 Embedding Model")
    print("4. 生成向量嵌入")
