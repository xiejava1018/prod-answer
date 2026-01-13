#!/usr/bin/env python
"""
批量重新生成所有功能的向量，使用新的策略（强调功能描述）

Usage:
    python regenerate_embeddings.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.testing')
django.setup()

from apps.products.models import Feature, FeatureEmbedding
from apps.embeddings.services import EmbeddingServiceFactory


def regenerate_all_embeddings():
    """重新生成所有功能的向量"""
    print("开始重新生成功能向量...")
    print("=" * 60)

    # 获取所有活跃的功能
    features = Feature.objects.filter(is_active=True)
    total = features.count()

    print(f"找到 {total} 个活跃功能")

    # 获取默认的向量生成服务
    provider = EmbeddingServiceFactory.get_default_provider()
    print(f"使用模型: {provider.model_name}")
    print(f"向量维度: {provider.dimension}")
    print()

    success_count = 0
    failed_count = 0
    skipped_count = 0

    for idx, feature in enumerate(features, 1):
        try:
            # 检查是否已存在向量
            existing = FeatureEmbedding.objects.filter(
                feature=feature,
                model_name=provider.model_name
            ).first()

            # 使用新的策略生成向量（强调功能描述）
            text = f"{feature.feature_name}。功能描述：{feature.description}。详细说明：{feature.description}"
            embedding = provider.encode_single(text)

            # 保存或更新向量
            if existing:
                existing.embedding = embedding
                existing.model_version = provider.model_params.get('model', 'unknown')
                existing.save()
                status = "更新"
            else:
                FeatureEmbedding.objects.create(
                    feature=feature,
                    embedding=embedding,
                    model_name=provider.model_name,
                    model_version=provider.model_params.get('model', 'unknown')
                )
                status = "新建"

            success_count += 1
            print(f"[{idx}/{total}] {status}: {feature.feature_name} (维度: {len(embedding)})")

        except Exception as e:
            failed_count += 1
            print(f"[{idx}/{total}] 失败: {feature.feature_name} - {str(e)}")

    print()
    print("=" * 60)
    print("重新生成完成！")
    print(f"总计: {total}")
    print(f"成功: {success_count}")
    print(f"失败: {failed_count}")


if __name__ == '__main__':
    regenerate_all_embeddings()
