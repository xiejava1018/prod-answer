"""
Test script for importing subsystem products from JSON.
"""
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.products.import_service import ProductImportService


def test_import_subsystems():
    """Test importing subsystem products from JSON file."""
    print("="*80)
    print("测试导入子系统产品")
    print("="*80)

    # JSON文件路径
    json_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'docs',
        '产品集技术参数V3.json'
    )

    print(f"\nJSON文件路径: {json_file}")
    print(f"文件存在: {os.path.exists(json_file)}")

    if not os.path.exists(json_file):
        print(f"❌ 错误: JSON文件不存在: {json_file}")
        return False

    # 执行导入
    print("\n开始导入...")
    results = ProductImportService.import_from_json(
        json_file,
        vendor="安全产品厂商"
    )

    print(f"\n导入结果:")
    print(f"  成功: {results['success']}")
    print(f"  创建产品数: {results['products_created']}")
    print(f"  创建功能数: {results['features_created']}")

    if results['errors']:
        print(f"  错误: {results['errors']}")

    if results['success']:
        print("\n✅ 导入成功!")
    else:
        print("\n❌ 导入失败!")

    return results['success']


def test_clear_subsystems():
    """Test clearing all subsystem products."""
    print("\n" + "="*80)
    print("测试清除子系统产品")
    print("="*80)

    results = ProductImportService.clear_subsystem_products()

    print(f"\n清除结果:")
    print(f"  成功: {results['success']}")
    print(f"  删除产品数: {results['products_deleted']}")
    print(f"  删除功能数: {results['features_deleted']}")

    if results['errors']:
        print(f"  错误: {results['errors']}")

    if results['success']:
        print("\n✅ 清除成功!")
    else:
        print("\n❌ 清除失败!")

    return results['success']


def show_subsystem_products():
    """Show all subsystem products."""
    print("\n" + "="*80)
    print("当前子系统产品列表")
    print("="*80)

    from apps.products.models import Product, Feature

    subsystem_types = [
        'asset_mapping',
        'exposure_mapping',
        'big_data',
        'soar'
    ]

    total_products = 0
    total_features = 0

    for subsystem_type in subsystem_types:
        products = Product.objects.filter(
            subsystem_type=subsystem_type,
            is_active=True
        )

        if products.exists():
            print(f"\n{dict(Product.SUBSYSTEM_TYPE_CHOICES).get(subsystem_type)}:")
            for product in products:
                features_count = product.features.filter(is_active=True).count()
                print(f"  - {product.name}: {features_count} 个功能")
                total_products += 1
                total_features += features_count

    print(f"\n总计: {total_products} 个产品, {total_features} 个功能")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='测试子系统产品导入')
    parser.add_argument(
        '--action',
        choices=['import', 'clear', 'show'],
        default='show',
        help='操作类型: import(导入), clear(清除), show(显示)'
    )

    args = parser.parse_args()

    if args.action == 'import':
        test_import_subsystems()
        show_subsystem_products()
    elif args.action == 'clear':
        test_clear_subsystems()
        show_subsystem_products()
    else:
        show_subsystem_products()
