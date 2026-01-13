#!/usr/bin/env python
"""
Test script for embedding API configuration.
Usage:
    export SILICONFLOW_API_KEY="your-api-key"
    python test_embedding.py siliconflow
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.testing')
os.environ.setdefault('USE_SQLITE', 'True')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.embeddings.services import EmbeddingServiceFactory
from apps.embeddings.models import EmbeddingModelConfig


def test_siliconflow():
    """Test SiliconFlow API"""
    print("\n" + "="*60)
    print("测试硅基流动 API (SiliconFlow)")
    print("="*60)

    # Get or create config
    config = EmbeddingModelConfig.objects.get(model_name='siliconflow-bge-large-zh')

    # Set API key from environment
    api_key = os.environ.get('SILICONFLOW_API_KEY')
    if not api_key:
        print("\n❌ 错误: 请设置 SILICONFLOW_API_KEY 环境变量")
        print("   示例: export SILICONFLOW_API_KEY='sk-xxx'")
        return False

    config.set_api_key(api_key)
    config.save()

    # Test connection
    print("\n1. 测试连接...")
    try:
        provider = EmbeddingServiceFactory.create_provider(config)
        is_connected = provider.test_connection()
        if is_connected:
            print("   ✓ 连接成功")
        else:
            print("   ❌ 连接失败")
            return False
    except Exception as e:
        print(f"   ❌ 连接失败: {str(e)}")
        return False

    # Test encoding
    print("\n2. 测试文本编码...")
    try:
        test_texts = [
            "产品能力匹配系统",
            "智能推荐算法",
            "用户行为分析"
        ]
        embeddings = provider.encode(test_texts)
        print(f"   ✓ 成功编码 {len(test_texts)} 个文本")
        print(f"   ✓ 嵌入维度: {len(embeddings[0])}")
        print(f"   ✓ 示例向量前5个值: {embeddings[0][:5]}")
    except Exception as e:
        print(f"   ❌ 编码失败: {str(e)}")
        return False

    # Test similarity
    print("\n3. 测试相似度计算...")
    try:
        import numpy as np
        text1_emb = embeddings[0]
        text2_emb = embeddings[1]

        # Calculate cosine similarity
        similarity = np.dot(text1_emb, text2_emb) / (
            np.linalg.norm(text1_emb) * np.linalg.norm(text2_emb)
        )
        print(f"   ✓ 相似度计算成功")
        print(f"   ✓ '产品能力匹配系统' 与 '智能推荐算法' 的相似度: {similarity:.4f}")
    except Exception as e:
        print(f"   ❌ 相似度计算失败: {str(e)}")
        return False

    print("\n" + "="*60)
    print("✓ 所有测试通过！硅基流动API配置正确")
    print("="*60)
    return True


def test_zhipuai():
    """Test ZhipuAI API"""
    print("\n" + "="*60)
    print("测试智谱AI API (ZhipuAI)")
    print("="*60)

    config = EmbeddingModelConfig.objects.get(model_name='zhipuai-embedding-2')

    api_key = os.environ.get('ZHIPUAI_API_KEY')
    if not api_key:
        print("\n❌ 错误: 请设置 ZHIPUAI_API_KEY 环境变量")
        print("   示例: export ZHIPUAI_API_KEY='your-key'")
        return False

    config.set_api_key(api_key)
    config.save()

    print("\n1. 测试连接...")
    try:
        provider = EmbeddingServiceFactory.create_provider(config)
        is_connected = provider.test_connection()
        if is_connected:
            print("   ✓ 连接成功")
        else:
            print("   ❌ 连接失败")
            return False
    except Exception as e:
        print(f"   ❌ 连接失败: {str(e)}")
        return False

    print("\n2. 测试文本编码...")
    try:
        embeddings = provider.encode(["测试文本"])
        print(f"   ✓ 成功编码，维度: {len(embeddings[0])}")
    except Exception as e:
        print(f"   ❌ 编码失败: {str(e)}")
        return False

    print("\n✓ 智谱AI API测试通过！")
    return True


if __name__ == '__main__':
    provider = sys.argv[1] if len(sys.argv) > 1 else 'siliconflow'

    if provider == 'siliconflow':
        test_siliconflow()
    elif provider == 'zhipuai':
        test_zhipuai()
    else:
        print(f"\n未知的provider: {provider}")
        print("用法: python test_embedding.py [siliconflow|zhipuai]")
