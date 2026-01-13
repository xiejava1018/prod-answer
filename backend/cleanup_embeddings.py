#!/usr/bin/env python
"""
清理已删除功能和产品的向量数据

Usage:
    python cleanup_embeddings.py [--dry-run]
"""
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.testing')
django.setup()

from apps.products.models import Feature, Product, FeatureEmbedding


def cleanup_embeddings(dry_run=True):
    """
    清理已删除功能和产品的向量数据

    Args:
        dry_run: 如果为 True，只显示将要删除的数据，不实际删除
    """
    print("=" * 80)
    print("清理向量数据")
    print("=" * 80)
    print(f"模式: {'预览（不删除）' if dry_run else '执行删除'}")
    print()

    # 统计信息
    total_embeddings = FeatureEmbedding.objects.count()
    active_embeddings = FeatureEmbedding.objects.filter(
        feature__is_active=True,
        feature__product__is_active=True
    ).count()

    # 找出需要删除的向量
    inactive_feature_embeddings = FeatureEmbedding.objects.filter(
        feature__is_active=False
    )

    inactive_product_embeddings = FeatureEmbedding.objects.filter(
        feature__is_active=True,
        feature__product__is_active=False
    )

    total_to_delete = inactive_feature_embeddings.count() + inactive_product_embeddings.count()

    print("当前状态:")
    print(f"  总向量数: {total_embeddings}")
    print(f"  活跃向量数: {active_embeddings}")
    print(f"  需要删除的向量数: {total_to_delete}")
    print()

    if total_to_delete == 0:
        print("✓ 没有需要清理的向量数据")
        return

    # 显示详细信息
    print("需要删除的向量:")
    print("-" * 80)

    # 已删除的功能的向量
    if inactive_feature_embeddings.count() > 0:
        print(f"\n1. 已删除功能的向量 ({inactive_feature_embeddings.count()} 个):")
        for emb in inactive_feature_embeddings:
            print(f"   - {emb.feature.feature_name} (产品: {emb.feature.product.name})")

    # 已删除产品的功能向量
    if inactive_product_embeddings.count() > 0:
        print(f"\n2. 已删除产品的功能向量 ({inactive_product_embeddings.count()} 个):")
        for emb in inactive_product_embeddings:
            print(f"   - {emb.feature.feature_name} (产品: {emb.feature.product.name})")

    print()
    print("-" * 80)

    if dry_run:
        print("以上是预览结果。使用 --execute 参数实际删除这些向量。")
        return

    # 执行删除
    try:
        print("\n开始删除...")
        deleted_count = 0

        # 删除已删除功能的向量
        for emb in inactive_feature_embeddings:
            print(f"  删除: {emb.feature.feature_name} (产品: {emb.feature.product.name})")
            emb.delete()
            deleted_count += 1

        # 删除已删除产品的功能向量
        for emb in inactive_product_embeddings:
            print(f"  删除: {emb.feature.feature_name} (产品: {emb.feature.product.name})")
            emb.delete()
            deleted_count += 1

        print()
        print("=" * 80)
        print(f"✓ 清理完成！共删除 {deleted_count} 个向量")
        print(f"  剩余向量数: {FeatureEmbedding.objects.count()}")
        print("=" * 80)

    except Exception as e:
        print(f"\n错误: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    # 检查命令行参数
    dry_run = '--execute' not in sys.argv

    if dry_run:
        print("提示: 使用 --execute 参数来实际删除向量数据")
        print()

    cleanup_embeddings(dry_run=dry_run)
