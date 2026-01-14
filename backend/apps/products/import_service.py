"""
Product import service for importing products from JSON files.
"""
import json
from django.db import transaction
from .models import Product, Feature


class ProductImportService:
    """Service for importing products from structured JSON data."""

    # 子系统映射
    SUBSYSTEM_MAPPING = {
        '资产测绘与攻击面管理子系统': 'asset_mapping',
        '互联网暴露面测绘运营子系统': 'exposure_mapping',
        '安全大数据平台子系统': 'big_data',
        '安全管理和自动化编排子系统': 'soar',
    }

    @staticmethod
    def import_from_json(json_file_path: str, vendor: str = "默认厂商") -> dict:
        """
        Import products from JSON file.

        Args:
            json_file_path: Path to JSON file containing product data
            vendor: Vendor name for the products

        Returns:
            Dictionary with import results
        """
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        results = {
            'success': True,
            'products_created': 0,
            'features_created': 0,
            'errors': []
        }

        try:
            with transaction.atomic():
                for subsystem_name, items in data.items():
                    # 获取子系统类型
                    subsystem_type = ProductImportService.SUBSYSTEM_MAPPING.get(
                        subsystem_name,
                        'other'
                    )

                    # 创建或获取产品
                    product, created = Product.objects.get_or_create(
                        name=subsystem_name,
                        subsystem_type=subsystem_type,
                        defaults={
                            'vendor': vendor,
                            'description': f'{subsystem_name}技术参数',
                            'version': '1.0',
                            'is_active': True,
                            'spec_metadata': {'source': '产品集技术参数V3.xlsx'}
                        }
                    )

                    if created:
                        results['products_created'] += 1

                    # 处理功能特性
                    current_level1 = None
                    current_level2 = None
                    current_indicator_type = None

                    for item in items:
                        # 跳过空行
                        if not item.get('序号'):
                            continue

                        # 提取层级信息
                        level1 = item.get('一级功能') or current_level1
                        level2 = item.get('二级功能') or current_level2
                        indicator = item.get('指标项') or current_indicator_type
                        requirement = item.get('技术要求', '')

                        # 更新当前层级状态
                        if item.get('一级功能'):
                            current_level1 = item.get('一级功能')
                        if item.get('二级功能'):
                            current_level2 = item.get('二级功能')
                        if item.get('指标项'):
                            current_indicator_type = item.get('指标项')

                        # 映射指标项类型
                        indicator_type_map = {
                            '产品功能': 'product_function',
                            '性能指标': 'performance',
                            '安全要求': 'security',
                            '可靠性': 'reliability',
                            '兼容性': 'compatibility',
                            '易用性': 'usability',
                        }
                        indicator_type = indicator_type_map.get(
                            current_indicator_type,
                            'other'
                        ) if current_indicator_type else 'product_function'

                        # 创建功能特性
                        if requirement:
                            # 生成功能名称
                            if level2:
                                feature_name = level2
                            elif level1:
                                feature_name = level1
                            else:
                                feature_name = f"功能特性{item.get('序号', '')}"

                            feature, created = Feature.objects.get_or_create(
                                product=product,
                                feature_name=feature_name,
                                defaults={
                                    'description': requirement,
                                    'category': level1 or '其他',
                                    'subcategory': level2 or '',
                                    'level1_function': level1 or '',
                                    'level2_function': level2 or '',
                                    'indicator_type': indicator_type,
                                    'importance_level': 5,
                                    'is_active': True,
                                }
                            )

                            if created:
                                results['features_created'] += 1

        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))

        return results

    @staticmethod
    def clear_subsystem_products() -> dict:
        """
        Clear all subsystem products (for testing/reset).

        Returns:
            Dictionary with deletion results
        """
        results = {
            'success': True,
            'products_deleted': 0,
            'features_deleted': 0,
            'errors': []
        }

        try:
            with transaction.atomic():
                subsystem_types = [
                    'asset_mapping',
                    'exposure_mapping',
                    'big_data',
                    'soar'
                ]

                for subsystem_type in subsystem_types:
                    products = Product.objects.filter(
                        subsystem_type=subsystem_type
                    )

                    for product in products:
                        # 删除所有功能
                        features_count = product.features.count()
                        product.features.all().delete()
                        results['features_deleted'] += features_count

                        # 删除产品
                        product.delete()
                        results['products_deleted'] += 1

        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))

        return results
